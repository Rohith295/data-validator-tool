from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar

import polars as pl


class ParseError(Exception): ...


class ParserStrategy(ABC):
    """Abstract base for file parsers. Subclass this and implement read()."""

    extensions: ClassVar[list[str]]

    @abstractmethod
    def read(self, path: Path) -> pl.DataFrame | pl.LazyFrame:
        """Read the file into a DataFrame or LazyFrame.

        Parsers may return a LazyFrame for large files so that
        downstream validators benefit from predicate/projection pushdown.
        """
        ...
