import pytest

from data_validator import validate, validate_file


class TestValidateAPI:
    def test_pass_and_fail(self):
        data = [{"id": "1", "name": "alice"}, {"id": "2", "name": ""}]
        report = validate(
            data,
            [
                {"columns_check": {"params": ["id", "name"]}},
                {"non_empty_check": {"params": ["name"]}},
                {"types_check": {"params": {"id": "string"}}},
            ],
        )
        assert report.overall_passed is False
        assert len(report.results) == 3
        assert report.results[0].passed is True
        assert report.results[1].passed is False

    def test_validate_file_csv(self, tmp_path):
        (tmp_path / "data.csv").write_text("id,name\n1,alice\n")
        (tmp_path / "s.json").write_text(
            '{"validations":[{"columns_check":{"params":["id","name"]}}]}'
        )
        assert validate_file(tmp_path / "data.csv", tmp_path / "s.json").overall_passed is True

    def test_invalid_check_raises(self):
        with pytest.raises(ValueError):
            validate([{"id": "1"}], [{"bad_check": {"params": ["id"]}}])
