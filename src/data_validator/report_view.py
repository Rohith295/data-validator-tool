from __future__ import annotations

from typing import Any

import polars as pl

from data_validator.models import ValidationReport


class ReportView:
    """Wraps a ValidationReport with Polars DataFrames and HTML rendering for notebooks."""

    def __init__(self, report: ValidationReport) -> None:
        self.report = report

    @property
    def passed(self) -> bool:
        return self.report.overall_passed

    def summary(self) -> pl.DataFrame:
        """One row per check with pass/fail, error count, and timing."""
        return pl.DataFrame(
            [
                {
                    "check": r.validator_name,
                    "passed": r.passed,
                    "errors": len(r.errors),
                    "elapsed_ms": r.elapsed_ms,
                }
                for r in self.report.results
            ]
        )

    def errors_df(self) -> pl.DataFrame:
        """Flat table of every error across all checks."""
        rows: list[dict[str, Any]] = []
        for r in self.report.results:
            for e in r.errors:
                rows.append(
                    {
                        "check": r.validator_name,
                        "row": e.row,
                        "column": e.column,
                        "message": e.message,
                        "value": e.value,
                    }
                )
        if rows:
            return pl.DataFrame(rows)
        return pl.DataFrame(
            schema={
                "check": pl.Utf8,
                "row": pl.Int64,
                "column": pl.Utf8,
                "message": pl.Utf8,
                "value": pl.Utf8,
            },
        )

    def _repr_html_(self) -> str:
        import html as html_mod

        from data_validator.reporting.html_renderer import HTMLReportRenderer

        renderer = HTMLReportRenderer()
        html_bytes = renderer.render(self.report, history=[])
        raw_html = html_bytes.decode("utf-8")
        escaped = html_mod.escape(raw_html)
        return (
            f'<iframe srcdoc="{escaped}" '
            f'style="width:100%;height:720px;border:none;border-radius:8px;" '
            f'sandbox="allow-scripts">'
            f"</iframe>"
        )

    def to_html(self, history: list[dict[str, Any]] | None = None) -> str:
        from data_validator.reporting.html_renderer import HTMLReportRenderer

        renderer = HTMLReportRenderer()
        html_bytes = renderer.render(self.report, history=history)
        return html_bytes.decode("utf-8")

    def save_html(
        self,
        path: str,
        history: list[dict[str, Any]] | None = None,
    ) -> None:
        from pathlib import Path

        html = self.to_html(history=history)
        Path(path).write_text(html, encoding="utf-8")

    def __repr__(self) -> str:
        status = "PASS" if self.report.overall_passed else "FAIL"
        n = len(self.report.results)
        return f"ReportView({status}, {n} checks)"
