import csv
import logging
from pathlib import Path

import polars as pl

from data_validator.parsers.base import ParseError, ParserStrategy
from data_validator.parsers.registry import ParserRegistry

log = logging.getLogger(__name__)

_SNIFF_BYTES = 8192
_LAZY_THRESHOLD = 100 * 1024 * 1024  # 100 MB


@ParserRegistry.register(".csv", ".tsv")
class CsvParser(ParserStrategy):
    """CSV parser. Uses lazy scanning for files > 100 MB."""

    def read(self, path: Path) -> pl.DataFrame | pl.LazyFrame:
        file_size = path.stat().st_size
        if file_size == 0:
            raise ParseError(f"File is empty: {path}")

        sep = self._detect_separator(path)

        frame: pl.DataFrame | pl.LazyFrame
        if file_size > _LAZY_THRESHOLD:
            log.info("File %s is %d MB, using lazy scan", path, file_size // (1024 * 1024))
            frame = self._read_lazy(path, sep)
        else:
            frame = self._read_eager(path, sep)

        col_names = (
            frame.collect_schema().names() if isinstance(frame, pl.LazyFrame) else frame.columns
        )

        clean_names = {c: c.strip().lstrip("\ufeff") for c in col_names}
        frame = frame.rename(clean_names)

        cleaned = list(clean_names.values())
        frame = frame.with_columns(pl.col(c).str.strip_chars() for c in cleaned)

        return frame

    @staticmethod
    def _read_eager(path: Path, sep: str) -> pl.DataFrame:
        try:
            return pl.read_csv(
                path,
                separator=sep,
                infer_schema_length=0,
                ignore_errors=False,
                encoding="utf8-lossy",
            )
        except pl.exceptions.ComputeError as e:
            raise ParseError(
                f"CSV has rows with inconsistent column counts in {path}. "
                f"Values containing the delimiter ('{sep}') must be quoted. "
                f"Detail: {e}"
            ) from e

    @staticmethod
    def _read_lazy(path: Path, sep: str) -> pl.LazyFrame:
        try:
            return pl.scan_csv(
                path,
                separator=sep,
                infer_schema_length=0,
                ignore_errors=False,
                encoding="utf8-lossy",
            )
        except pl.exceptions.ComputeError as e:
            raise ParseError(
                f"CSV has rows with inconsistent column counts in {path}. "
                f"Values containing the delimiter ('{sep}') must be quoted. "
                f"Detail: {e}"
            ) from e

    @staticmethod
    def _detect_separator(path: Path) -> str:
        if path.suffix.lower() == ".tsv":
            return "\t"
        with open(
            path,
            encoding="utf-8",
            errors="replace",
            newline="",
        ) as f:
            sample = f.read(_SNIFF_BYTES)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",\t|;")
            return dialect.delimiter
        except csv.Error:
            log.warning("Could not detect delimiter for %s, defaulting to comma", path)
            return ","
