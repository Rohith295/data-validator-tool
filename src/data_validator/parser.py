"""File parsing — delegates to the parser registry by extension."""

import logging
from pathlib import Path

import polars as pl

from data_validator.models import TabularData
from data_validator.parsers.base import ParseError as ParseError  # re-export
from data_validator.parsers.registry import ParserRegistry

log = logging.getLogger(__name__)


def _col_names(frame: pl.DataFrame | pl.LazyFrame) -> list[str]:
    """Get column names without triggering LazyFrame schema resolution warnings."""
    if isinstance(frame, pl.LazyFrame):
        return frame.collect_schema().names()
    return frame.columns


def _normalize(
    frame: pl.DataFrame | pl.LazyFrame,
) -> pl.DataFrame | pl.LazyFrame:
    """Cast all columns to strings and fill nulls with empty string.

    Works on both DataFrame and LazyFrame — for lazy frames the operations
    are added to the query plan without triggering execution.
    """
    cols = _col_names(frame)
    return frame.cast({c: pl.Utf8 for c in cols}).fill_null("")


def parse(file_path: Path) -> TabularData:
    """Parse a file from disk into TabularData."""
    ext = file_path.suffix.lower()

    parser = ParserRegistry.get(ext)
    frame = _normalize(parser.read(file_path))

    is_lazy = isinstance(frame, pl.LazyFrame)
    cols = _col_names(frame)

    if is_lazy:
        row_count = -1  # deferred — avoids scanning the entire file
        log.info("Parsed %s (lazy): cols=%d", file_path.name, len(cols))
    else:
        assert isinstance(frame, pl.DataFrame)
        row_count = len(frame)
        log.info("Parsed %s: %d rows x %d cols", file_path.name, row_count, len(cols))

    return TabularData(
        headers=list(cols),
        df=frame,
        file_path=file_path.as_posix(),
        encoding_detected="utf-8",
        row_count=row_count,
        format=ext.lstrip("."),
    )


def parse_dataframe(
    df: pl.DataFrame,
    file_path: str = "<in-memory>",
    fmt: str = "dataframe",
) -> TabularData:
    """Wrap an in-memory DataFrame into TabularData (same normalization as file parsing)."""
    normalized = _normalize(df)
    assert isinstance(normalized, pl.DataFrame)
    return TabularData(
        headers=list(normalized.columns),
        df=normalized,
        file_path=file_path,
        encoding_detected="utf-8",
        row_count=len(normalized),
        format=fmt,
    )
