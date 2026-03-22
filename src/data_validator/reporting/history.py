import json
from pathlib import Path
from typing import Any

from data_validator.models import ValidationReport


class ReportHistory:
    """Tracks past validation runs in a JSON file for trend reporting."""

    def __init__(self, history_dir: str = "reports") -> None:
        self.history_file = Path(history_dir) / "history.json"

    def append(self, report: ValidationReport) -> None:
        history = self._load()
        entry = {
            "timestamp": report.timestamp,
            "date": report.timestamp[:10],
            "file_path": report.file_path,
            "overall_passed": report.overall_passed,
            "row_count": report.data_summary.row_count,
            "results": [
                {
                    "validator_name": r.validator_name,
                    "passed": r.passed,
                    "error_count": len(r.errors),
                    "elapsed_ms": r.elapsed_ms,
                }
                for r in report.results
            ],
            "total_errors": sum(len(r.errors) for r in report.results),
        }
        history.append(entry)
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.history_file.write_text(json.dumps(history, indent=2), encoding="utf-8")

    def load_recent(
        self,
        limit: int = 30,
        file_path: str | None = None,
    ) -> list[dict[str, Any]]:
        history = self._load()
        if file_path is not None:
            history = [entry for entry in history if entry.get("file_path") == file_path]
        return history[-limit:]

    def _load(self) -> list[dict[str, Any]]:
        if not self.history_file.exists():
            return []
        try:
            data: list[dict[str, Any]] = json.loads(self.history_file.read_text(encoding="utf-8"))
            return data
        except (json.JSONDecodeError, ValueError):
            return []
