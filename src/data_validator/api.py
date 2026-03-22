"""Programmatic API for using data-validator from Python code."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import polars as pl

from data_validator.engine import ValidationEngine
from data_validator.models import ValidationReport
from data_validator.parser import parse_dataframe
from data_validator.schema import SchemaError, parse_checks

_engine = ValidationEngine()


def validate(
    data: pl.DataFrame | list[dict[str, Any]],
    checks: list[dict[str, Any]],
) -> ValidationReport:
    """Run checks against in-memory data (DataFrame or list of dicts)."""
    df = pl.DataFrame(data) if isinstance(data, list) else data
    tabular = parse_dataframe(df)

    try:
        parsed = parse_checks(checks)
    except SchemaError as e:
        raise ValueError(str(e)) from e

    return _engine.run_checks(data=tabular, checks=parsed)


def validate_file(
    file_path: str | Path,
    schema_path: str | Path,
) -> ValidationReport:
    """Validate a file against a JSON schema."""
    return _engine.run(
        file_path=Path(file_path),
        schema_path=Path(schema_path),
    )
