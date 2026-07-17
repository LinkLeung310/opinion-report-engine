"""Command-line entry point for report generation."""

from __future__ import annotations

from pathlib import Path

import psycopg
import typer
from pydantic import ValidationError

from report_engine.config import ReportConfig
from report_engine.llm.protocol import Narrator
from report_engine.llm.stub import StubNarrator
from report_engine.runtime import build_real_narrator, build_report_service
from report_engine.settings import Settings, SettingsError
from report_engine.storage import CatalogPublicationError


app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Generate traceable public-opinion report bundles.",
)


@app.callback()
def main() -> None:
    """Opinion Report Engine command group."""


@app.command()
def generate(
    config: Path = typer.Option(
        ...,
        "--config",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        help="Path to report-config.json.",
    ),
    out: Path = typer.Option(
        Path("out"),
        "--out",
        file_okay=False,
        resolve_path=True,
        help="Directory that receives versioned report bundles.",
    ),
    stub_llm: bool = typer.Option(
        False,
        "--stub-llm",
        help="Use deterministic offline narration for local verification.",
    ),
) -> None:
    """Generate one report from the fixed JSON input contract."""

    try:
        parsed_config = ReportConfig.model_validate_json(
            config.read_text(encoding="utf-8")
        )
        settings = Settings.from_environment(require_llm=not stub_llm)
        narrator = _build_narrator(settings, stub_llm=stub_llm)
    except (OSError, ValidationError, SettingsError) as exc:
        typer.echo(f"Configuration error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    try:
        with psycopg.connect(settings.pg_dsn, connect_timeout=5) as connection:
            report = build_report_service(connection, narrator).generate(
                parsed_config,
                out,
            )
    except psycopg.Error as exc:
        typer.echo(
            f"Database connection failed ({exc.__class__.__name__}).",
            err=True,
        )
        raise typer.Exit(code=1) from exc
    except CatalogPublicationError as exc:
        typer.echo(f"Report publication failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    target = out / report.report_id
    typer.echo(f"Report generated: {target}")


def _build_narrator(settings: Settings, *, stub_llm: bool) -> Narrator:
    if stub_llm:
        return StubNarrator()
    return build_real_narrator(settings)
