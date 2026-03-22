import json
from pathlib import Path

from typer.testing import CliRunner

from data_validator.cli import app

runner = CliRunner()

_ROOT = Path(__file__).resolve().parent.parent / "sample_data"
GOOD_CSV = str(_ROOT / "1.csv")
BAD_CSV = str(_ROOT / "4.csv")
SCHEMA = str(_ROOT / "my_schema.json")


class TestCLI:
    def test_list_checks(self):
        result = runner.invoke(app, ["--list-checks"])
        assert result.exit_code == 0
        assert "range_check" in result.stdout

    def test_describe_check(self):
        result = runner.invoke(app, ["--describe-check", "range_check"])
        assert result.exit_code == 0
        assert "params model" in result.stdout
        assert "RangeCheckParams" in result.stdout

    def test_list_parsers(self):
        result = runner.invoke(app, ["--list-parsers"])
        assert result.exit_code == 0
        assert "CsvParser" in result.stdout

    def test_list_notifiers(self):
        result = runner.invoke(app, ["--list-notifiers"])
        assert result.exit_code == 0
        assert "jsonl" in result.stdout

    def test_pass_exits_zero(self):
        result = runner.invoke(app, ["--file_path", GOOD_CSV, "--schema_path", SCHEMA, "-q"])
        assert result.exit_code == 0

    def test_fail_exits_one(self):
        result = runner.invoke(app, ["--file_path", BAD_CSV, "--schema_path", SCHEMA, "-q"])
        assert result.exit_code == 1

    def test_missing_file_exits_two(self):
        result = runner.invoke(app, ["--file_path", "nope.csv", "--schema_path", SCHEMA])
        assert result.exit_code == 2

    def test_notify_jsonl(self, tmp_path):
        log_file = tmp_path / "audit.jsonl"
        result = runner.invoke(
            app,
            [
                "--file_path",
                GOOD_CSV,
                "--schema_path",
                SCHEMA,
                "-q",
                "--notify",
                f"jsonl={log_file}",
            ],
        )
        assert result.exit_code == 0
        parsed = json.loads(log_file.read_text().strip())
        assert parsed["overall_passed"] is True

    def test_notify_bad_format(self):
        result = runner.invoke(
            app,
            ["--file_path", GOOD_CSV, "--schema_path", SCHEMA, "-q", "--notify", "garbage"],
        )
        assert result.exit_code == 2

    def test_notify_unknown_type(self):
        result = runner.invoke(
            app,
            [
                "--file_path",
                GOOD_CSV,
                "--schema_path",
                SCHEMA,
                "-q",
                "--notify",
                "slack=https://example.com",
            ],
        )
        assert result.exit_code == 2
