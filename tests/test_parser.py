import pytest

from data_validator.parser import parse
from data_validator.parsers.base import ParseError


class TestParse:
    def test_csv_parsed(self, tmp_path):
        (tmp_path / "data.csv").write_text("name,age\nAlice,30\nBob,25\n")
        result = parse(tmp_path / "data.csv")
        assert result.headers == ["name", "age"]
        assert result.row_count == 2

    def test_json_parsed(self, tmp_path):
        (tmp_path / "data.json").write_text('[{"name":"Alice"},{"name":"Bob"}]')
        assert parse(tmp_path / "data.json").row_count == 2

    def test_empty_file_raises(self, tmp_path):
        (tmp_path / "data.csv").write_text("")
        with pytest.raises(ParseError):
            parse(tmp_path / "data.csv")
