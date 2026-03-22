import json

import pytest

from data_validator.schema import SchemaError, load_schema


class TestLoadSchema:
    def test_valid_schema(self, tmp_path):
        f = tmp_path / "s.json"
        f.write_text(
            json.dumps(
                {
                    "validations": [
                        {"columns_check": {"params": ["name"]}},
                        {"non_empty_check": {"params": ["name"]}},
                    ]
                }
            )
        )
        schema = load_schema(f)
        assert len(schema.validations) == 2

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(SchemaError):
            load_schema(tmp_path / "nope.json")

    def test_malformed_json_raises(self, tmp_path):
        f = tmp_path / "s.json"
        f.write_text("{not valid json!!")
        with pytest.raises(SchemaError):
            load_schema(f)

    def test_unknown_validator_raises(self, tmp_path):
        f = tmp_path / "s.json"
        f.write_text(json.dumps({"validations": [{"bad_check": {"params": ["name"]}}]}))
        with pytest.raises(SchemaError, match="No validator registered"):
            load_schema(f)

    def test_invalid_type_name_raises(self, tmp_path):
        f = tmp_path / "s.json"
        f.write_text(
            json.dumps(
                {
                    "validations": [
                        {"types_check": {"params": {"age": "intger"}}},
                    ]
                }
            )
        )
        with pytest.raises(SchemaError, match="types_check"):
            load_schema(f)

    def test_invalid_regex_pattern_raises(self, tmp_path):
        f = tmp_path / "s.json"
        f.write_text(
            json.dumps(
                {
                    "validations": [
                        {"regex_check": {"params": {"email": "[invalid"}}},
                    ]
                }
            )
        )
        with pytest.raises(SchemaError, match="Invalid regex pattern"):
            load_schema(f)

    def test_invalid_range_key_raises(self, tmp_path):
        f = tmp_path / "s.json"
        f.write_text(
            json.dumps(
                {
                    "validations": [
                        {
                            "range_check": {
                                "params": {
                                    "age": {"min": 0, "maxx": 100},
                                }
                            }
                        },
                    ]
                }
            )
        )
        with pytest.raises(SchemaError, match="age -> maxx"):
            load_schema(f)
