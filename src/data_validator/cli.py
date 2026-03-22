import logging
from pathlib import Path
from typing import Annotated

import typer

from data_validator.api import (
    describe_validator,
    list_notifiers,
    list_parsers,
    list_validators,
    validate_file,
)
from data_validator.config import ExitCode
from data_validator.notifications.registry import NotifierRegistry
from data_validator.parsers.base import ParseError
from data_validator.schema import SchemaError

app = typer.Typer(name="validate")


def _print_entries(title: str, rows: list[dict[str, str]]) -> None:
    typer.echo(title)
    for row in rows:
        typer.echo(f"- {row['name']}")
        for key, value in row.items():
            if key == "name" or not value:
                continue
            typer.echo(f"  {key.replace('_', ' ')}: {value}")


def _print_validator_details(name: str) -> None:
    info = describe_validator(name)
    typer.echo(info["name"])
    if info["description"]:
        typer.echo(f"  description: {info['description']}")
    typer.echo(f"  params model: {info['params_model']}")
    typer.echo("  params schema:")
    for line in info["params_schema"].splitlines():
        typer.echo(f"    {line}")


@app.command()
def validate(
    file_path: Annotated[
        Path | None, typer.Option("--file_path", "--file-path", help="Path to the data file")
    ] = None,
    schema_path: Annotated[
        Path | None, typer.Option("--schema_path", "--schema-path", help="Path to the JSON schema")
    ] = None,
    notify: Annotated[
        list[str] | None,
        typer.Option("--notify", help="Notifier as type=arg (e.g. webhook=URL, jsonl=path)"),
    ] = None,
    html_report: Annotated[bool, typer.Option("--report", help="Generate HTML report")] = False,
    list_checks: Annotated[
        bool, typer.Option("--list-checks", help="List available validators and exit")
    ] = False,
    describe_check: Annotated[
        str | None, typer.Option("--describe-check", help="Show details for one validator and exit")
    ] = None,
    list_parser_types: Annotated[
        bool, typer.Option("--list-parsers", help="List available parsers and exit")
    ] = False,
    list_notifier_types: Annotated[
        bool, typer.Option("--list-notifiers", help="List available notifiers and exit")
    ] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q")] = False,
) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        level=level,
    )

    if list_checks:
        _print_entries("Validators", list_validators())
        raise typer.Exit(code=ExitCode.PASS)

    if describe_check is not None:
        try:
            _print_validator_details(describe_check)
        except ValueError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(code=ExitCode.ERROR) from None
        raise typer.Exit(code=ExitCode.PASS)

    if list_parser_types:
        _print_entries("Parsers", list_parsers())
        raise typer.Exit(code=ExitCode.PASS)

    if list_notifier_types:
        _print_entries("Notifiers", list_notifiers())
        raise typer.Exit(code=ExitCode.PASS)

    if file_path is None:
        typer.echo("Error: --file_path is required", err=True)
        raise typer.Exit(code=ExitCode.ERROR)

    if schema_path is None:
        typer.echo("Error: --schema_path is required", err=True)
        raise typer.Exit(code=ExitCode.ERROR)

    if not file_path.exists():
        typer.echo(f"Error: file not found: {file_path}", err=True)
        raise typer.Exit(code=ExitCode.ERROR)

    if not schema_path.exists():
        typer.echo(f"Error: schema not found: {schema_path}", err=True)
        raise typer.Exit(code=ExitCode.ERROR)

    try:
        report = validate_file(file_path, schema_path)
    except SchemaError as e:
        typer.echo(f"Schema error: {e}", err=True)
        raise typer.Exit(code=ExitCode.ERROR) from None
    except ParseError as e:
        typer.echo(f"Parse error: {e}", err=True)
        raise typer.Exit(code=ExitCode.ERROR) from None
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=ExitCode.ERROR) from None

    if not quiet:
        NotifierRegistry.get("console")().notify(report)

    for entry in notify or []:
        if "=" not in entry:
            typer.echo(f"Error: --notify must be type=arg, got '{entry}'", err=True)
            raise typer.Exit(code=ExitCode.ERROR)
        name, arg = entry.split("=", 1)
        try:
            notifier_cls = NotifierRegistry.get(name)
        except ValueError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(code=ExitCode.ERROR) from None
        notifier_cls(arg).notify(report)  # type: ignore[call-arg]

    if html_report:
        from data_validator.reporting.history import ReportHistory
        from data_validator.reporting.html_renderer import HTMLReportRenderer

        report_dir = Path("reports")
        report_dir.mkdir(parents=True, exist_ok=True)

        history = ReportHistory()
        history.append(report)

        renderer = HTMLReportRenderer()
        content = renderer.render(
            report,
            history=history.load_recent(file_path=report.file_path),
        )
        dest = report_dir / f"{file_path.stem}_report.html"
        dest.write_bytes(content)
        typer.echo(f"Report saved: {dest.resolve()}")

    raise typer.Exit(code=ExitCode.PASS if report.overall_passed else ExitCode.FAIL)


def main() -> None:
    app()
