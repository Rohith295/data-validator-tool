"""End-to-end tests: generate data with known errors, validate via CLI + API, verify detection."""

import json
import random
import subprocess
import sys
from pathlib import Path

import polars as pl
import pytest

# ---------------------------------------------------------------------------
# Data generation helpers
# ---------------------------------------------------------------------------

COLUMNS = ["id", "name", "email", "age", "salary", "active", "created_at"]
EMAIL_RE = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
DATE_RE = r"\d{4}-\d{2}-\d{2}"

SCHEMA = {
    "validations": [
        {"columns_check": {"params": COLUMNS}},
        {"non_empty_check": {"params": ["id", "name", "email"]}},
        {"types_check": {"params": {"age": "integer", "salary": "float", "active": "bool"}}},
        {
            "range_check": {
                "params": {"age": {"min": 0, "max": 150}, "salary": {"min": 0, "max": 10000000}}
            }
        },
        {"regex_check": {"params": {"email": EMAIL_RE, "created_at": DATE_RE}}},
        {"unique_check": {"params": ["id"]}},
    ]
}


def _good_row(i: int) -> dict:
    return {
        "id": str(i),
        "name": f"User {i}",
        "email": f"user{i}@example.com",
        "age": str(random.randint(18, 80)),
        "salary": f"{random.uniform(30000, 150000):.2f}",
        "active": random.choice(["true", "false"]),
        "created_at": f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
    }


def _inject_errors(rows: list[dict]) -> dict:
    """Inject known errors into random rows. Returns a summary of what was injected."""
    errors = {
        "empty_name": [],
        "bad_email": [],
        "bad_age_type": [],
        "negative_salary": [],
        "duplicate_id": [],
        "bad_date": [],
    }

    # empty name (non_empty_check)
    idx = random.randint(5, 15)
    rows[idx]["name"] = ""
    errors["empty_name"].append(idx)

    # bad email (regex_check)
    idx = random.randint(20, 30)
    rows[idx]["email"] = "not-an-email"
    errors["bad_email"].append(idx)

    # non-integer age (types_check)
    idx = random.randint(35, 45)
    rows[idx]["age"] = "twenty"
    errors["bad_age_type"].append(idx)

    # negative salary (range_check)
    idx = random.randint(50, 60)
    rows[idx]["salary"] = "-5000.00"
    errors["negative_salary"].append(idx)

    # duplicate id (unique_check)
    idx = random.randint(70, 80)
    rows[idx]["id"] = rows[0]["id"]
    errors["duplicate_id"].append(idx)

    # bad date (regex_check)
    idx = random.randint(85, 95)
    rows[idx]["created_at"] = "not-a-date"
    errors["bad_date"].append(idx)

    return errors


def _generate_test_data(n: int = 100) -> tuple[list[dict], dict]:
    random.seed(42)
    rows = [_good_row(i) for i in range(1, n + 1)]
    injected = _inject_errors(rows)
    return rows, injected


# ---------------------------------------------------------------------------
# File writers
# ---------------------------------------------------------------------------


def _write_csv(rows: list[dict], path: Path) -> None:
    df = pl.DataFrame(rows)
    df.write_csv(path)


def _write_json(rows: list[dict], path: Path) -> None:
    path.write_text(json.dumps(rows, indent=2), encoding="utf-8")


def _write_ndjson(rows: list[dict], path: Path) -> None:
    lines = [json.dumps(row) for row in rows]
    path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def test_dir(tmp_path_factory):
    return tmp_path_factory.mktemp("e2e")


@pytest.fixture(scope="module")
def test_data():
    return _generate_test_data()


@pytest.fixture(scope="module")
def schema_file(test_dir):
    path = test_dir / "schema.json"
    path.write_text(json.dumps(SCHEMA, indent=2), encoding="utf-8")
    return path


