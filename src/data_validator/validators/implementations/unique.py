from typing import Any, ClassVar

import polars as pl
from pydantic import RootModel

from data_validator.models import TabularData
from data_validator.validators.base import ValidatorStrategy, missing_column_error
from data_validator.validators.registry import ValidatorRegistry


class UniqueCheckParams(RootModel[list[str]]): ...


@ValidatorRegistry.register("unique_check")
class UniqueCheckValidator(ValidatorStrategy):
    """Flags duplicate values in the specified columns."""

    params_model: ClassVar[type[UniqueCheckParams]] = UniqueCheckParams

    def check(self, data: TabularData, params: Any) -> None:
        columns: list[str] = params
        available = set(data.headers)

        for col in columns:
            if col not in available:
                self._add_error(missing_column_error(col))
                continue

            non_empty = data.lf.filter(
                pl.col(col).is_not_null() & (pl.col(col).str.strip_chars() != ""),
            )

            first_seen = non_empty.group_by(col).agg(
                pl.col("_row_idx").min().alias("_first_row"),
            )

            dupe_rows = (
                non_empty.filter(pl.col(col).is_duplicated())
                .join(first_seen, on=col, how="left")
                .filter(pl.col("_row_idx") != pl.col("_first_row"))
                .sort("_row_idx")
            )

            self._add_errors(
                dupe_rows,
                col,
                "Duplicate value",
            )
