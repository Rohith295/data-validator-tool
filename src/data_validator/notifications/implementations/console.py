from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from data_validator.formatting import format_duration
from data_validator.models import ValidationReport
from data_validator.notifications.base import Notifier
from data_validator.notifications.registry import NotifierRegistry


@NotifierRegistry.register("console")
class ConsoleNotifier(Notifier):
    """Rich-formatted terminal output with pass/fail panels and error tables."""

    def __init__(self) -> None:
        self.console = Console()

    def notify(self, report: ValidationReport) -> None:
        status = "[bold green]PASS[/]" if report.overall_passed else "[bold red]FAIL[/]"
        self.console.print()
        self.console.print(
            Panel(
                f"File: [cyan]{report.file_path}[/]\n"
                f"Schema: [cyan]{report.schema_path}[/]\n"
                f"Result: {status}",
                title="Validation Report",
                border_style="green" if report.overall_passed else "red",
            )
        )

        for result in report.results:
            icon = "[green]✓[/]" if result.passed else "[red]✗[/]"
            self.console.print(
                f"\n  {icon} [bold]{result.validator_name}[/]  [dim]({result.elapsed_ms:.1f}ms)[/]"
            )

            if result.errors:
                table = Table(show_header=True, padding=(0, 1), expand=False)
                table.add_column("Row", style="yellow", justify="right")
                table.add_column("Column", style="cyan")
                table.add_column("Message", style="white")
                table.add_column("Value", style="dim")

                for err in result.errors[:20]:
                    table.add_row(
                        str(err.row) if err.row is not None else "-",
                        err.column or "-",
                        err.message,
                        err.value or "-",
                    )

                if len(result.errors) > 20:
                    table.add_row(
                        "", "", f"[dim]... and {len(result.errors) - 20} more errors[/]", ""
                    )

                self.console.print(table)

        passed = sum(1 for r in report.results if r.passed)
        total = len(report.results)
        total_errors = sum(len(r.errors) for r in report.results)
        summary = f"\n  [dim]{passed}/{total} checks passed"
        if total_errors:
            summary += f" · {total_errors} errors found"
        summary += f" · {format_duration(report.total_elapsed_ms)}[/]"
        self.console.print(summary)
        self.console.print()
