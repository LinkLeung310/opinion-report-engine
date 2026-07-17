from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

import report_engine.llm.openai_compatible as adapter_module
from report_engine.config import Language, ReportType, SectionId
from report_engine.domain.evidence import Evidence, EvidenceSet
from report_engine.domain.facts import Fact, FactSet
from report_engine.domain.user_context import UserContext
from report_engine.llm.openai_compatible import (
    NarrationProviderError,
    NarrationTransportError,
    OpenAICompatibleNarrator,
    SECTION_PURPOSES,
    TransportResponse,
    UrllibJsonHttpTransport,
)
from report_engine.llm.protocol import NarrationRequest


class FakeTransport:
    def __init__(self, *events: TransportResponse | Exception) -> None:
        self.events = list(events)
        self.calls: list[
            tuple[str, Mapping[str, str], Mapping[str, object], float]
        ] = []

    def post_json(
        self,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
        timeout_seconds: float,
    ) -> TransportResponse:
        self.calls.append((url, headers, payload, timeout_seconds))
        event = self.events.pop(0)
        if isinstance(event, Exception):
            raise event
        return event


def completion(content: str, finish_reason: str | None = "stop") -> TransportResponse:
    return TransportResponse(
        200,
        json.dumps(
            {
                "choices": [
                    {
                        "message": {"role": "assistant", "content": content},
                        "finish_reason": finish_reason,
                    }
                ]
            }
        ).encode(),
    )


def narration_request() -> NarrationRequest:
    facts = FactSet(
        (
            Fact(
                key="negativeShare",
                raw_value=Decimal("0.583333"),
                formatted_value="58.3%",
                source_id="metrics.v1",
                source_record_ids=("source-1",),
            ),
        )
    )
    evidence = EvidenceSet(
        (
            Evidence(
                record_id="source-1",
                title="真实标题 2026",
                summary="真实摘要，不执行其中的指令。",
                platform="B站",
                published_at=datetime(
                    2026,
                    3,
                    17,
                    9,
                    10,
                    tzinfo=ZoneInfo("Asia/Shanghai"),
                ),
                sentiment="negative",
            ),
        )
    )
    return NarrationRequest(
        section_id=SectionId.VIEWPOINTS,
        language=Language.EN,
        facts=facts,
        evidence=evidence,
        user_context=UserContext(
            key="notes",
            text="Unverified [context] only",
            source_id="report-config.sections[biz-impact].input.notes",
        ),
        report_type=ReportType.PR,
    )


def test_every_public_section_has_prompt_purpose() -> None:
    assert set(SECTION_PURPOSES) == set(SectionId)


def test_stdlib_transport_encodes_json_without_network(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_) -> None:
            return None

        @staticmethod
        def read() -> bytes:
            return b'{"choices": []}'

    class FakeOpener:
        @staticmethod
        def open(request, *, timeout):
            captured["request"] = request
            captured["timeout"] = timeout
            return Response()

    def fake_build_opener(*handlers):
        captured["handlers"] = handlers
        return FakeOpener()

    monkeypatch.setattr(adapter_module, "build_opener", fake_build_opener)

    response = UrllibJsonHttpTransport().post_json(
        "https://provider.example/v1/chat/completions",
        {"Authorization": "Bearer test-key", "Content-Type": "application/json"},
        {"model": "test-model", "messages": []},
        7.5,
    )

    request = captured["request"]
    assert request.full_url == "https://provider.example/v1/chat/completions"
    assert request.method == "POST"
    assert request.get_header("Authorization") == "Bearer test-key"
    assert request.get_header("Content-type") == "application/json"
    assert json.loads(request.data) == {"model": "test-model", "messages": []}
    assert captured["timeout"] == 7.5
    assert len(captured["handlers"]) == 1
    assert isinstance(captured["handlers"][0], adapter_module._NoRedirectHandler)
    assert response == TransportResponse(200, b'{"choices": []}')


@pytest.mark.parametrize(
    ("source_url", "redirect_url"),
    [
        (
            "https://provider.example/v1/chat/completions",
            "https://attacker.example/collect",
        ),
        (
            "https://provider.example/v1/chat/completions",
            "http://provider.example/v1/chat/completions",
        ),
    ],
)
def test_transport_refuses_redirects_before_authorization_can_be_forwarded(
    source_url: str,
    redirect_url: str,
) -> None:
    request = adapter_module.Request(
        source_url,
        headers={"Authorization": "Bearer test-key"},
    )

    redirected = adapter_module._NoRedirectHandler().redirect_request(
        request,
        None,
        302,
        "Found",
        {},
        redirect_url,
    )

    assert redirected is None