@pytest.fixture(scope="module")
def clean_schema_file(test_dir):
    """Schema without unique_check for clean data tests."""
    schema = {
        "validations": [
            {"columns_check": {"params": COLUMNS}},
            {"non_empty_check": {"params": ["id", "name", "email"]}},
            {"types_check": {"params": {"age": "integer", "salary": "float", "active": "bool"}}},
            {
                "range_check": {
                    "params": {"age": {"min": 0, "max": 150}, "salary": {"min": 0, "max": 10000000}}
                }
            },
            {"regex_check": {"params": {"email": EMAIL_RE, "created_at": DATE_RE}}},
            {"unique_check": {"params": ["id"]}},
        ]
    }
    path = test_dir / "clean_schema.json"
    path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    return path


@pytest.fixture(scope="module")
def csv_file(test_dir, test_data):
    rows, _ = test_data
    path = test_dir / "test_data.csv"
    _write_csv(rows, path)
    return path


@pytest.fixture(scope="module")
def json_file(test_dir, test_data):
    rows, _ = test_data
    path = test_dir / "test_data.json"
    _write_json(rows, path)
    return path


@pytest.fixture(scope="module")
def ndjson_file(test_dir, test_data):
    rows, _ = test_data
    path = test_dir / "test_data.jsonl"
    _write_ndjson(rows, path)
    return path


@pytest.fixture(scope="module")
def clean_csv(test_dir):
    random.seed(99)
    rows = [_good_row(i) for i in range(1, 51)]
    path = test_dir / "clean_data.csv"
    _write_csv(rows, path)
    return path


@pytest.fixture(scope="module")
def clean_ndjson(test_dir):
    random.seed(99)
    rows = [_good_row(i) for i in range(1, 51)]
    path = test_dir / "clean_data.jsonl"
    _write_ndjson(rows, path)
    return path


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------


class TestCliE2e:
    """Run the installed CLI binary against generated data."""

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "data_validator", *args],
            capture_output=True,
            text=True,
        )

    def test_csv_detects_errors(self, csv_file, schema_file):
        result = self._run(
            "--file_path",
            str(csv_file),
            "--schema_path",
            str(schema_file),
            "--quiet",
        )
        assert result.returncode == 1, f"Expected FAIL (1), got {result.returncode}"

    def test_json_detects_errors(self, json_file, schema_file):
        result = self._run(
            "--file_path",
            str(json_file),
            "--schema_path",
            str(schema_file),
            "--quiet",
        )
        assert result.returncode == 1, f"Expected FAIL (1), got {result.returncode}"

    def test_ndjson_detects_errors(self, ndjson_file, schema_file):
        result = self._run(
            "--file_path",
            str(ndjson_file),
            "--schema_path",
            str(schema_file),
            "--quiet",
        )
        assert result.returncode == 1, f"Expected FAIL (1), got {result.returncode}"

    def test_clean_csv_passes(self, clean_csv, clean_schema_file):
        result = self._run(
            "--file_path",
            str(clean_csv),
            "--schema_path",
            str(clean_schema_file),
            "--quiet",
        )
        assert result.returncode == 0, (
            f"Expected PASS (0), got {result.returncode}\nstderr: {result.stderr}"
        )

    def test_clean_ndjson_passes(self, clean_ndjson, clean_schema_file):
        result = self._run(
            "--file_path",
            str(clean_ndjson),
            "--schema_path",
            str(clean_schema_file),
            "--quiet",
        )
        assert result.returncode == 0, (
            f"Expected PASS (0), got {result.returncode}\nstderr: {result.stderr}"
        )

    def test_csv_report_generated(self, csv_file, schema_file, test_dir):
        result = self._run(
            "--file_path",
            str(csv_file),
            "--schema_path",
            str(schema_file),
            "--quiet",
            "--report",
        )
        assert "Report saved:" in result.stdout or "Report saved:" in result.stderr

    def test_missing_file_exits_two(self, schema_file):
        result = self._run(
            "--file_path",
            "/nonexistent/file.csv",
            "--schema_path",
            str(schema_file),
        )
        assert result.returncode == 2

    def test_missing_schema_exits_two(self, csv_file):
        result = self._run(
            "--file_path",
            str(csv_file),
            "--schema_path",
            "/nonexistent/schema.json",
        )
        assert result.returncode == 2


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------


