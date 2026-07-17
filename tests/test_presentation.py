from decimal import Decimal

import pytest

from report_engine.config import Language, SectionId
from report_engine.domain.facts import Fact, FactSet
from report_engine.presentation import (
    failed_section_markdown,
    localize_fact_set,
    section_heading,
)


@pytest.mark.parametrize("section_id", tuple(SectionId))
def test_every_public_section_has_an_English_heading_and_failure_fragment(
    section_id: SectionId,
) -> None:
    heading = section_heading(section_id, Language.EN)
    markdown = failed_section_markdown(section_id, Language.EN)

    assert heading in markdown
    assert not any("\u4e00" <= character <= "\u9fff" for character in markdown)


@pytest.mark.parametrize(
    ("section_id", "key", "raw_value", "zh_value", "expected"),
    (
        (
            SectionId.SENTIMENT_EVOLUTION,
            "phase1Label",
            "前期",
            "前期",
            "Early phase",
        ),
        (
            SectionId.SENTIMENT_EVOLUTION,
            "negativeShareDelta",
            Decimal("0.5"),
            "+50.0 个百分点",
            "+50.0 percentage points",
        ),
        (
            SectionId.ENGAGEMENT,
            "record1Sentiment",
            "negative",
            "负面",
            "Negative",
        ),
        (
            SectionId.MEDIA_SOCIAL,
            "socialMinusMediaNegativeShare",
            Decimal("0.333"),
            "+33.3 个百分点",
            "+33.3 percentage points",
        ),
        (
            SectionId.TIMELINE,
            "milestone1Roles",
            "first_observed",
            "首次收录",
            "first observed",
        ),
        (
            SectionId.TOP_CONTENT,
            "record1Category",
            "dual_signal",
            "双信号代表",
            "dual-signal representative",
        ),
        (
            SectionId.NEGATIVE_THEMES,
            "theme1Label",
            "user_agency",
            "用户自主权",
            "User agency and control",
        ),
        (
            SectionId.BIZ_IMPACT,
            "causalClaimStatus",
            "not_established",
            "未建立因果关系",
            "No causal relationship established",
        ),
    ),
)
def test_fact_localization_changes_only_display_text(
    section_id: SectionId,
    key: str,
    raw_value,
    zh_value: str,
    expected: str,
) -> None:
    facts = FactSet(
        facts=(
            Fact(
                key=key,
                raw_value=raw_value,
                formatted_value=zh_value,
                source_id="fixture.v1",
                source_record_ids=("record-1",),
            ),
        )
    )

    localized = localize_fact_set(section_id, facts, Language.EN).get(key)

    assert localized.formatted_value == expected
    assert localized.raw_value == raw_value
    assert localized.source_id == "fixture.v1"
    assert localized.source_record_ids == ("record-1",)
    assert localize_fact_set(section_id, facts, Language.ZH) is facts
