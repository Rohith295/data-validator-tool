import polars as pl

from data_validator.models import TabularData
from data_validator.validators.implementations.regex import RegexCheckValidator


def make_data(headers, rows):
    df = pl.DataFrame(rows, schema={h: pl.Utf8 for h in headers})
    return TabularData(
        headers=headers,
        df=df,
        file_path="test.csv",
        encoding_detected="utf-8",
        row_count=len(df),
        format="csv",
    )


class TestRegexCheck:
    def setup_method(self):
        self.v = RegexCheckValidator()

    def test_matching_values_pass(self):
        data = make_data(["email"], [{"email": "a@b.com"}])
        result = self.v.validate("regex_check", data, {"email": r"[^@\s]+@[^@\s]+\.[^@\s]+"})
        assert result.passed

    def test_non_matching_fails(self):
        data = make_data(["email"], [{"email": "not-an-email"}])
        result = self.v.validate("regex_check", data, {"email": r"[^@\s]+@[^@\s]+\.[^@\s]+"})
        assert len(result.errors) == 1

    def test_invalid_regex_pattern(self):
        data = make_data(["x"], [{"x": "abc"}])
        result = self.v.validate("regex_check", data, {"x": "[invalid"})
        assert "Invalid regex" in result.errors[0].message
