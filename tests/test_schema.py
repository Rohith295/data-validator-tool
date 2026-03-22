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
