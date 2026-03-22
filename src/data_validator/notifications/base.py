from abc import ABC, abstractmethod

from data_validator.models import ValidationReport


class Notifier(ABC):
    """Abstract base for notification targets (console, webhook, log file)."""

    @abstractmethod
    def notify(self, report: ValidationReport) -> None: ...
