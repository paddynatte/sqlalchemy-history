# sqlalchemy-history

Lightweight async-compatible audit history for SQLAlchemy 2.0+

## Installation

pip install sqlalchemy-history## Usage

from sqlalchemy_history import Versioned, init_versioning

class Product(Versioned, Base):
    __tablename__ = "products"
    ...

# At startup
init_versioning(Base.metadata)## License

MIT