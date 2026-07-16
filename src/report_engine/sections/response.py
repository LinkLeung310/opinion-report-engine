"""Balanced, date-only response-window facts without causal attribution."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from report_engine.domain.facts import Fact, FactSet


RESPONSE_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
SENTIMENTS = ("positive", "neutral", "negative")
MAX_WINDOW_DAYS = 7


class ResponseInputError(ValueError):
    """A safe, actionable error for invalid response-section input."""


def parse_response_date(value: object) -> date:
    if not isinstance(value, str) or RESPONSE_DATE_PATTERN.fullmatch(value) is None:
        raise ResponseInputError("responseDate must use YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ResponseInputError("responseDate must be a valid calendar date") from error


@dataclass(frozen=True)
class ResponseWindow:
    report_from: date
    report_to: date
    response_date: date
    window_days: int
    pre_start: date
    pre_end: date
    post_start: date
    post_end: date

    @classmethod
    def build(
        cls,
        report_from: date,
        report_to: date,
        response_date: date,
    ) -> ResponseWindow:
        if report_from > report_to:
            raise ValueError("Report date range must be chronological")
        if not report_from < response_date < report_to:
            raise ResponseInputError(
                "responseDate must be strictly inside dateRange with a complete day "
                "available before and after it"
            )

        before_days = (response_date - report_from).days
        after_days = (report_to - response_date).days
        window_days = min(MAX_WINDOW_DAYS, before_days, after_days)
        return cls(
            report_from=report_from,
            report_to=report_to,
            response_date=response_date,
            window_days=window_days,
            pre_start=response_date - timedelta(days=window_days),
            pre_end=response_date - timedelta(days=1),
            post_start=response_date + timedelta(days=1),
            post_end=response_date + timedelta(days=window_days),
        )


@dataclass(frozen=True)
class ResponseObservation:
    day: date
    sentiment: str
    response_tagged: bool

    def __post_init__(self) -> None:
        if self.sentiment not in SENTIMENTS:
            raise ValueError("Unsupported response observation sentiment")
        if type(self.response_tagged) is not bool:
            raise ValueError("Response tag signal must be boolean")


@dataclass(frozen=True)
class ResponseWindowStats:
    label: str
    start_day: date
    end_day: date
    article_count: int
    positive_articles: int
    neutral_articles: int
    negative_articles: int

    def __post_init__(self) -> None:
        counts = (
            self.article_count,
            self.positive_articles,
            self.neutral_articles,
            self.negative_articles,
        )
        if self.start_day > self.end_day or min(counts) < 0:
            raise ValueError("Response window statistics must be valid")
        if sum(counts[1:]) != self.article_count:
            raise ValueError("Response window total must equal sentiment counts")

    @property
    def calendar_days(self) -> int:
        return (self.end_day - self.start_day).days + 1

    @property
    def date_range_label(self) -> str:
        start = f"{self.start_day.month}/{self.start_day.day}"
        end = f"{self.end_day.month}/{self.end_day.day}"
        return start if self.start_day == self.end_day else f"{start}-{end}"

    @property
    def daily_average(self) -> Decimal:
        return Decimal(self.article_count) / Decimal(self.calendar_days)

    def share(self, sentiment: str) -> Decimal | None:
        counts = {
            "positive": self.positive_articles,
            "neutral": self.neutral_articles,
            "negative": self.negative_articles,
        }
        if sentiment not in counts:
            raise ValueError("Unsupported response-window sentiment")
        if self.article_count == 0:
            return None
        return Decimal(counts[sentiment]) / Decimal(self.article_count)


@dataclass(frozen=True)
class ResponseSnapshot:
    window: ResponseWindow
    observations: tuple[ResponseObservation, ...]
    query_id: str

    def __post_init__(self) -> None:
        if not self.query_id.strip():
            raise ValueError("Response query ID cannot be blank")
        if any(
            observation.day < self.window.report_from
            or observation.day > self.window.report_to
            for observation in self.observations
        ):
            raise ValueError("Response observation falls outside the report scope")

    @property
    def article_count(self) -> int:
        return len(self.observations)

    @property
    def has_scoped_data(self) -> bool:
        return self.article_count > 0

    def _window_stats(
        self,
        label: str,
        start_day: date,
        end_day: date,
    ) -> ResponseWindowStats:
        observations = tuple(
            observation
            for observation in self.observations
            if start_day <= observation.day <= end_day
        )
        return ResponseWindowStats(
            label=label,
            start_day=start_day,
            end_day=end_day,
            article_count=len(observations),
            positive_articles=sum(
                observation.sentiment == "positive" for observation in observations
            ),
            neutral_articles=sum(
                observation.sentiment == "neutral" for observation in observations
            ),
            negative_articles=sum(
                observation.sentiment == "negative" for observation in observations
            ),
        )

    @property
    def pre(self) -> ResponseWindowStats:
        return self._window_stats(
            "pre",
            self.window.pre_start,
            self.window.pre_end,
        )

    @property
    def post(self) -> ResponseWindowStats:
        return self._window_stats(
            "post",
            self.window.post_start,
            self.window.post_end,
        )

    @property
    def comparison_articles(self) -> int:
        return self.pre.article_count + self.post.article_count

    @property
    def has_comparison_data(self) -> bool:
        return self.comparison_articles > 0

    @property
    def response_day_articles(self) -> int:
        return sum(
            observation.day == self.window.response_date
            for observation in self.observations
        )

    @property
    def response_day_official_tagged_articles(self) -> int:
        return sum(
            observation.day == self.window.response_date
            and observation.response_tagged
            for observation in self.observations
        )

    @property
    def outside_matched_windows_articles(self) -> int:
        return (
            self.article_count
            - self.comparison_articles
            - self.response_day_articles
        )

    @property
    def article_delta(self) -> int:
        return self.post.article_count - self.pre.article_count

    @property
    def daily_average_delta(self) -> Decimal:
        return self.post.daily_average - self.pre.daily_average

    @property
    def article_percent_change(self) -> Decimal | None:
        if self.pre.article_count == 0:
            return None
        return Decimal(self.article_delta) / Decimal(self.pre.article_count)

    def share_delta(self, sentiment: str) -> Decimal | None:
        pre_share = self.pre.share(sentiment)
        post_share = self.post.share(sentiment)
        if pre_share is None or post_share is None:
            return None
        return post_share - pre_share

    def to_fact_set(self) -> FactSet:
        window_source = "response.windows.v1"
        share_source = "response.shares.v1"
        comparison_source = "response.comparison.v1"
        pre = self.pre
        post = self.post
        facts = [
            Fact("articles", self.article_count, f"{self.article_count:,}", self.query_id),
            Fact(
                "responseDate",
                self.window.response_date,
                self.window.response_date.isoformat(),
                window_source,
            ),
            Fact(
                "windowDays",
                self.window.window_days,
                f"{self.window.window_days:,}",
                window_source,
            ),
            Fact(
                "preDateRange",
                f"{pre.start_day.isoformat()}/{pre.end_day.isoformat()}",
                pre.date_range_label,
                window_source,
            ),
            Fact(
                "postDateRange",
                f"{post.start_day.isoformat()}/{post.end_day.isoformat()}",
                post.date_range_label,
                window_source,
            ),
            Fact(
                "comparisonArticles",
                self.comparison_articles,
                f"{self.comparison_articles:,}",
                comparison_source,
            ),
            Fact(
                "responseDayArticles",
                self.response_day_articles,
                f"{self.response_day_articles:,}",
                self.query_id,
            ),
            Fact(
                "responseDayOfficialTaggedArticles",
                self.response_day_official_tagged_articles,
                f"{self.response_day_official_tagged_articles:,}",
                self.query_id,
            ),
            Fact(
                "outsideMatchedWindowsArticles",
                self.outside_matched_windows_articles,
                f"{self.outside_matched_windows_articles:,}",
                comparison_source,
            ),
        ]
        for prefix, side in (("pre", pre), ("post", post)):
            facts.extend(
                (
                    Fact(
                        f"{prefix}Articles",
                        side.article_count,
                        f"{side.article_count:,}",
                        self.query_id,
                    ),
                    Fact(
                        f"{prefix}DailyAverage",
                        side.daily_average,
                        f"{side.daily_average:.1f}",
                        comparison_source,
                    ),
                )
            )
            for sentiment in SENTIMENTS:
                count = getattr(side, f"{sentiment}_articles")
                share = side.share(sentiment)
                facts.extend(
                    (
                        Fact(
                            f"{prefix}{sentiment.title()}Articles",
                            count,
                            f"{count:,}",
                            self.query_id,
                        ),
                        Fact(
                            f"{prefix}{sentiment.title()}Share",
                            share,
                            f"{share:.1%}" if share is not None else "不可用",
                            share_source,
                        ),
                    )
                )

        percent_change = self.article_percent_change
        facts.extend(
            (
                Fact(
                    "articleDelta",
                    self.article_delta,
                    f"{self.article_delta:+,}",
                    comparison_source,
                ),
                Fact(
                    "dailyAverageDelta",
                    self.daily_average_delta,
                    f"{self.daily_average_delta:+.1f}",
                    comparison_source,
                ),
                Fact(
                    "articlePercentChange",
                    percent_change,
                    f"{percent_change:+.1%}"
                    if percent_change is not None
                    else "不可用",
                    comparison_source,
                ),
            )
        )
        for sentiment in SENTIMENTS:
            delta = self.share_delta(sentiment)
            facts.append(
                Fact(
                    f"{sentiment}ShareDelta",
                    delta,
                    f"{delta * 100:+.1f} 个百分点"
                    if delta is not None
                    else "不可用",
                    comparison_source,
                )
            )
        return FactSet(facts=tuple(facts))
