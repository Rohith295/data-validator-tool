import polars as pl

from data_validator.models import TabularData
from data_validator.validators.implementations.non_empty import NonEmptyCheckValidator


def make_data(headers, rows):
    if rows:
        df = pl.DataFrame(rows, schema={h: pl.Utf8 for h in headers})
    else:
        df = pl.DataFrame({h: [] for h in headers}).cast(pl.Utf8)
    return TabularData(
        headers=headers,
        df=df,
        file_path="test.csv",
        encoding_detected="utf-8",
        row_count=len(df),
        format="csv",
    )


class TestNonEmptyCheck:
    def setup_method(self):
        self.v = NonEmptyCheckValidator()

    def test_all_filled_passes(self):
        data = make_data(["name"], [{"name": "Alice"}])
        result = self.v.validate("non_empty_check", data, ["name"])
        assert result.passed

    def test_blank_value_caught(self):
        data = make_data(["name"], [{"name": ""}])
        result = self.v.validate("non_empty_check", data, ["name"])
        assert len(result.errors) == 1
        assert result.errors[0].row == 1

    def test_whitespace_only_caught(self):
        data = make_data(["name"], [{"name": "   "}])
        result = self.v.validate("non_empty_check", data, ["name"])
        assert len(result.errors) == 1

    def test_null_value_caught(self):
        data = make_data(["name"], [{"name": None}])
        result = self.v.validate("non_empty_check", data, ["name"])
        assert len(result.errors) == 1

    def test_entirely_blank_row_caught(self):
        data = make_data(
            ["id", "name"],
            [
                {"id": "1", "name": "Alice"},
                {"id": "", "name": ""},
                {"id": "3", "name": "Bob"},
            ],
        )
        result = self.v.validate("non_empty_check", data, ["id", "name"])
        assert len(result.errors) == 2
        assert all(e.row == 2 for e in result.errors)
