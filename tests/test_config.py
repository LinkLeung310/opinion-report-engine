from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError

from report_engine.config import Language, ReportConfig, ReportType


def sample_config() -> dict:
    return {
        "reportType": "csuite",
        "language": "zh",
        "topic": {
            "tag": "layoff",
            "displayName": "裁员",
            "eventTitle": '××“裁员60%”事件',
        },
        "dateRange": {"from": "2026-03-17", "to": "2026-03-23"},
        "sections": [
            {"id": "verdict", "enabled": True},
            {
                "id": "response",
                "enabled": False,
                "input": {"responseDate": None},
            },
            {
                "id": "benchmark",
                "enabled": False,
                "input": {"comparisonTag": None},
            },
        ],
    }


def test_parses_the_fixed_input_contract() -> None:
    config = ReportConfig.model_validate(sample_config())

    assert config.report_type is ReportType.CSUITE
    assert config.language is Language.ZH
    assert config.topic.tag == "layoff"
    assert config.topic.display_name == "裁员"
    assert config.date_range.from_date.isoformat() == "2026-03-17"


def test_unknown_report_type_falls_back_to_csuite() -> None:
    raw = sample_config()
    raw["reportType"] = "unknown-audience"

    config = ReportConfig.model_validate(raw)

    assert config.report_type is ReportType.CSUITE


def test_section_array_order_is_preserved() -> None:
    config = ReportConfig.model_validate(sample_config())

    assert [section.id for section in config.sections] == [
        "verdict",
        "response",
        "benchmark",
    ]


def test_section_specific_input_shape_is_preserved_for_the_registry() -> None:
    config = ReportConfig.model_validate(sample_config())

    assert config.sections[1].input == {"responseDate": None}
    assert config.sections[2].input == {"comparisonTag": None}


def test_rejects_an_inverted_date_range() -> None:
    raw = sample_config()
    raw["dateRange"] = {"from": "2026-03-24", "to": "2026-03-23"}

    with pytest.raises(ValidationError, match="dateRange.from"):
        ReportConfig.model_validate(raw)


def test_rejects_an_unknown_language() -> None:
    raw = sample_config()
    raw["language"] = "fr"

    with pytest.raises(ValidationError):
        ReportConfig.model_validate(raw)


def test_rejects_extra_public_contract_fields() -> None:
    raw = deepcopy(sample_config())
    raw["topic"]["unexpected"] = "contract drift"

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ReportConfig.model_validate(raw)


def test_rejects_an_unknown_section_id() -> None:
    raw = sample_config()
    raw["sections"][0]["id"] = "invented-section"

    with pytest.raises(ValidationError):
        ReportConfig.model_validate(raw)


def test_rejects_duplicate_section_ids() -> None:
    raw = sample_config()
    raw["sections"][1]["id"] = "verdict"

    with pytest.raises(ValidationError, match="duplicate IDs"):
        ReportConfig.model_validate(raw)


def test_requires_at_least_one_enabled_section() -> None:
    raw = sample_config()
    for section in raw["sections"]:
        section["enabled"] = False

    with pytest.raises(ValidationError, match="at least one section"):
        ReportConfig.model_validate(raw)
