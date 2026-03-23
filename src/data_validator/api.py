"""API for using data-validator programmatically"""

from __future__ import annotations

import json
from inspect import cleandoc
from pathlib import Path
from typing import Any

import polars as pl
from pydantic import RootModel

from data_validator.engine import ValidationEngine
from data_validator.models import ValidationReport
from data_validator.notifications.registry import NotifierRegistry
from data_validator.parser import parse_dataframe
from data_validator.parsers.registry import ParserRegistry
from data_validator.schema import SchemaError, parse_checks
from data_validator.validators.registry import ValidatorRegistry

_engine = ValidationEngine()


def _summary(text: str | None) -> str:
    if not text:
        return ""
    return cleandoc(text).splitlines()[0]


def _schema_json(model: type[RootModel[Any]]) -> str:
    schema = model.model_json_schema()
    return json.dumps(schema, indent=2, sort_keys=True)


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


def list_validators() -> list[dict[str, str]]:
    """Return registered validators and their declared param models."""
    items: list[dict[str, str]] = []
    for name, validator_cls in ValidatorRegistry.items():
        items.append(
            {
                "name": name,
                "description": _summary(validator_cls.__doc__),
                "params_model": validator_cls.params_model.__name__,
            }
        )
    return items


def describe_validator(name: str) -> dict[str, str]:
    """Return metadata for one registered validator."""
    validator_cls = next((cls for check, cls in ValidatorRegistry.items() if check == name), None)
    if validator_cls is None:
        raise ValueError(f"No validator registered with name: {name}")

    return {
        "name": name,
        "description": _summary(validator_cls.__doc__),
        "params_model": validator_cls.params_model.__name__,
        "params_schema": _schema_json(validator_cls.params_model),
    }


def list_parsers() -> list[dict[str, str]]:
    """Return registered parsers and their supported extensions."""
    items: list[dict[str, str]] = []
    for parser_cls in ParserRegistry.implementations():
        items.append(
            {
                "name": parser_cls.__name__,
                "description": _summary(parser_cls.__doc__),
                "extensions": ", ".join(parser_cls.extensions),
            }
        )
    return items


def list_notifiers() -> list[dict[str, str]]:
    """Return registered notifiers."""
    items: list[dict[str, str]] = []
    for name, notifier_cls in NotifierRegistry.items():
        items.append(
            {
                "name": name,
                "description": _summary(notifier_cls.__doc__),
            }
        )
    return items
