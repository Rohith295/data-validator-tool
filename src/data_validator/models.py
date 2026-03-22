from __future__ import annotations

from typing import Any

import polars as pl
from pydantic import BaseModel, ConfigDict, Field


class TabularData(BaseModel):
    """Parsed file contents: column headers, row count, and the in-memory DataFrame."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    headers: list[str]
    df: Any = Field(default=None, exclude=True)
    file_path: str
    encoding_detected: str
    row_count: int
    format: str

    @property
    def is_lazy(self) -> bool:
        """True when the underlying frame is a LazyFrame (large file, not yet collected)."""
        return isinstance(self.df, pl.LazyFrame)

    @property
    def lf(self) -> pl.LazyFrame:
        """LazyFrame with ``_row_idx`` attached. Works for both eager and lazy sources."""
        df: pl.DataFrame | pl.LazyFrame = self.df
        if isinstance(df, pl.LazyFrame):
            return df.with_row_index("_row_idx")
        return df.lazy().with_row_index("_row_idx")

    def as_lazy(self) -> pl.LazyFrame:
        """Return a LazyFrame regardless of whether df is eager or lazy."""
        df: pl.DataFrame | pl.LazyFrame = self.df
        if isinstance(df, pl.LazyFrame):
            return df
        return df.lazy()


class ValidationError(BaseModel):
    """Single validation failure tied to an optional row/column location."""

    row: int | None = None
    column: str | None = None
    message: str
    value: str | None = None


class ValidationResult(BaseModel):
    """Outcome of one check: pass/fail, list of errors, and elapsed time."""

    validator_name: str
    passed: bool
    errors: list[ValidationError]
    elapsed_ms: float


class ValidationReport(BaseModel):
    """Full validation run output returned by the engine."""

    file_path: str
    schema_path: str
    overall_passed: bool
    results: list[ValidationResult]
    timestamp: str
    data_summary: TabularData
    total_elapsed_ms: float | None = None
