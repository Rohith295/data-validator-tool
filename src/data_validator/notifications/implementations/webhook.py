import json
import logging
import urllib.request

from data_validator.models import ValidationReport
from data_validator.notifications.base import Notifier
from data_validator.notifications.registry import NotifierRegistry

log = logging.getLogger(__name__)


@NotifierRegistry.register("webhook")
class WebhookNotifier(Notifier):
    """POSTs the full report as JSON to a URL."""

    def __init__(self, url: str, timeout: int = 10) -> None:
        self.url = url
        self.timeout = timeout

    def notify(self, report: ValidationReport) -> None:
        payload = json.dumps(report.model_dump(), default=str).encode("utf-8")
        req = urllib.request.Request(
            self.url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                log.info("Webhook delivered: %d %s", resp.status, self.url)
        except Exception as e:
            log.error("Webhook failed for %s: %s", self.url, e)
