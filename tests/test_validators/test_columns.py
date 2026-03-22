import polars as pl

from data_validator.models import TabularData
from data_validator.validators.implementations.columns import ColumnsCheckValidator


def make_data(headers):
    df = pl.DataFrame({h: [] for h in headers}).cast(pl.Utf8)
    return TabularData(
        headers=headers,
        df=df,
        file_path="test.csv",
        encoding_detected="utf-8",
        row_count=0,
        format="csv",
    )


class TestColumnsCheck:
    def setup_method(self):
        self.v = ColumnsCheckValidator()

    def test_exact_match_passes(self):
        result = self.v.validate("columns_check", make_data(["name", "age"]), ["name", "age"])
        assert result.passed

    def test_missing_column(self):
        result = self.v.validate("columns_check", make_data(["name"]), ["name", "age"])
        assert len(result.errors) == 1
        assert "Missing" in result.errors[0].message

    def test_unexpected_column(self):
        result = self.v.validate(
            "columns_check", make_data(["name", "age", "dept"]), ["name", "age"]
        )
        assert len(result.errors) == 1
        assert "Unexpected" in result.errors[0].message
