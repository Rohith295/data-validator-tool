from typing import Any, ClassVar, Literal

import polars as pl

from data_validator.models import TabularData
from data_validator.validators.base import ValidatorStrategy, missing_column_error
from data_validator.validators.registry import ValidatorRegistry

_INTEGER_RE = r"^-?\d+$"
_FLOAT_RE = r"^-?(\d+\.?\d*|\d*\.?\d+)([eE][+-]?\d+)?$"
_BOOL_VALUES = ["true", "false", "0", "1"]


@ValidatorRegistry.register("types_check")
class TypesCheckValidator(ValidatorStrategy):
    """Validates that column values match expected types (string, integer, float, bool)."""

    params_type: ClassVar[Any] = dict[str, Literal["string", "integer", "float", "bool"]]

    def check(self, data: TabularData, params: Any) -> None:
        type_map: dict[str, Literal["string", "integer", "float", "bool"]] = params
        available = set(data.headers)

        for col, expected_type in type_map.items():
            if col not in available:
                self._add_error(missing_column_error(col))
                continue

            if expected_type == "string":
                continue

            non_empty = data.lf.filter(
                pl.col(col).is_not_null() & (pl.col(col).str.strip_chars() != ""),
            )

            if expected_type == "integer":
                bad = non_empty.filter(~pl.col(col).str.contains(_INTEGER_RE))
            elif expected_type == "float":
                bad = non_empty.filter(~pl.col(col).str.contains(_FLOAT_RE))
            elif expected_type == "bool":
                bad = non_empty.filter(
                    ~pl.col(col).str.to_lowercase().is_in(_BOOL_VALUES),
                )

            self._add_errors(bad, col, f"Expected type '{expected_type}'")
