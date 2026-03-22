# Using data-validator in a notebook

Install the library and you have everything — validate data, inspect results, render dashboards, all without leaving the notebook.

```bash
pip install data-validator
```

## Quick start

```python
from data_validator import validate, ReportView

data = [
    {"id": "1", "email": "alice@test.com", "age": "30"},
    {"id": "2", "email": "Bob@test.com", "age": "25"},
    {"id": "3", "email": "", "age": "200"},
]

report = validate(data, checks=[
    {"columns_check": {"params": ["id", "email", "age"]}},
    {"non_empty_check": {"params": ["id", "email"]}},
    {"types_check": {"params": {"age": "integer"}}},
    {"range_check": {"params": {"age": {"min": 0, "max": 150}}}},
])

view = ReportView(report)
view      # renders the full interactive dashboard
```

## The report object

`validate()` returns a plain Pydantic `ValidationReport`. No Polars dependency, fully serializable:

```python
report.overall_passed          # True / False
report.results                 # list of ValidationResult
report.results[0].errors       # list of ValidationError
report.timestamp               # ISO 8601
report.total_elapsed_ms        # pipeline time in ms
report.model_dump()            # dict — for JSON, logging, APIs, etc.
```

## ReportView — interactive exploration

Wrap the report to get Polars DataFrames and HTML rendering:

```python
from data_validator import ReportView

view = ReportView(report)
```

### Summary table

```python
view.summary()
```

Returns a Polars DataFrame — one row per check:

| check | passed | errors | elapsed_ms |
|---|---|---|---|
| columns_check | true | 0 | 0.2 |
| non_empty_check | false | 1 | 0.3 |
| types_check | true | 0 | 0.4 |
| range_check | false | 1 | 0.2 |

### Errors table

```python
view.errors_df()
```

Flat table of every error across all checks:

| check | row | column | message | value |
|---|---|---|---|---|
| non_empty_check | 3 | email | Empty value in column 'email' | |
| range_check | 3 | age | Value 200 exceeds max 150 | 200 |

Since it's a Polars DataFrame, you can filter, group, sort, or export:

```python
import polars as pl

# just email errors
view.errors_df().filter(pl.col("column") == "email")

# error count by check
view.errors_df().group_by("check").len()

# export to CSV
view.errors_df().write_csv("errors.csv")
```

### HTML dashboard

Just type `view` in a cell. It renders the same interactive dashboard that the CLI generates with `--report` — dark theme, Chart.js charts (pass/fail donut, errors-by-validator bar chart), collapsible error tables, stat cards.

```python
view      # Jupyter renders the full dashboard inline
```

### Save or export

```python
view.save_html("report.html")     # write to file
html_string = view.to_html()      # get as string — useful for emailing or embedding
```

## Validating files

If your data is on disk, use `validate_file()`:

```python
from data_validator import validate_file, ReportView

report = validate_file("data.csv", "schema.json")
view = ReportView(report)
view
```

Works with CSV, JSON, JSONL out of the box. Register a custom parser for other formats — see [adding-parsers.md](adding-parsers.md).

## Validating DataFrames

If you already have a Polars DataFrame (or loaded data with pandas and converted):

```python
import polars as pl
from data_validator import validate, ReportView

df = pl.read_csv("data.csv")
# or: df = pl.from_pandas(pandas_df)

report = validate(df, checks=[
    {"non_empty_check": {"params": ["email"]}},
    {"unique_check": {"params": ["id"]}},
])
view = ReportView(report)
view
```

## Full example — cell by cell

```python
# cell 1 — install (first time only)
!pip install data-validator
```

```python
# cell 2 — validate
import polars as pl
from data_validator import validate, ReportView

df = pl.read_csv("users.csv")
report = validate(df, checks=[
    {"columns_check": {"params": ["id", "email", "name", "age"]}},
    {"non_empty_check": {"params": ["id", "email"]}},
    {"unique_check": {"params": ["id"]}},
    {"types_check": {"params": {"age": "integer"}}},
    {"range_check": {"params": {"age": {"min": 0, "max": 150}}}},
])
view = ReportView(report)
```

```python
# cell 3 — dashboard
view
```

```python
# cell 4 — summary
view.summary()
```

```python
# cell 5 — all errors
view.errors_df()
```

```python
# cell 6 — filter to a specific column
view.errors_df().filter(pl.col("column") == "email")
```

```python
# cell 7 — export
view.save_html("users_report.html")
view.errors_df().write_csv("users_errors.csv")
```

```python
# cell 8 — programmatic access
report.overall_passed     # True / False
report.total_elapsed_ms   # how long the whole thing took
report.model_dump()       # full dict for JSON serialization
```

## ReportView reference

| Method / Property | Returns | Description |
|---|---|---|
| `view.passed` | `bool` | `True` if all checks passed |
| `view.summary()` | `pl.DataFrame` | One row per check: name, passed, error count, time |
| `view.errors_df()` | `pl.DataFrame` | Flat table of every error, filterable with Polars |
| `view` (in cell) | HTML | Same dashboard as `--report` — charts, stat cards, error tables |
| `view.to_html()` | `str` | Raw HTML string |
| `view.save_html(path)` | `None` | Write dashboard to a file |
