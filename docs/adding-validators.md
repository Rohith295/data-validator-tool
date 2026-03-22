# Adding a new validator

The validator system is set up so you never touch the engine, schema loader, or CLI to add a check. One file does the job — or if you're using data-validator as a library, you don't even need that. Just define and register your class before calling `validate()`.

For working with results interactively (dashboards, DataFrames, filtering), see [notebook-usage.md](notebook-usage.md).

## As a library user (notebook / script)

```python
from typing import Any, ClassVar
import polars as pl
from data_validator import validate, ValidatorStrategy, ValidatorRegistry
from data_validator.models import TabularData, ValidationError

@ValidatorRegistry.register("lowercase_check")
class LowercaseCheckValidator(ValidatorStrategy):
    params_type: ClassVar[Any] = list[str]

    def check(self, data: TabularData, params: Any) -> None:
        columns: list[str] = params
        for col in columns:
            bad = data.lf.filter(pl.col(col) != pl.col(col).str.to_lowercase())
            self._add_errors(bad, col, f"Value is not lowercase")

# use it immediately
report = validate(
    [{"email": "Alice@test.com"}, {"email": "bob@test.com"}],
    checks=[{"lowercase_check": {"params": ["email"]}}],
)
```

That's it. The `@ValidatorRegistry.register()` decorator makes it available as soon as the class is defined.

One expectation for new validators: define the validator's input contract as well as its row-level logic. In practice that means adding a Pydantic `params_model` on the validator class. The goal is to reject bad schema config early and keep `check()` focused on data validation.

## Inside the project (contributing a built-in check)

Say you want to add the same `lowercase_check` as a built-in. Create one file:

```python
# src/data_validator/validators/implementations/lowercase.py

from typing import Any, ClassVar

import polars as pl
from pydantic import RootModel

from data_validator.models import TabularData, ValidationError
from data_validator.validators.base import ValidatorStrategy, missing_column_error
from data_validator.validators.registry import ValidatorRegistry


class LowercaseCheckParams(RootModel[list[str]]):
    pass


@ValidatorRegistry.register("lowercase_check")
class LowercaseCheckValidator(ValidatorStrategy):
    params_model: ClassVar[type[LowercaseCheckParams]] = LowercaseCheckParams

    def check(self, data: TabularData, params: Any) -> None:
        columns: list[str] = params

        for col in columns:
            if col not in data.headers:
                self._add_error(missing_column_error(col))
                continue

            bad = data.lf.filter(pl.col(col) != pl.col(col).str.to_lowercase())
            self._add_errors(bad, col, f"Value is not lowercase")
```

Then add the import in `implementations/__init__.py` so the decorator runs at startup:

```python
from data_validator.validators.implementations.lowercase import LowercaseCheckValidator
```

Now it works in any schema file:

```json
{ "lowercase_check": { "params": ["email", "username"] } }
```

If your validator accepts richer config than a plain list or dict, model that directly in `params_model`. A validator is not finished until its schema params are validated.

## How it works under the hood

### `data.lf`

A Polars **LazyFrame**. Use standard Polars expressions to filter down to bad rows — this builds a query plan (no data loaded yet). Polars optimizes and executes it only when errors are collected.

### `self._add_errors(lf, col, message)`

Collects *only* the filtered error rows from the LazyFrame and converts them to `ValidationError` objects. The base class manages the error list — you never create or return one yourself.

- `lf` — a filtered LazyFrame (the "bad" rows)
- `col` — the column being checked
- `message` — a plain string or f-string describing the error
- `extra_cols` (optional) — additional columns to include in the select (e.g. `["_first_row"]` in unique checks)

### `self._add_error(error)`

Append a single `ValidationError` directly — useful for structural issues like missing columns or invalid regex patterns.

### `params_model`

Tells the registry how to validate schema params before your `check()` runs. If someone passes `{"email": "pattern"}` to a validator expecting a list of column names, it blows up at schema load time with a clear error — not somewhere in your code at runtime.

Common patterns:

| `params_model` | Schema shape | Use case |
|---|---|---|
| `RootModel[list[str]]` | `["col1", "col2"]` | Column name lists |
| `RootModel[dict[str, str]]` | `{"col": "value"}` | Column-to-value mappings |
| `RootModel[dict[str, RangeSpec]]` | `{"col": {"min": 0, "max": 100}}` | Richer nested config |

If you need stricter rules, put them on the Pydantic model itself. `RangeSpec` uses `extra="forbid"` to reject misspelled keys, and `RegexCheckParams` validates that every regex compiles.

### `@ValidatorRegistry.register("name")`

Connects your class to the schema key. The name you pass here is the key users write in their JSON schema.

### `run_once`

Override this property to return `True` if your check doesn't need row data — like `columns_check` which only compares headers. This is a hint for the engine, not strictly enforced, but it communicates intent.
