import polars as pl

from data_validator.models import TabularData
from data_validator.validators.implementations.types import TypesCheckValidator


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


class TestTypesCheck:
    def setup_method(self):
        self.v = TypesCheckValidator()

    def test_correct_types_pass(self):
        data = make_data(["age", "name"], [{"age": "30", "name": "Alice"}])
        result = self.v.validate("types_check", data, {"age": "integer", "name": "string"})
        assert result.passed

    def test_text_in_integer_column(self):
        data = make_data(["age"], [{"age": "thirty"}])
        result = self.v.validate("types_check", data, {"age": "integer"})
        assert len(result.errors) == 1

    def test_float_in_integer_column_fails(self):
        data = make_data(["age"], [{"age": "30.5"}])
        result = self.v.validate("types_check", data, {"age": "integer"})
        assert len(result.errors) == 1

    def test_bool_true_false_passes(self):
        data = make_data(["active"], [{"active": "true"}, {"active": "false"}])
        result = self.v.validate("types_check", data, {"active": "bool"})
        assert result.passed
