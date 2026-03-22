import re
from typing import Any, ClassVar

import polars as pl

from data_validator.models import TabularData, ValidationError
from data_validator.validators.base import ValidatorStrategy, missing_column_error
from data_validator.validators.registry import ValidatorRegistry


@ValidatorRegistry.register("regex_check")
class RegexCheckValidator(ValidatorStrategy):
    """Validates that column values match given regex patterns (fullmatch)."""

    params_type: ClassVar[Any] = dict[str, str]

    def check(self, data: TabularData, params: Any) -> None:
        pattern_map: dict[str, str] = params
        available = set(data.headers)

        for col, pattern in pattern_map.items():
            if col not in available:
                self._add_error(missing_column_error(col))
                continue

            try:
                re.compile(pattern)
            except re.error as e:
                self._add_error(ValidationError(column=col, message=f"Invalid regex pattern: {e}"))
                continue

            non_empty = data.lf.filter(
                pl.col(col).is_not_null() & (pl.col(col).str.strip_chars() != ""),
            )

            full_pattern = f"^(?:{pattern})$"
            bad = non_empty.filter(~pl.col(col).str.contains(full_pattern))

            self._add_errors(bad, col, f"Value does not match pattern '{pattern}'")
