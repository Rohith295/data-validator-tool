# Adding a new parser

Parsers follow the same registry pattern as validators. One file, one decorator, zero changes to existing code.

For working with results interactively (dashboards, DataFrames, filtering), see [notebook-usage.md](notebook-usage.md).

## As a library user

```python
from pathlib import Path
import polars as pl
from data_validator import ParserStrategy, ParserRegistry

@ParserRegistry.register(".parquet")
class ParquetParser(ParserStrategy):
    def read(self, path: Path) -> pl.DataFrame | pl.LazyFrame:
        return pl.read_parquet(path)
```

After this runs, `validate_file("data.parquet", "schema.json")` just works — the engine picks up `.parquet` from the registry automatically.

## Inside the project

Create a file in `src/data_validator/parsers/implementations/`:

```python
# src/data_validator/parsers/implementations/parquet_parser.py

from pathlib import Path

import polars as pl

from data_validator.parsers.base import ParserStrategy
from data_validator.parsers.registry import ParserRegistry


@ParserRegistry.register(".parquet")
class ParquetParser(ParserStrategy):
    def read(self, path: Path) -> pl.DataFrame | pl.LazyFrame:
        return pl.read_parquet(path)
```

Then add the import in `implementations/__init__.py`:

```python
from data_validator.parsers.implementations.parquet_parser import ParquetParser
```

That's all. The CLI now accepts `.parquet` files.

## What your `read()` method should do

Return a `pl.DataFrame` or `pl.LazyFrame`. That's the only contract. The engine handles:

- Casting all columns to `Utf8` (strings)
- Filling nulls with `""`
- Building the `TabularData` object

So your parser just needs to get the data into a DataFrame — don't worry about type casting or null handling.

For large files, returning a `LazyFrame` (e.g. from `pl.scan_csv()` or `pl.scan_ndjson()`) enables true lazy evaluation — validators build query plans and only materialise error rows, keeping memory low. See the built-in CSV and NDJSON parsers for examples of size-based eager/lazy switching.

## Registering multiple extensions

If your format uses multiple file extensions, pass them all to the decorator:

```python
@ParserRegistry.register(".csv", ".tsv")
class CsvParser(ParserStrategy):
    ...
```

## Error handling

Raise `ParseError` for issues that are the file's fault (empty file, corrupt data, unsupported encoding). The engine catches these and reports them cleanly.

```python
from data_validator.parsers.base import ParseError

class MyParser(ParserStrategy):
    def read(self, path: Path) -> pl.DataFrame:
        if path.stat().st_size == 0:
            raise ParseError(f"File is empty: {path}")
        ...
```

## Existing parsers

Look at these for reference:

- `csv_parser.py` — CSV/TSV with delimiter detection, BOM stripping, lazy scanning for large files
- `json_parser.py` — JSON array of objects
- `ndjson_parser.py` — JSONL / NDJSON (one object per line), lazy scanning for large files
