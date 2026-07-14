from __future__ import annotations

from datetime import date

import pytest

from report_engine.domain.facts import Fact, FactSet
from report_engine.sections.metrics import MetricsSnapshot


def test_metrics_use_one_auditable_fact_set_for_all_consumers() -> None:
    snapshot = MetricsSnapshot(
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

    facts = snapshot.to_fact_set()

    assert facts.get("articles").raw_value == 12
    assert facts.get("articles").formatted_value == "12"
    assert facts.get("negativeRatio").formatted_value == "58.3%"
    assert facts.get("engagement").raw_value == 26_170
    assert facts.get("peakDay").formatted_value == "3/20"
    assert {fact.source_id for fact in facts.facts} == {"metrics.v1"}
    assert facts.prompt_values()["negativeRatio"] == "58.3%"


def test_fact_set_rejects_duplicate_keys() -> None:
    duplicated = Fact(
        key="articles",
        raw_value=12,
        formatted_value="12",
        source_id="metrics.v1",
    )

    with pytest.raises(ValueError, match="unique"):
        FactSet(facts=(duplicated, duplicated))
