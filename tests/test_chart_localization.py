from __future__ import annotations

from datetime import date
import re
from unittest.mock import patch

from matplotlib.figure import Figure
from matplotlib.text import Text

from report_engine.charts.benchmark import BenchmarkChartBuilder
from report_engine.charts.engagement import EngagementChartBuilder
from report_engine.charts.keywords import KeywordsChartBuilder
from report_engine.charts.media_social import MediaSocialChartBuilder
from report_engine.charts.metrics import MetricsChartBuilder
from report_engine.charts.negative_themes import NegativeThemesChartBuilder
from report_engine.charts.platforms import PlatformsChartBuilder
from report_engine.charts.response import ResponseChartBuilder
from report_engine.charts.risk import RiskChartBuilder
from report_engine.charts.sentiment_evolution import SentimentEvolutionChartBuilder
from report_engine.charts.severity import SeverityChartBuilder
from report_engine.charts.spread_path import SpreadPathChartBuilder
from report_engine.charts.timeline import TimelineChartBuilder
from report_engine.charts.top_content import TopContentChartBuilder
from report_engine.charts.trend import TrendChartBuilder
from report_engine.config import Language
from report_engine.sections.metrics import MetricsSnapshot
from tests.test_benchmark import fixture_snapshot as benchmark_snapshot
from tests.test_engagement import fixture_snapshot as engagement_snapshot
from tests.test_keywords_chart import snapshot as keywords_snapshot
from tests.test_media_social import fixture_snapshot as media_social_snapshot
from tests.test_negative_themes import fixture_snapshot as negative_themes_snapshot
from tests.test_platforms import fixture_snapshot as platforms_snapshot
from tests.test_response import fixture_snapshot as response_snapshot
from tests.test_risk import fixture_snapshot as risk_snapshot
from tests.test_sentiment_evolution_chart import snapshot as evolution_snapshot
from tests.test_severity import fixture_snapshot as severity_snapshot
from tests.test_spread_path import fixture_snapshot as spread_path_snapshot
from tests.test_timeline import fixture_snapshot as timeline_snapshot
from tests.test_top_content import fixture_snapshot as top_content_snapshot
from tests.test_trend_chart import snapshot as trend_snapshot


HAN_TEXT = re.compile(r"[\u3400-\u9fff]")


def metrics_snapshot() -> MetricsSnapshot:
    return MetricsSnapshot(
        article_count=12,
        positive_articles=2,
        neutral_articles=3,
        negative_articles=7,
        platform_count=4,
        likes=15_460,
        comments=4_705,
        shares=4_620,
        favorites=1_385,
        peak_day=date(2026, 3, 20),
        peak_article_count=3,
        query_id="metrics.v1",
    )


def visible_text(builder, snapshot, output_directory) -> str:
    captured: list[str] = []
    original_savefig = Figure.savefig

    def capture(figure: Figure, *args, **kwargs):
        captured.extend(
            item.get_text()
            for item in figure.findobj(match=lambda artist: isinstance(artist, Text))
        )
        return original_savefig(figure, *args, **kwargs)

    with patch.object(Figure, "savefig", capture):
        builder.build(snapshot, output_directory, Language.EN)
    return "\n".join(captured)


def test_every_chart_localizes_engine_owned_visible_text_to_english(tmp_path) -> None:
    platforms = platforms_snapshot()
    keywords = keywords_snapshot()
    engagement = engagement_snapshot()
    top_content = top_content_snapshot()
    spread_path = spread_path_snapshot()
    cases = (
        (
            MetricsChartBuilder(),
            metrics_snapshot(),
            ("Negative content accounts for", "Articles", "Positive"),
            (),
        ),
        (
            TrendChartBuilder(),
            trend_snapshot(),
            ("Peak on", "Articles", "Neutral"),
            (),
        ),
        (
            PlatformsChartBuilder(),
            platforms,
            ("Volume and sentiment", "Engagement concentration", "Total engagement"),
            tuple(row.platform for row in platforms.display_rows),
        ),
        (
            SeverityChartBuilder(),
            severity_snapshot(),
            ("Severity classification", "Negative score", "High/critical negatives"),
            (),
        ),
        (
            RiskChartBuilder(),
            risk_snapshot(),
            ("Overall risk signal index", "Negative sentiment", "not probability"),
            (),
        ),
        (
            SentimentEvolutionChartBuilder(),
            evolution_snapshot(),
            ("Sentiment composition", "Early phase", "Negative"),
            (),
        ),
        (
            KeywordsChartBuilder(),
            keywords,
            ("Documents mentioning the phrase", "Positive", "Negative"),
            tuple(phrase.text for phrase in keywords.display_phrases),
        ),
        (
            EngagementChartBuilder(),
            engagement,
            ("Likes", "Engagement composition", "Highest-count records"),
            tuple(record.title for record in engagement.records),
        ),
        (
            MediaSocialChartBuilder(),
            media_social_snapshot(),
            ("Media", "Social", "Within-group sentiment"),
            (),
        ),
        (
            TimelineChartBuilder(),
            timeline_snapshot(),
            ("Observed time", "calendar days", "first observed"),
            (),
        ),
        (
            TopContentChartBuilder(),
            top_content,
            ("Stored engagement per record", "Structured risk signal", "Not applicable"),
            tuple(record.title for record in top_content.records),
        ),
        (
            NegativeThemesChartBuilder(),
            negative_themes_snapshot(),
            ("Matched negative records", "concerns", "counts are not additive"),
            (),
        ),
        (
            SpreadPathChartBuilder(),
            spread_path,
            ("First-observed order", "First-observed cell / wave", "not repost edges"),
            tuple(row.platform for row in spread_path.display_platforms),
        ),
        (
            ResponseChartBuilder(),
            response_snapshot(),
            ("Before response", "Observed volume", "do not establish causality"),
            (),
        ),
        (
            BenchmarkChartBuilder(),
            benchmark_snapshot(),
            ("Current event", "Historical benchmark", "Daily average articles"),
            (),
        ),
    )

    for index, (builder, snapshot, expected, preserved_source_text) in enumerate(cases):
        text = visible_text(builder, snapshot, tmp_path / str(index))
        for fragment in expected:
            assert fragment in text, f"{builder.__class__.__name__}: missing {fragment!r}"
        engine_text = text
        for source_text in preserved_source_text:
            engine_text = engine_text.replace(source_text, "")
        assert not HAN_TEXT.search(engine_text), (
            f"{builder.__class__.__name__} retained engine-owned Chinese text: "
            f"{engine_text!r}"
        )
