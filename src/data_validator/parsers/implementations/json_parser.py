from pathlib import Path

import polars as pl

from data_validator.parsers.base import ParseError, ParserStrategy
from data_validator.parsers.registry import ParserRegistry


@ParserRegistry.register(".json")
class JsonParser(ParserStrategy):
    """Parses a JSON file containing an array of objects."""

    def read(self, path: Path) -> pl.DataFrame:
        if path.stat().st_size == 0:
            raise ParseError(f"File is empty: {path}")

        try:
            df = pl.read_json(path)
        except (pl.exceptions.ComputeError, pl.exceptions.SchemaError) as e:
            raise ParseError(f"Failed to parse JSON file {path}: {e}") from e
        return df.cast({c: pl.Utf8 for c in df.columns})