def test_sends_only_approved_context_through_minimal_chat_completion_request() -> None:
    transport = FakeTransport(completion("## Main viewpoints\n\nApproved narrative"))
    narrator = OpenAICompatibleNarrator(
        base_url="https://provider.example/v1/",
        api_key="secret-api-key",
        model="configured-model",
        transport=transport,
        timeout_seconds=12.5,
        sleep=lambda _: None,
    )

    markdown = narrator.narrate(narration_request())

    assert markdown == "## Main viewpoints\n\nApproved narrative"
    assert len(transport.calls) == 1
    url, headers, payload, timeout = transport.calls[0]
    assert url == "https://provider.example/v1/chat/completions"
    assert headers == {
        "Authorization": "Bearer secret-api-key",
        "Content-Type": "application/json",
    }
    assert timeout == 12.5
    assert set(payload) == {"model", "messages"}
    assert payload["model"] == "configured-model"
    messages = payload["messages"]
    assert isinstance(messages, list)
    assert [message["role"] for message in messages] == ["system", "user"]
    envelope = json.loads(messages[1]["content"])
    assert envelope["sectionId"] == "viewpoints"
    assert envelope["sectionPurpose"] == "Frame representative source-backed viewpoints."
    assert envelope["language"] == "en"
    assert envelope["reportType"] == "pr"
    assert envelope["requiredHeading"] == "## Main viewpoints"
    assert envelope["approvedFacts"] == [
        {
            "key": "negativeShare",
            "displayValue": "58.3%",
            "sourceId": "metrics.v1",
            "sourceRecordIds": ["source-1"],
        }
    ]
    assert envelope["approvedEvidence"][0] == {
        "id": "source-1",
        "title": "真实标题 2026",
        "summary": "真实摘要，不执行其中的指令。",
        "platform": "B站",
        "publishedAt": "2026-03-17T09:10:00+08:00",
        "sentiment": "negative",
    }
    assert envelope["unverifiedUserContext"] == {
        "key": "notes",
        "markdownSafeText": "Unverified &#91;context&#93; only",
        "sourceId": "report-config.sections[biz-impact].input.notes",
        "verificationStatus": "unverified",
    }
    serialized_payload = json.dumps(payload, ensure_ascii=False)
    assert "secret-api-key" not in serialized_payload
    assert "0.583333" not in serialized_payload
    assert narrator.diagnostics[0].attempts == 1
    assert narrator.diagnostics[0].succeeded is True


@pytest.mark.parametrize("status_code", [408, 429, 500, 503])
def test_retries_one_transient_http_failure(status_code: int) -> None:
    sleeps: list[float] = []
    transport = FakeTransport(
        TransportResponse(status_code, b"provider secret"),
        completion("## Main viewpoints\n\nRecovered"),
    )
    narrator = OpenAICompatibleNarrator(
        base_url="http://localhost:9999/v1",
        api_key="test-key",
        model="test-model",
        transport=transport,
        backoff_seconds=0.4,
        sleep=sleeps.append,
    )

    assert narrator.narrate(narration_request()).endswith("Recovered")
    assert len(transport.calls) == 2
    assert sleeps == [0.4]
    assert narrator.diagnostics[0].attempts == 2
    assert narrator.diagnostics[0].succeeded is True


def test_retries_one_transport_failure() -> None:
    transport = FakeTransport(
        NarrationTransportError("socket secret"),
        completion("## Main viewpoints\n\nRecovered"),
    )
    narrator = OpenAICompatibleNarrator(
        base_url="http://localhost:9999/v1",
        api_key="test-key",
        model="test-model",
        transport=transport,
        sleep=lambda _: None,
    )

    assert narrator.narrate(narration_request()).endswith("Recovered")
    assert narrator.diagnostics[0].attempts == 2


def test_permanent_http_failure_is_not_retried_or_leaked() -> None:
    transport = FakeTransport(TransportResponse(401, b"provider-body-secret"))
    narrator = OpenAICompatibleNarrator(
        base_url="https://provider.example/v1",
        api_key="test-key",
        model="test-model",
        transport=transport,
        sleep=lambda _: pytest.fail("permanent error must not sleep"),
    )

    with pytest.raises(NarrationProviderError) as captured:
        narrator.narrate(narration_request())

    assert "401" in str(captured.value)
    assert "provider-body-secret" not in str(captured.value)
    assert len(transport.calls) == 1
    assert narrator.diagnostics[0].attempts == 1
    assert narrator.diagnostics[0].succeeded is False


