# Adding a new notification channel

Notifications receive a `ValidationReport` after validation completes. The built-in ones handle console output, JSONL logging, and webhook POSTs — but you can add your own for Slack, email, S3 uploads, or anything else.

For working with results interactively (dashboards, DataFrames, filtering), see [notebook-usage.md](notebook-usage.md).

## As a library user

```python
from data_validator import Notifier, validate
from data_validator.models import ValidationReport


class SlackNotifier(Notifier):
    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    def notify(self, report: ValidationReport) -> None:
        status = "PASS" if report.overall_passed else "FAIL"
        message = f"Validation {status} for {report.file_path}"
        import json, urllib.request
        payload = json.dumps({"text": message}).encode()
        req = urllib.request.Request(self.webhook_url, data=payload)
        req.add_header("Content-Type", "application/json")
        urllib.request.urlopen(req)


# use it
report = validate(
    [{"id": "1", "name": "alice"}],
    checks=[{"columns_check": {"params": ["id", "name"]}}],
)
SlackNotifier("https://hooks.slack.com/...").notify(report)
```

Notifiers are standalone — they don't need to register anywhere. Just subclass `Notifier`, implement `notify()`, and call it with a report.

## Inside the project

Create a file in `src/data_validator/notifications/implementations/`:

```python
# src/data_validator/notifications/implementations/slack.py

import json
import logging
import urllib.request

from data_validator.models import ValidationReport
from data_validator.notifications.base import Notifier
from data_validator.notifications.registry import NotifierRegistry

log = logging.getLogger(__name__)


@NotifierRegistry.register("slack")
class SlackNotifier(Notifier):
    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    def notify(self, report: ValidationReport) -> None:
        status = "PASS" if report.overall_passed else "FAIL"
        failed = [r.validator_name for r in report.results if not r.passed]
        text = f"Validation *{status}* for `{report.file_path}`"
        if failed:
            text += f"\nFailed checks: {', '.join(failed)}"

        payload = json.dumps({"text": text}).encode("utf-8")
        req = urllib.request.Request(
            self.webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10):
                log.info("Slack notification sent")
        except Exception as e:
            log.error("Slack notification failed: %s", e)
```

Add the import in `implementations/__init__.py`:

```python
from data_validator.notifications.implementations.slack import SlackNotifier
```

The `@NotifierRegistry.register("slack")` decorator makes it available immediately:

```bash
validate --file_path data.csv --schema_path schema.json --notify slack=https://hooks.slack.com/...
```

## The `Notifier` interface

```python
class Notifier(ABC):
    @abstractmethod
    def notify(self, report: ValidationReport) -> None: ...
```

The `ValidationReport` has everything you need:

- `report.overall_passed` — `True` / `False`
- `report.file_path` — what was validated
- `report.results` — list of `ValidationResult`, each with `.validator_name`, `.passed`, `.errors`, `.elapsed_ms`
- `report.data_summary` — row count, headers, format info
- `report.timestamp` — ISO 8601
- `report.total_elapsed_ms` — total pipeline time
- `report.model_dump()` — serialize to dict for JSON, logging, etc.

## Best practices

- **Don't raise exceptions** from `notify()`. Log errors and move on — a failed notification shouldn't crash the pipeline. See how `WebhookNotifier` wraps the HTTP call in a try/except.
- **Keep it stateless** if possible. Each `notify()` call should be independent.
- **Accept config in `__init__`** — URLs, tokens, timeouts, etc.

## Existing notifiers

- `console.py` — Rich-formatted terminal output with pass/fail panels and error tables
- `jsonl.py` — Appends one JSON line per run to a log file
- `webhook.py` — POSTs the full report as JSON to a URL
