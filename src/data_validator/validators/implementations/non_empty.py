from typing import Any, ClassVar

import polars as pl
from pydantic import RootModel

from data_validator.models import TabularData
from data_validator.validators.base import ValidatorStrategy, missing_column_error
from data_validator.validators.registry import ValidatorRegistry


class NonEmptyCheckParams(RootModel[list[str]]): ...


@ValidatorRegistry.register("non_empty_check")
class NonEmptyCheckValidator(ValidatorStrategy):
    """Flags rows where specified columns are blank or null."""

    params_model: ClassVar[type[NonEmptyCheckParams]] = NonEmptyCheckParams

    def check(self, data: TabularData, params: Any) -> None:
        columns: list[str] = params
        available = set(data.headers)

        for col in columns:
            if col not in available:
                self._add_error(missing_column_error(col))
                continue

            bad = data.lf.filter(
                pl.col(col).is_null() | (pl.col(col).str.strip_chars() == ""),
            )
            self._add_errors(bad, col, f"Empty value in required column '{col}'")
