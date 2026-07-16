from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from report_engine.config import ReportConfig


WORKFLOW_PATH = (
    Path(__file__).parents[1] / "n8n" / "report-generation-orchestrator.json"
)


def load_workflow() -> dict:
    return json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))


def test_n8n_workflow_is_an_inactive_orchestration_layer() -> None:
    workflow = load_workflow()

    assert workflow["active"] is False
    assert workflow["settings"]["executionOrder"] == "v1"
    node_types = {node["type"] for node in workflow["nodes"]}
    assert "n8n-nodes-base.postgres" not in node_types
    assert "n8n-nodes-base.code" not in node_types
    assert not any("langchain" in node_type for node_type in node_types)


def test_every_node_uses_a_uuid_v4_and_contains_no_credentials() -> None:
    workflow = load_workflow()

    for node in workflow["nodes"]:
        parsed = UUID(node["id"])
        assert parsed.version == 4
        assert "credentials" not in node


def test_http_nodes_use_the_live_local_version_and_visible_error_outputs() -> None:
    workflow = load_workflow()
    http_nodes = [
        node for node in workflow["nodes"] if node["type"] == "n8n-nodes-base.httpRequest"
    ]

    assert {node["name"] for node in http_nodes} == {
        "Submit Report",
        "Get Report Status",
    }
    for node in http_nodes:
        assert node["typeVersion"] == 4.4
        assert node["retryOnFail"] is True
        assert node["maxTries"] == 3
        assert node["waitBetweenTries"] == 5000
        assert node["onError"] == "continueErrorOutput"
        error_outputs = workflow["connections"][node["name"]]["main"][1]
        assert error_outputs == [{"node": "API Error", "type": "main", "index": 0}]


def test_status_branches_complete_fail_or_poll_again() -> None:
    workflow = load_workflow()
    connections = workflow["connections"]

    assert connections["Report Complete?"]["main"][0][0]["node"] == "Report Ready"
    assert connections["Report Complete?"]["main"][1][0]["node"] == "Report Failed?"
    assert connections["Report Failed?"]["main"][0][0]["node"] == "Report Failed"
    assert connections["Report Failed?"]["main"][1][0]["node"] == "Wait Before Poll"


def test_failure_terminals_mark_the_execution_failed() -> None:
    workflow = load_workflow()
    nodes_by_name = {node["name"]: node for node in workflow["nodes"]}

    for node_name in ("Report Failed", "API Error"):
        node = nodes_by_name[node_name]
        assert node["type"] == "n8n-nodes-base.stopAndError"
        assert node["typeVersion"] == 1
        assert node["parameters"]["errorMessage"]


def test_submit_body_and_status_url_match_the_m3_contract() -> None:
    workflow = load_workflow()
    nodes_by_name = {node["name"]: node for node in workflow["nodes"]}

    submit = nodes_by_name["Submit Report"]
    report_config = json.loads(submit["parameters"]["jsonBody"])
    parsed_config = ReportConfig.model_validate(report_config)
    assert set(report_config) == {
        "reportType",
        "language",
        "topic",
        "dateRange",
        "sections",
    }
    assert tuple(
        section.id.value for section in parsed_config.sections if section.enabled
    ) == (
        "verdict",
        "metrics",
        "trend",
        "viewpoints",
        "platforms",
        "severity",
        "risk",
    )
    assert submit["parameters"]["url"].endswith("/reports")

    status = nodes_by_name["Get Report Status"]
    status_url = status["parameters"]["url"]
    assert "$('Submit Report').item.json.taskId" in status_url
    assert status_url.endswith("/status")
