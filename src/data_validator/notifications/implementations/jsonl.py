import json
from pathlib import Path

from data_validator.models import ValidationReport
from data_validator.notifications.base import Notifier
from data_validator.notifications.registry import NotifierRegistry


@NotifierRegistry.register("jsonl")
class JSONLogNotifier(Notifier):
    """Appends one JSON line per run to a log file."""

    def __init__(self, log_path: str | Path) -> None:
        self.log_path = Path(log_path)

    def notify(self, report: ValidationReport) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(report.model_dump(), default=str, separators=(",", ":"))
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
