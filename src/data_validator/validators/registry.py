from collections.abc import Callable
from typing import Any, ClassVar

from pydantic import ValidationError as PydanticValidationError

from data_validator.validators.base import ValidatorStrategy


def _format_pydantic_error(name: str, err: PydanticValidationError) -> str:
    details: list[str] = []
    for item in err.errors():
        loc = " -> ".join(str(part) for part in item.get("loc", ()))
        msg = item.get("msg", "invalid value")
        if loc:
            details.append(f"{loc}: {msg}")
        else:
            details.append(msg)
    joined = "; ".join(details)
    return f"Invalid params for '{name}': {joined}"


class ValidatorRegistry:
    """Maps check names (e.g. "columns_check") to their ValidatorStrategy classes."""

    _validators: ClassVar[dict[str, type[ValidatorStrategy]]] = {}

    @classmethod
    def register(
        cls,
        name: str,
    ) -> Callable[[type[ValidatorStrategy]], type[ValidatorStrategy]]:
        def decorator(validator_cls: type[ValidatorStrategy]) -> type[ValidatorStrategy]:
            cls._validators[name] = validator_cls
            return validator_cls

        return decorator

    @classmethod
    def get(cls, name: str) -> ValidatorStrategy:
        if name not in cls._validators:
            raise ValueError(f"No validator registered with name: {name}")
        return cls._validators[name]()

    @classmethod
    def items(cls) -> list[tuple[str, type[ValidatorStrategy]]]:
        return sorted(cls._validators.items())

    @classmethod
    def validate_params(cls, name: str, raw_params: Any) -> Any:
        """Validate raw JSON params against the validator's Pydantic model."""
        if name not in cls._validators:
            raise ValueError(f"No validator registered with name: {name}")

        validator_cls = cls._validators[name]
        try:
            parsed = validator_cls.params_model.model_validate(raw_params)
        except PydanticValidationError as e:
            raise ValueError(_format_pydantic_error(name, e)) from e

        return parsed.root
