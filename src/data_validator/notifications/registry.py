from collections.abc import Callable
from typing import ClassVar

from data_validator.notifications.base import Notifier


class NotifierRegistry:
    """Maps notifier names (e.g. "webhook") to their Notifier classes."""

    _notifiers: ClassVar[dict[str, type[Notifier]]] = {}

    @classmethod
    def register(cls, name: str) -> Callable[[type[Notifier]], type[Notifier]]:
        def decorator(notifier_cls: type[Notifier]) -> type[Notifier]:
            cls._notifiers[name] = notifier_cls
            return notifier_cls

        return decorator

    @classmethod
    def get(cls, name: str) -> type[Notifier]:
        if name not in cls._notifiers:
            available = ", ".join(sorted(cls._notifiers))
            raise ValueError(f"Unknown notifier: '{name}'. Available: {available}")
        return cls._notifiers[name]

    @classmethod
    def available(cls) -> list[str]:
        return sorted(cls._notifiers)