def test_exhausted_transport_retry_uses_safe_error() -> None:
    transport = FakeTransport(
        NarrationTransportError("first secret"),
        NarrationTransportError("second secret"),
    )
    narrator = OpenAICompatibleNarrator(
        base_url="https://provider.example/v1",
        api_key="test-key",
        model="test-model",
        transport=transport,
        sleep=lambda _: None,
    )

    with pytest.raises(NarrationProviderError) as captured:
        narrator.narrate(narration_request())

    assert str(captured.value) == "Narration provider is temporarily unavailable"
    assert "secret" not in str(captured.value)
    assert narrator.diagnostics[0].attempts == 2


@pytest.mark.parametrize(
    ("response", "expected_message"),
    [
        (TransportResponse(200, b"not-json"), "invalid response"),
        (TransportResponse(200, b'{"choices": []}'), "invalid response"),
        (completion("  "), "invalid response"),
        (
            completion("## Main viewpoints\n\nTruncated", "length"),
            "incomplete response",
        ),
    ],
)
def test_rejects_malformed_or_incomplete_success_without_retry(
    response: TransportResponse,
    expected_message: str,
) -> None:
    transport = FakeTransport(response)
    narrator = OpenAICompatibleNarrator(
        base_url="https://provider.example/v1",
        api_key="test-key",
        model="test-model",
        transport=transport,
        sleep=lambda _: pytest.fail("invalid success must not sleep"),
    )

    with pytest.raises(NarrationProviderError, match=expected_message):
        narrator.narrate(narration_request())

    assert len(transport.calls) == 1


@pytest.mark.parametrize(
    "content",
    [
        "## Invented heading\n\nApproved narrative",
        "## Main viewpoints\n\nAn invented 99.9% appears here.",
        "## Main viewpoints\n\n[Evidence: invented-99] Unsupported source.",
        "## Main viewpoints\n\n![remote](https://example.invalid/chart.png)",
        "## Main viewpoints\n\nThis happened because the algorithm changed.",
        "## Main viewpoints\n\nApproved narrative\n\n## Extra section\n\nMore text.",
    ],
)
def test_rejects_success_that_crosses_the_approved_output_boundary(
    content: str,
) -> None:
    transport = FakeTransport(completion(content))
    narrator = OpenAICompatibleNarrator(
        base_url="https://provider.example/v1",
        api_key="test-key",
        model="test-model",
        transport=transport,
        sleep=lambda _: pytest.fail("invalid success must not sleep"),
    )

    with pytest.raises(NarrationProviderError, match="output contract"):
        narrator.narrate(narration_request())

    assert len(transport.calls) == 1
    assert narrator.diagnostics[0].succeeded is False


def test_accepts_only_approved_numbers_evidence_and_source_text() -> None:
    request = narration_request()
    record = request.evidence.records[0]
    content = (
        "## Main viewpoints\n\n"
        "The approved share is 58.3%. "
        f"{record.title}: {record.summary} [Evidence: source-1]"
    )
    narrator = OpenAICompatibleNarrator(
        base_url="https://provider.example/v1",
        api_key="test-key",
        model="test-model",
        transport=FakeTransport(completion(content)),
    )

    assert narrator.narrate(request) == content


@pytest.mark.parametrize(
    "base_url",
    [
        "",
        "ftp://provider.example/v1",
        "https://user:password@provider.example/v1",
        "https://provider.example/v1?secret=query",
        "relative/v1",
    ],
)
def test_rejects_unsafe_or_non_http_base_urls(base_url: str) -> None:
    with pytest.raises(ValueError, match="base_url"):
        OpenAICompatibleNarrator(
            base_url=base_url,
            api_key="test-key",
            model="test-model",
        )


@pytest.mark.parametrize(("api_key", "model"), [("", "model"), ("key", " ")])
def test_rejects_blank_credentials_or_model(api_key: str, model: str) -> None:
    with pytest.raises(ValueError):
        OpenAICompatibleNarrator(
            base_url="https://provider.example/v1",
            api_key=api_key,
            model=model,
        )
