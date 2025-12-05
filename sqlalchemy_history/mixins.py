"""Mixins for versioned models."""
from __future__ import annotations

from typing import Any, ClassVar


_registry: dict[str, type] = {}


def get_versioned_models() -> dict[str, type]:
    """Get all registered versioned models."""
    return _registry.copy()


class Versioned:
    """
    Mixin to enable audit history tracking on a model.
    
    Usage:
        class Product(Versioned, Base):
            __tablename__ = "products"
            ...
    
    Options:
        __versioned__ = True          # Enable/disable (default: True)
        __versioned_exclude__ = []    # Columns to exclude from history
    """
    
    __versioned__: ClassVar[bool] = True
    __versioned_exclude__: ClassVar[list[str]] = []
    
    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        tablename = getattr(cls, "__tablename__", None)
        if tablename and getattr(cls, "__versioned__", True):
            _registry[tablename] = cls