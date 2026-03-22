import polars as pl

from data_validator.models import TabularData
from data_validator.validators.implementations.range import RangeCheckValidator, RangeSpec


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


class TestRangeCheck:
    def setup_method(self):
        self.v = RangeCheckValidator()

    def test_within_range_passes(self):
        data = make_data(["age"], [{"age": "25"}, {"age": "50"}])
        result = self.v.validate("range_check", data, {"age": RangeSpec(min=0, max=100)})
        assert result.passed

    def test_below_minimum(self):
        data = make_data(["age"], [{"age": "-5"}])
        result = self.v.validate("range_check", data, {"age": RangeSpec(min=0, max=100)})
        assert "minimum" in result.errors[0].message

    def test_above_maximum(self):
        data = make_data(["age"], [{"age": "150"}])
        result = self.v.validate("range_check", data, {"age": RangeSpec(min=0, max=100)})
        assert "maximum" in result.errors[0].message

    def test_non_numeric_value(self):
        data = make_data(["age"], [{"age": "abc"}])
        result = self.v.validate("range_check", data, {"age": RangeSpec(min=0, max=100)})
        assert "Cannot parse" in result.errors[0].message
