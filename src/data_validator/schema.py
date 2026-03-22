import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, model_validator


class SchemaError(Exception):
    """Raised when a schema file is missing, malformed, or references unknown checks."""


class ValidationCheck(BaseModel):
    """Single check entry: a validator name and its parameters."""

    name: str
    params: Any

    @model_validator(mode="before")
    @classmethod
    def parse_entry(cls, data: Any) -> Any:
        """Transform {"columns_check": {"params": [...]}} → canonical form."""
        if not isinstance(data, dict):
            raise SchemaError("Each validation entry must be a dict.")
        if "name" in data:
            return data
        if len(data) != 1:
            raise SchemaError("Each validation entry must be a dict with one key.")
        name = next(iter(data))
        body = data[name]
        if not isinstance(body, dict) or "params" not in body:
            raise SchemaError("Each validation entry must have a 'params' dict.")
        return {"name": name, "params": body["params"]}


class ValidationSchema(BaseModel):
    """Top-level schema: a list of validation checks to run against data."""

    validations: list[ValidationCheck]


def parse_checks(raw_checks: list[dict[str, Any]]) -> list[ValidationCheck]:
    """Parse and validate a list of check dicts into ValidationCheck objects."""
    from data_validator.validators.registry import ValidatorRegistry

    checks: list[ValidationCheck] = []
    for entry in raw_checks:
        try:
            check = ValidationCheck.model_validate(entry)
        except Exception as e:
            if isinstance(e, SchemaError):
                raise
            raise SchemaError(str(e)) from e
        try:
            check.params = ValidatorRegistry.validate_params(
                check.name,
                check.params,
            )
        except ValueError as e:
            raise SchemaError(str(e)) from e
        checks.append(check)
    return checks


def load_schema(schema_path: Path) -> ValidationSchema:
    """Load a JSON schema file and validate all check entries."""
    if not schema_path.exists():
        raise SchemaError(f"Schema file not found: {schema_path}")
    try:
        raw = json.loads(schema_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SchemaError(f"Invalid JSON in schema file: {e}") from e

    if not isinstance(raw, dict) or "validations" not in raw:
        raise SchemaError("Schema must contain a 'validations' key.")

    if not isinstance(raw["validations"], list):
        raise SchemaError("'validations' must be a list.")

    validated = parse_checks(raw["validations"])
    return ValidationSchema(validations=validated)
