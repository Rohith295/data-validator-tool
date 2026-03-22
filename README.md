# data-validator

CLI tool and Python library that validates data files against a schema. You define what columns should exist, what types they should be, which ones can't be empty, etc. — the tool does the rest. Currently supports CSV and JSON files.

Built for Python 3.10+. Uses Polars under the hood so it doesn't fall over on large files.

## Install

```bash
pip install data-validator
```

Or from source:

```bash
pip install -e ".[dev]"
```

## Quick start

### CLI

```bash
validate --file_path data.csv --schema_path schema.json
```

Exits with 0 (pass), 1 (fail), or 2 (error). Add `--report` for an HTML dashboard, or `--notify` to send results somewhere:

```bash
validate --file_path data.csv --schema_path schema.json --notify webhook=https://example.com/hook
validate --file_path data.csv --schema_path schema.json --notify jsonl=audit.jsonl
validate --file_path data.csv --schema_path schema.json --notify jsonl=audit.jsonl --notify webhook=https://example.com/hook
```

### Python

```python
from data_validator import validate, ReportView

report = validate(
    [{"id": "1", "name": "alice", "age": "30"}],
    checks=[
        {"columns_check": {"params": ["id", "name", "age"]}},
        {"non_empty_check": {"params": ["id"]}},
        {"types_check": {"params": {"age": "integer"}}},
    ],
)
print(report.overall_passed)   # True

# in a notebook
view = ReportView(report)
view              # renders the full HTML dashboard inline
view.summary()    # Polars DataFrame — one row per check
view.errors_df()  # Polars DataFrame — every error, filterable
```

## Project structure

```
src/data_validator/
├── cli.py                 # start here — Typer CLI
├── api.py                 # validate() and validate_file()
├── engine.py              # wires schema + parser + validators together
├── schema.py              # loads and validates the JSON schema
├── models.py              # Pydantic models (TabularData, ValidationReport, etc.)
├── config.py              # exit codes
├── parser.py              # routes files to the right parser
├── parsers/               # CSV, JSON, NDJSON
│   ├── base.py
│   ├── registry.py
│   └── implementations/
├── validators/            # columns, types, non_empty, unique, range, regex
│   ├── base.py
│   ├── registry.py
│   └── implementations/
├── notifications/         # console, webhook, jsonl
│   ├── base.py
│   ├── registry.py
│   └── implementations/
├── reporting/             # HTML reports + history
│   ├── html_renderer.py
│   └── history.py
└── report_view.py         # notebook helper (Polars DataFrames)
```

**Reading order:** `cli.py` → `api.py` → `engine.py` → `schema.py` / `parser.py` → `validators/` → `notifications/`

Parsers, validators, and notifications all follow the same pattern: abstract base → registry with `@register` decorator → `implementations/` folder. See the [docs](#docs) for step-by-step guides on extending each one.


## Docs

- [CLI usage](docs/cli-usage.md) — all options, schema reference, supported formats, reporting
- [Notebook usage](docs/notebook-usage.md) — interactive dashboards, DataFrames, cell-by-cell examples
- [Examples](examples/README.md) — runnable notebooks using the Python API and sample data
- [Adding a validator](docs/adding-validators.md) — custom data checks
- [Adding a parser](docs/adding-parsers.md) — new file format support
- [Adding a notification channel](docs/adding-notifications.md) — Slack, email, S3, etc.

## Dev

```bash
make setup     # create venv + install deps (checks Python >= 3.10)
make test      # unit tests
make lint      # ruff
make typecheck # mypy
make all       # lint + typecheck + unit + e2e
make build     # build the library
```

### End-to-end tests

Generates test data with known errors across CSV, JSON, and NDJSON, then validates via both CLI and API in isolated environments across Python 3.11, 3.12, and 3.13.

```bash
make test-e2e
```

Requires [pyenv](https://github.com/pyenv/pyenv) — missing Python versions are installed automatically.
