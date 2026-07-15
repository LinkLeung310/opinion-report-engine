from __future__ import annotations

from report_engine.sections.platforms import PlatformRow, PlatformsSnapshot


def row(
    platform: str,
    articles: int,
    positive: int,
    neutral: int,
    negative: int,
    engagement: int,
) -> PlatformRow:
    return PlatformRow(
        platform=platform,
        article_count=articles,
        positive_articles=positive,
        neutral_articles=neutral,
        negative_articles=negative,
        likes=engagement,
        comments=0,
        shares=0,
        favorites=0,
    )


def fixture_snapshot() -> PlatformsSnapshot:
    return PlatformsSnapshot(
        rows=(
            row("微博", 4, 0, 1, 3, 15_715),
            row("B站", 4, 1, 1, 2, 6_610),
            row("新闻", 3, 1, 1, 1, 2_425),
            row("知乎", 1, 0, 0, 1, 1_420),
        ),
        query_id="platforms.v1",
    )


def test_platform_facts_disclose_ties_and_concentration_without_rate_distortion() -> None:
    snapshot = fixture_snapshot()
    facts = snapshot.to_fact_set()

    assert facts.get("articles").raw_value == 12
    assert facts.get("volumeLeaders").formatted_value == "微博、B站"
    assert facts.get("volumeLeaderCount").raw_value == 2
    assert facts.get("leadingArticleShare").formatted_value == "33.3%"
    assert facts.get("negativeLeader").formatted_value == "微博"
    assert facts.get("negativeLeaderShare").formatted_value == "42.9%"
    assert facts.get("negativeLeaderRatio").formatted_value == "75.0%"
    assert facts.get("engagementLeader").formatted_value == "微博"
    assert facts.get("engagementLeaderShare").formatted_value == "60.0%"
    assert facts.get("engagementLeaderPerArticle").formatted_value == "3,928.8"


def test_platform_chart_rows_group_the_tail_without_losing_totals() -> None:
    rows = tuple(
        row(f"平台{index}", 10 - index, 10 - index, 0, 0, 100 - index)
        for index in range(9)
    )
    snapshot = PlatformsSnapshot(rows=rows, query_id="platforms.v1")

    assert len(snapshot.display_rows) == 8
    assert snapshot.display_rows[-1].platform == "其他"
    assert sum(item.article_count for item in snapshot.display_rows) == snapshot.article_count
    assert (
        sum(item.total_engagement for item in snapshot.display_rows)
        == snapshot.total_engagement
    )


def test_platform_facts_omit_a_negative_winner_when_the_scope_has_no_negatives() -> None:
    snapshot = PlatformsSnapshot(
        rows=(row("B站", 2, 1, 1, 0, 20),),
        query_id="platforms.v1",
    )
    facts = snapshot.to_fact_set()

    assert snapshot.negative_leader is None
    assert "negativeLeader" not in facts.prompt_values()
