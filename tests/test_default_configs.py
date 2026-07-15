from __future__ import annotations

import json
from pathlib import Path

import pytest

from report_engine.application.planner import ReportPlanner
from report_engine.config import Language, ReportConfig, ReportType, SectionId
from report_engine.sections.registry import default_registry


EXAMPLES = Path(__file__).parents[1] / "examples"
CSUITE_DEFAULT = (
    SectionId.VERDICT,
    SectionId.METRICS,
    SectionId.TREND,
    SectionId.VIEWPOINTS,
    SectionId.PLATFORMS,
    SectionId.SEVERITY,
    SectionId.RISK,
)
PR_DEFAULT = (
    *CSUITE_DEFAULT,
    SectionId.SENTIMENT_EVOLUTION,
    SectionId.KEYWORDS,
    SectionId.ENGAGEMENT,
    SectionId.MEDIA_SOCIAL,
)


@pytest.mark.parametrize(
    ("filename", "report_type", "enabled"),
    (
        ("report-config.csuite.json", ReportType.CSUITE, CSUITE_DEFAULT),
        ("report-config.pr.json", ReportType.PR, PR_DEFAULT),
    ),
)
def test_standard_default_configs_preserve_all_ids_and_expected_enabled_order(
    filename: str,
    report_type: ReportType,
    enabled: tuple[SectionId, ...],
) -> None:
    raw = json.loads((EXAMPLES / filename).read_text(encoding="utf-8"))
    config = ReportConfig.model_validate(raw)
    plan = ReportPlanner(default_registry()).build(config)

    assert config.report_type is report_type
    assert config.language is Language.ZH
    assert config.topic.tag == "bilibili-dislike"
    assert config.date_range.from_date.isoformat() == "2026-03-17"
    assert config.date_range.to_date.isoformat() == "2026-03-23"
    assert tuple(section.id for section in config.sections) == tuple(SectionId)
    assert tuple(section.id for section in plan.sections) == enabled
    assert all(section.can_execute for section in plan.sections)


def test_standard_defaults_preserve_disabled_section_input_shapes() -> None:
    raw = json.loads(
        (EXAMPLES / "report-config.pr.json").read_text(encoding="utf-8")
    )
    config = ReportConfig.model_validate(raw)
    inputs = {section.id: section.input for section in config.sections}

    assert inputs[SectionId.RESPONSE] == {"responseDate": None}
    assert inputs[SectionId.BENCHMARK] == {"comparisonTag": None}
    assert inputs[SectionId.BIZ_IMPACT] == {"notes": None}
