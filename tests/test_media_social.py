from __future__ import annotations

from decimal import Decimal

import pytest

from report_engine.sections.media_social import MediaSocialRow, MediaSocialSnapshot


def row(
    source_type: str,
    articles: int,
    positive: int,
    neutral: int,
    negative: int,
    platforms: int,
) -> MediaSocialRow:
    return MediaSocialRow(
        source_type=source_type,
        article_count=articles,
        positive_articles=positive,
        neutral_articles=neutral,
        negative_articles=negative,
        platform_count=platforms,
    )


def fixture_snapshot() -> MediaSocialSnapshot:
    return MediaSocialSnapshot(
        rows=(row("media", 3, 1, 1, 1, 1), row("social", 9, 1, 2, 6, 3)),
        query_id="media-social.v1",
    )


def test_media_social_facts_keep_volume_and_composition_denominators_separate() -> None:
    snapshot = fixture_snapshot()
    facts = snapshot.to_fact_set()

    assert facts.get("articles").raw_value == 12
    assert facts.get("mediaArticleShare").formatted_value == "25.0%"
    assert facts.get("socialArticleShare").formatted_value == "75.0%"
    assert facts.get("mediaNegativeShare").formatted_value == "33.3%"
    assert facts.get("socialNegativeShare").formatted_value == "66.7%"
    assert facts.get("mediaNegativePopulationShare").formatted_value == "14.3%"
    assert facts.get("socialNegativePopulationShare").formatted_value == "85.7%"
    assert facts.get("socialMinusMediaNegativeShare").raw_value.quantize(
        Decimal("0.0001")
    ) == Decimal("0.3333")
    assert (
        facts.get("socialMinusMediaNegativeShare").formatted_value
        == "+33.3 个百分点"
    )
    assert facts.get("volumeLeaders").formatted_value == "社交内容"
    assert facts.get("negativeShareLeaders").formatted_value == "社交内容"
    assert facts.get("sourceClassification").raw_value == "source_type"


def test_absent_group_is_not_presented_as_zero_percent_sentiment() -> None:
    snapshot = MediaSocialSnapshot(
        rows=(row("media", 0, 0, 0, 0, 0), row("social", 2, 1, 0, 1, 1)),
        query_id="media-social.v1",
    )
    facts = snapshot.to_fact_set()

    assert snapshot.comparison_status == "insufficient_group_coverage"
    assert snapshot.social_minus_media_negative_share is None
    assert facts.get("mediaArticleShare").formatted_value == "0.0%"
    assert "mediaNegativeShare" not in facts.prompt_values()
    assert "socialMinusMediaNegativeShare" not in facts.prompt_values()
    assert "negativeShareLeaders" not in facts.prompt_values()


def test_populated_zero_negative_groups_form_a_valid_tie() -> None:
    snapshot = MediaSocialSnapshot(
        rows=(row("media", 2, 1, 1, 0, 1), row("social", 3, 2, 1, 0, 2)),
        query_id="media-social.v1",
    )
    facts = snapshot.to_fact_set()

    assert snapshot.comparison_status == "comparable"
    assert (
        facts.get("socialMinusMediaNegativeShare").formatted_value
        == "+0.0 个百分点"
    )
    assert facts.get("negativeShareLeaders").formatted_value == "媒体内容、社交内容"
    assert facts.get("negativeShareLeaderCount").raw_value == 2
    assert facts.get("mediaNegativePopulationShare").formatted_value == "0.0%"


def test_empty_snapshot_is_valid_no_data_but_has_no_facts() -> None:
    snapshot = MediaSocialSnapshot(
        rows=(row("media", 0, 0, 0, 0, 0), row("social", 0, 0, 0, 0, 0)),
        query_id="media-social.v1",
    )

    assert snapshot.has_data is False
    assert snapshot.comparison_status == "no_data"
    with pytest.raises(ValueError, match="empty snapshot"):
        snapshot.to_fact_set()


def test_snapshot_and_rows_reject_invalid_shapes_or_totals() -> None:
    with pytest.raises(ValueError, match="media then social"):
        MediaSocialSnapshot(
            rows=(row("social", 1, 1, 0, 0, 1), row("media", 1, 1, 0, 0, 1)),
            query_id="media-social.v1",
        )
    with pytest.raises(ValueError, match="sentiment counts"):
        row("media", 2, 1, 0, 0, 1)
    with pytest.raises(ValueError, match="cannot contain platforms"):
        row("media", 0, 0, 0, 0, 1)
    with pytest.raises(ValueError, match="must contain a platform"):
        row("social", 1, 1, 0, 0, 0)
