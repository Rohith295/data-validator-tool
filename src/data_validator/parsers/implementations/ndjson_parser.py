import logging
from pathlib import Path

import polars as pl

from data_validator.parsers.base import ParseError, ParserStrategy
from data_validator.parsers.registry import ParserRegistry

log = logging.getLogger(__name__)

_LAZY_THRESHOLD = 100 * 1024 * 1024  # 100 MB


@ParserRegistry.register(".jsonl", ".ndjson")
class NdjsonParser(ParserStrategy):
    """Parses JSONL/NDJSON files. Uses lazy scanning for files > 100 MB."""

    def read(self, path: Path) -> pl.DataFrame | pl.LazyFrame:
        file_size = path.stat().st_size
        if file_size == 0:
            raise ParseError(f"File is empty: {path}")

        try:
            # probe first row for column names, then force all to Utf8
            probe = pl.read_ndjson(path, n_rows=1)
            all_str = {col: pl.Utf8 for col in probe.columns}

            if file_size > _LAZY_THRESHOLD:
                log.info("File %s is %d MB, using lazy scan", path, file_size // (1024 * 1024))
                return pl.scan_ndjson(path, schema_overrides=all_str)
            return pl.read_ndjson(path, schema_overrides=all_str)
        except (pl.exceptions.ComputeError, pl.exceptions.SchemaError) as e:
            raise ParseError(f"Failed to parse NDJSON file {path}: {e}") from e
