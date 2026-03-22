import polars as pl

from data_validator.models import TabularData
from data_validator.validators.implementations.unique import UniqueCheckValidator


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


class TestUniqueCheck:
    def setup_method(self):
        self.v = UniqueCheckValidator()

    def test_all_unique_passes(self):
        data = make_data(["id"], [{"id": "1"}, {"id": "2"}, {"id": "3"}])
        result = self.v.validate("unique_check", data, ["id"])
        assert result.passed

    def test_duplicate_detected(self):
        data = make_data(["id"], [{"id": "1"}, {"id": "2"}, {"id": "1"}])
        result = self.v.validate("unique_check", data, ["id"])
        assert len(result.errors) == 1
        assert result.errors[0].row == 3

    def test_multiple_duplicates(self):
        data = make_data(["id"], [{"id": "1"}, {"id": "1"}, {"id": "2"}, {"id": "2"}])
        result = self.v.validate("unique_check", data, ["id"])
        assert len(result.errors) == 2
