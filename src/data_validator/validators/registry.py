import typing
from collections.abc import Callable
from typing import Any, ClassVar

from pydantic import TypeAdapter
from pydantic import ValidationError as PydanticValidationError

from data_validator.validators.base import ValidatorStrategy


def _type_label(tp: Any) -> str:
    origin = typing.get_origin(tp)
    if origin is dict:
        return "a dict"
    if origin is list:
        return "a list"
    return str(tp)


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
    def validate_params(cls, name: str, raw_params: Any) -> Any:
        """Check raw JSON params match what the validator expects (via params_type)."""
        if name not in cls._validators:
            return raw_params  # unknown validator — will fail in get()

        validator_cls = cls._validators[name]
        adapter = TypeAdapter(validator_cls.params_type)
        try:
            return adapter.validate_python(raw_params)
        except PydanticValidationError as e:
            raise ValueError(
                f"'{name}' expects params as "
                f"{_type_label(validator_cls.params_type)}, "
                f"got {type(raw_params).__name__}"
            ) from e
