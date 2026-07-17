from __future__ import annotations

from report_engine.application.service import ReportApplicationService
from report_engine.runtime import build_report_service_factory
from report_engine.settings import Settings


class _Connection:
    def __init__(self, resource_id: int) -> None:
        self.resource_id = resource_id
        self.entered = False
        self.closed = False

    def __enter__(self):
        self.entered = True
        return self

    def __exit__(self, *_):
        self.closed = True


def test_service_factory_owns_a_connection_and_narrator_per_task() -> None:
    connections: list[_Connection] = []
    narrators: list[object] = []

    def connect(dsn: str, *, connect_timeout: int):
        assert dsn == "postgresql://fixture"
        assert connect_timeout == 5
        connection = _Connection(len(connections) + 1)
        connections.append(connection)
        return connection

    def narrator_factory():
        narrator = object()
        narrators.append(narrator)
        return narrator

    factory = build_report_service_factory(
        Settings(
            pg_dsn="postgresql://fixture",
            llm_base_url=None,
            llm_api_key=None,
            llm_model=None,
        ),
        narrator_factory=narrator_factory,
        connect=connect,
    )

    with factory() as first:
        assert isinstance(first, ReportApplicationService)
        assert connections[0].entered is True
        assert connections[0].closed is False
    with factory() as second:
        assert isinstance(second, ReportApplicationService)

    assert first is not second
    assert len(connections) == 2
    assert connections[0] is not connections[1]
    assert all(connection.closed for connection in connections)
    assert len(narrators) == 2
    assert narrators[0] is not narrators[1]
