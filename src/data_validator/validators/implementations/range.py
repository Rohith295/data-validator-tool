from typing import Any, ClassVar

import polars as pl
from pydantic import BaseModel, ConfigDict, RootModel

from data_validator.models import TabularData
from data_validator.validators.base import ValidatorStrategy, missing_column_error
from data_validator.validators.registry import ValidatorRegistry


class RangeSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min: float | None = None
    max: float | None = None


class RangeCheckParams(RootModel[dict[str, RangeSpec]]): ...


@ValidatorRegistry.register("range_check")
class RangeCheckValidator(ValidatorStrategy):
    """Checks that numeric column values fall within min/max bounds."""

    params_model: ClassVar[type[RangeCheckParams]] = RangeCheckParams

    def check(self, data: TabularData, params: Any) -> None:
        range_map: dict[str, RangeSpec] = params
        available = set(data.headers)

        for col, spec in range_map.items():
            if col not in available:
                self._add_error(missing_column_error(col))
                continue

            non_empty = data.lf.filter(
                pl.col(col).is_not_null() & (pl.col(col).str.strip_chars() != ""),
            )

            with_num = non_empty.with_columns(
                pl.col(col).cast(pl.Float64, strict=False).alias("_num"),
            )

            # non-numeric values
            self._add_errors(
                with_num.filter(pl.col("_num").is_null()),
                col,
                "Cannot parse as number for range check",
            )

            numeric = with_num.filter(pl.col("_num").is_not_null())

            if spec.min is not None:
                self._add_errors(
                    numeric.filter(pl.col("_num") < spec.min),
                    col,
                    f"Below minimum {spec.min}",
                )

            if spec.max is not None:
                self._add_errors(
                    numeric.filter(pl.col("_num") > spec.max),
                    col,
                    f"Exceeds maximum {spec.max}",
                )