class TestApiE2e:
    """Use the Python API against generated data."""

    def test_csv_api_detects_all_error_types(self, csv_file, schema_file, test_data):
        from data_validator import validate_file

        report = validate_file(csv_file, schema_file)
        _, _injected = test_data

        assert not report.overall_passed

        failed_validators = {r.validator_name for r in report.results if not r.passed}
        assert "non_empty_check" in failed_validators, "Should catch empty name"
        assert "regex_check" in failed_validators, "Should catch bad email/date"
        assert "types_check" in failed_validators, "Should catch non-integer age"
        assert "range_check" in failed_validators, "Should catch negative salary"
        assert "unique_check" in failed_validators, "Should catch duplicate id"

    def test_ndjson_api_detects_all_error_types(self, ndjson_file, schema_file, test_data):
        from data_validator import validate_file

        report = validate_file(ndjson_file, schema_file)
        _, _injected = test_data

        assert not report.overall_passed

        failed_validators = {r.validator_name for r in report.results if not r.passed}
        assert "non_empty_check" in failed_validators
        assert "regex_check" in failed_validators
        assert "types_check" in failed_validators
        assert "range_check" in failed_validators
        assert "unique_check" in failed_validators

    def test_json_api_detects_all_error_types(self, json_file, schema_file, test_data):
        from data_validator import validate_file

        report = validate_file(json_file, schema_file)

        assert not report.overall_passed
        failed_validators = {r.validator_name for r in report.results if not r.passed}
        assert len(failed_validators) >= 4, (
            f"Expected >=4 failed validators, got {failed_validators}"
        )

    def test_in_memory_api(self, test_data):
        from data_validator import validate

        rows, _ = test_data
        report = validate(
            rows,
            checks=[
                {"non_empty_check": {"params": ["id", "name", "email"]}},
                {"types_check": {"params": {"age": "integer", "salary": "float"}}},
            ],
        )
        assert not report.overall_passed
        assert len(report.results) == 2

    def test_clean_data_passes_api(self):
        from data_validator import validate

        random.seed(99)
        rows = [_good_row(i) for i in range(1, 51)]
        report = validate(
            rows,
            checks=[
                {"columns_check": {"params": COLUMNS}},
                {"non_empty_check": {"params": ["id", "name", "email"]}},
                {
                    "types_check": {
                        "params": {"age": "integer", "salary": "float", "active": "bool"}
                    }
                },
                {
                    "range_check": {
                        "params": {
                            "age": {"min": 0, "max": 150},
                            "salary": {"min": 0, "max": 10000000},
                        }
                    }
                },
                {"regex_check": {"params": {"email": EMAIL_RE, "created_at": DATE_RE}}},
                {"unique_check": {"params": ["id"]}},
            ],
        )
        assert report.overall_passed, (
            f"Clean data should pass. Failed: "
            f"{[r.validator_name for r in report.results if not r.passed]}"
        )

    def test_error_row_numbers_are_correct(self, csv_file, schema_file, test_data):
        from data_validator import validate_file

        report = validate_file(csv_file, schema_file)
        _, injected = test_data

        # Find the non_empty_check result and verify the row number matches injection
        for r in report.results:
            if r.validator_name == "non_empty_check" and r.errors:
                error_rows = {e.row for e in r.errors}
                for idx in injected["empty_name"]:
                    assert (idx + 1) in error_rows, (
                        f"Expected row {idx + 1} in non_empty errors, got {error_rows}"
                    )

    def test_report_metadata(self, csv_file, schema_file):
        from data_validator import validate_file

        report = validate_file(csv_file, schema_file)
        assert report.data_summary.row_count == 100
        assert report.data_summary.format == "csv"
        assert len(report.results) == 6
        assert report.total_elapsed_ms > 0
        assert report.timestamp
