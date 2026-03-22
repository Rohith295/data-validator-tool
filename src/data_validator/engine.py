import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

from data_validator.models import (
    TabularData,
    ValidationReport,
    ValidationResult,
)
from data_validator.parser import parse
from data_validator.schema import ValidationCheck, load_schema
from data_validator.validators.registry import ValidatorRegistry

log = logging.getLogger(__name__)


class ValidationEngine:
    """Core orchestrator — runs a list of checks against data and builds a report."""

    def run(self, file_path: Path, schema_path: Path) -> ValidationReport:
        """Parse a file + schema, then validate."""
        schema = load_schema(schema_path)
        data = parse(file_path)
        return self.run_checks(
            data=data,
            checks=schema.validations,
            file_path=file_path.as_posix(),
            schema_path=schema_path.as_posix(),
        )

    def run_checks(
        self,
        data: TabularData,
        checks: list[ValidationCheck],
        file_path: str = "<in-memory>",
        schema_path: str = "<inline>",
    ) -> ValidationReport:
        """Run checks against already-parsed data. Used by both CLI and library API."""
        start = time.perf_counter()

        results: list[ValidationResult] = []
        for check in checks:
            validator = ValidatorRegistry.get(check.name)
            result = validator.validate(check.name, data, check.params)
            results.append(result)

        overall_passed = all(r.passed for r in results)
        elapsed = (time.perf_counter() - start) * 1000
        status = "PASS" if overall_passed else "FAIL"
        log.info("Validation completed in %.1fms — %s", elapsed, status)

        # resolve row count if it was deferred (lazy frame)
        row_count = data.row_count
        if row_count < 0 and isinstance(data.df, pl.LazyFrame):
            row_count = data.df.select(pl.len()).collect().item()

        summary = TabularData(
            headers=data.headers,
            file_path=file_path,
            encoding_detected=data.encoding_detected,
            row_count=row_count,
            format=data.format,
        )

        return ValidationReport(
            file_path=file_path,
            schema_path=schema_path,
            overall_passed=overall_passed,
            results=results,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data_summary=summary,
            total_elapsed_ms=round(elapsed, 3),
        )
