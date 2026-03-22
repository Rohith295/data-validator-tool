from collections.abc import Callable
from typing import ClassVar

from data_validator.parsers.base import ParseError, ParserStrategy


class ParserRegistry:
    """Maps file extensions (e.g. ".csv") to their ParserStrategy classes."""

    _parsers: ClassVar[dict[str, type[ParserStrategy]]] = {}

    @classmethod
    def register(
        cls,
        *extensions: str,
    ) -> Callable[[type[ParserStrategy]], type[ParserStrategy]]:
        def decorator(
            parser_cls: type[ParserStrategy],
        ) -> type[ParserStrategy]:
            for ext in extensions:
                cls._parsers[ext] = parser_cls
            parser_cls.extensions = list(extensions)
            return parser_cls

        return decorator

    @classmethod
    def get(cls, extension: str) -> ParserStrategy:
        ext = extension.lower()
        if ext not in cls._parsers:
            supported = ", ".join(sorted(cls._parsers))
            raise ParseError(f"Unsupported file format: {ext}. Supported: {supported}")
        return cls._parsers[ext]()
