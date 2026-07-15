from __future__ import annotations

from report_engine.application.planner import ReportPlanner
from report_engine.config import ReportConfig
from report_engine.sections.registry import default_registry

from .test_config import sample_config


def build_plan(raw: dict):
    return ReportPlanner(default_registry()).build(ReportConfig.model_validate(raw))


def test_plan_contains_only_enabled_sections_in_user_order() -> None:
    raw = sample_config()
    raw["sections"] = [
        {"id": "trend", "enabled": True},
        {"id": "metrics", "enabled": False},
        {"id": "verdict", "enabled": True},
    ]

    plan = build_plan(raw)

    assert [section.id for section in plan.sections] == ["trend", "verdict"]


def test_scope_includes_the_complete_end_date() -> None:
    plan = build_plan(sample_config())

    assert plan.scope.from_date.isoformat() == "2026-03-17"
    assert plan.scope.to_date.isoformat() == "2026-03-23"
    assert plan.scope.from_inclusive.isoformat() == "2026-03-17T00:00:00+08:00"
    assert plan.scope.to_exclusive.isoformat() == "2026-03-24T00:00:00+08:00"
    assert plan.scope.timezone_name == "Asia/Shanghai"


def test_missing_special_input_fails_only_that_planned_section() -> None:
    raw = sample_config()
    raw["sections"] = [
        {"id": "response", "enabled": True, "input": {}},
        {"id": "verdict", "enabled": True},
    ]

    plan = build_plan(raw)

    assert plan.sections[0].can_execute is False
    assert plan.sections[0].input_errors == (
        "Missing required section input: responseDate",
    )
    assert plan.sections[1].can_execute is True


def test_all_project_defined_special_inputs_are_registered() -> None:
    raw = sample_config()
    raw["sections"] = [
        {"id": "response", "enabled": True, "input": {"responseDate": "2026-03-20"}},
        {"id": "benchmark", "enabled": True, "input": {"comparisonTag": "prior"}},
        {"id": "biz-impact", "enabled": True, "input": {"notes": "sales context"}},
    ]

    plan = build_plan(raw)

    assert all(section.can_execute for section in plan.sections)


def test_blank_special_input_is_treated_as_missing() -> None:
    raw = sample_config()
    raw["sections"] = [
        {"id": "benchmark", "enabled": True, "input": {"comparisonTag": "  "}},
    ]

    plan = build_plan(raw)

    assert plan.sections[0].can_execute is False


def test_report_type_fallback_is_visible_as_a_plan_warning() -> None:
    raw = sample_config()
    raw["reportType"] = "unknown-audience"

    plan = build_plan(raw)

    assert plan.scope.report_type == "csuite"
    assert plan.warnings == ("Unknown reportType was normalized to csuite",)
