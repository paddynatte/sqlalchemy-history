# sqlalchemy-history

Lightweight async-compatible history for SQLAlchemy 2.0+

## Installation

uv add git+https://github.com/paddynatte/sqlalchemy-history.git

from sqlalchemy_history import Versioned, init_versioning

class Product(Versioned, Base):
    __tablename__ = "products"
    ...

# At startup
init_versioning(Base.metadata)## License

MIT
