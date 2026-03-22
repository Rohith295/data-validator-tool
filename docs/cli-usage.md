# CLI usage

## Basic usage

```bash
validate --file_path data.csv --schema_path schema.json
```

Prints a pass/fail report to the terminal and exits with:

| Exit code | Meaning |
|---|---|
| `0` | All checks passed |
| `1` | One or more checks failed |
| `2` | Error (bad schema, file not found, parse error, etc.) |

Both `--file_path` / `--file-path` and `--schema_path` / `--schema-path` work (underscore or hyphen).

## Options

```bash
validate --help
```

| Flag | Description |
|---|---|
| `--file_path PATH` | Path to the data file (required) |
| `--schema_path PATH` | Path to the JSON schema (required) |
| `--report` | Generate an HTML dashboard in `reports/` |
| `--notify type=arg` | Send results to a notifier (repeatable). Built-in: `webhook=URL`, `jsonl=path` |
| `-v` / `--verbose` | Debug-level logging |
| `-q` / `--quiet` | Suppress console output (exit code still reflects pass/fail) |

## Examples

```bash
# basic validation
validate --file_path data.csv --schema_path schema.json

# HTML dashboard with charts and history tracking
validate --file_path data.csv --schema_path schema.json --report

# append results to a JSONL audit log
validate --file_path data.csv --schema_path schema.json --notify jsonl=results.jsonl

# POST results to a webhook
validate --file_path data.csv --schema_path schema.json --notify webhook=https://example.com/hook

# combine multiple notifiers + report
validate --file_path data.csv --schema_path schema.json -q --report --notify jsonl=audit.jsonl --notify webhook=https://example.com/hook

# verbose logging for debugging
validate --file_path data.csv --schema_path schema.json -v
```

## Schema

A JSON file that says which checks to run. Only include what you care about — everything's optional.

```json
{
    "validations": [
        { "columns_check": { "params": ["id", "name", "age", "email"] } },
        { "non_empty_check": { "params": ["id", "email"] } },
        { "types_check": { "params": { "age": "integer", "name": "string" } } }
    ]
}
```

Six validators ship out of the box:

| Validator | Params | What it does |
|-----------|--------|-------------|
| `columns_check` | list of names | Exact column match — no missing, no extra |
| `non_empty_check` | list of names | These columns can't be blank |
| `types_check` | `{col: type}` | Type enforcement (`string`, `integer`, `float`, `bool`) |
| `unique_check` | list of names | No duplicate values in these columns |
| `regex_check` | `{col: pattern}` | Values must match the regex (fullmatch) |
| `range_check` | `{col: {min, max}}` | Numeric bounds. Both min and max are optional |

A fuller example:

```json
{
    "validations": [
        { "columns_check": { "params": ["id", "email", "age", "signup_date"] } },
        { "non_empty_check": { "params": ["id", "email"] } },
        { "types_check": { "params": { "id": "string", "age": "integer" } } },
        { "unique_check": { "params": ["id"] } },
        { "regex_check": { "params": {
            "email": "^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$",
            "signup_date": "^\\d{4}-\\d{2}-\\d{2}$"
        }}},
        { "range_check": { "params": { "age": { "min": 0, "max": 150 } } } }
    ]
}
```

## Supported formats

- **CSV** (`.csv`, `.tsv`) — auto-detects delimiters (comma, tab, pipe, semicolon), strips BOM, handles quoted fields, embedded newlines, short rows.
- **JSON** (`.json`) — expects an array of objects.
- **JSONL / NDJSON** (`.jsonl`, `.ndjson`) — one JSON object per line.

All parsing goes through Polars, so you don't need to think about chunking or streaming.

## HTML reporting

`--report` generates a dashboard in `reports/` with:

- Summary stat cards (rows scanned, validators run, total errors, total time)
- Pass/fail donut chart
- Errors-by-validator bar chart
- Collapsible per-validator error tables
- History timeline chart (builds up across runs via `reports/history.json`)

The template lives at `src/data_validator/reporting/templates/report.html.j2`. Reports are saved to the `reports/` directory.

## How it works

1. `parser.py` reads the file into a Polars DataFrame (all columns cast to strings)
2. `schema.py` loads the JSON schema and validates each check's params against the validator's declared type
3. `engine.py` loops through the checks, hands each one the DataFrame, collects results
4. Results go to the console (and optionally to HTML report, JSONL log, or webhook)
