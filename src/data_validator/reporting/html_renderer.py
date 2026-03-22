import json
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from data_validator.formatting import format_count, format_duration
from data_validator.models import ValidationReport

_TEMPLATE_DIR = Path(__file__).parent / "templates"


class HTMLReportRenderer:
    """Renders a validation report as a standalone HTML dashboard."""

    def __init__(self, template_name: str = "report.html.j2") -> None:
        self.env = Environment(
            loader=FileSystemLoader(str(_TEMPLATE_DIR)),
            autoescape=True,
        )
        self.env.filters["duration"] = format_duration
        self.env.filters["count"] = format_count
        self.template_name = template_name

    def render(
        self,
        report: ValidationReport,
        history: list[dict[str, Any]] | None = None,
    ) -> bytes:
        tmpl = self.env.get_template(self.template_name)
        html = tmpl.render(
            report=report,
            history_json=json.dumps(history or []),
        )
        return html.encode("utf-8")
