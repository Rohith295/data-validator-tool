from typing import Any, ClassVar

from pydantic import RootModel

from data_validator.models import TabularData, ValidationError
from data_validator.validators.base import ValidatorStrategy
from data_validator.validators.registry import ValidatorRegistry


class ColumnsCheckParams(RootModel[list[str]]):
    pass


@ValidatorRegistry.register("columns_check")
class ColumnsCheckValidator(ValidatorStrategy):
    """Checks that the data has exactly the expected columns — no missing, no extra."""

    params_model: ClassVar[type[ColumnsCheckParams]] = ColumnsCheckParams

    @property
    def run_once(self) -> bool:
        return True

    def check(self, data: TabularData, params: Any) -> None:
        columns: list[str] = params
        expected = set(columns)
        actual = set(data.headers)

        for col in sorted(expected - actual):
            self._add_error(ValidationError(message=f"Missing column: '{col}'", column=col))

        for col in sorted(actual - expected):
            self._add_error(ValidationError(message=f"Unexpected column: '{col}'", column=col))
