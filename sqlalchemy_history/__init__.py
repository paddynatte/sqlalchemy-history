"""
sqlalchemy-audit - Lightweight async-compatible audit history for SQLAlchemy 2.0+

Usage:
    from sqlalchemy_history import Versioned, init_versioning
    
    class Product(Versioned, Base):
        __tablename__ = "products"
        ...
    
    init_versioning(Base.metadata)
"""
from sqlalchemy_history.__metadata__ import __version__
from sqlalchemy_history.mixins import Versioned
from sqlalchemy_history.events import init_versioning

__all__ = (
    "__version__",
    "Versioned",
    "init_versioning",
)