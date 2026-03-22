import time
from abc import ABC, abstractmethod
from typing import Any, ClassVar

import polars as pl
from pydantic import RootModel

from data_validator.models import TabularData, ValidationError, ValidationResult


def missing_column_error(col: str) -> ValidationError:
    return ValidationError(column=col, message=f"Column '{col}' not found in data")


class ValidatorStrategy(ABC):
    """Abstract base for all validators.

    Subclasses implement ``check()`` using ``data.lf`` and the error helpers.
    See docs/adding-validators.md for usage.
    """

    params_model: ClassVar[type[RootModel[Any]]]

    def __init__(self) -> None:
        self._errors: list[ValidationError] = []

    @property
    def run_once(self) -> bool:
        return False

    def _add_errors(
        self,
        lf: pl.LazyFrame,
        col: str,
        message: str,
        extra_cols: list[str] | None = None,
    ) -> None:
        """Collect *only* the error rows from a filtered LazyFrame.

        Parameters
        ----------
        lf:
            A filtered LazyFrame containing just the rows that failed.
        col:
            The column being validated (used for row value + error column).
        message:
            A plain string or f-string describing the error.
        extra_cols:
            Additional columns to include in the select
            (e.g. ``["_first_row"]`` in unique checks).
        """
        select = ["_row_idx", col] + (extra_cols or [])
        df = lf.select(select).collect(engine="streaming")

        self._errors.extend(
            ValidationError(
                row=row["_row_idx"] + 1,
                column=col,
                message=message,
                value=str(row[col]) if row[col] is not None else "",
            )
            for row in df.iter_rows(named=True)
        )

    def _add_error(self, error: ValidationError) -> None:
        """Append a single ValidationError (e.g. missing column)."""
        self._errors.append(error)

    @abstractmethod
    def check(
        self,
        data: TabularData,
        params: Any,
    ) -> None: ...

    def validate(
        self,
        name: str,
        data: TabularData,
        params: Any,
    ) -> ValidationResult:
        self._errors = []
        start = time.perf_counter()
        self.check(data, params)
        elapsed = (time.perf_counter() - start) * 1000
        return ValidationResult(
            validator_name=name,
            passed=len(self._errors) == 0,
            errors=self._errors,
            elapsed_ms=round(elapsed, 3),
        )
