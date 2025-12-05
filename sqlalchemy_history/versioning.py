from __future__ import annotations
import datetime
from typing import Any, ClassVar
from sqlalchemy import Table, Column, Integer, String, event, inspect, select, func
from sqlalchemy.orm import Session
from advanced_alchemy.types import DateTimeUTC

_models: dict[str, type] = {}
_tables: dict[str, Table] = {}


class Versioned:
    __versioned__: ClassVar[bool] = True
    
    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "__tablename__") and cls.__versioned__:
            _models[cls.__tablename__] = cls


def init_versioning(metadata: Any) -> None:
    for name, model in _models.items():
        cols = [col.copy() for col in model.__table__.columns]
        for c in cols:
            c.unique = c.primary_key = c.autoincrement = False
            c.nullable = True
            c.default = c.server_default = None
            c.foreign_keys.clear()
        cols += [
            Column("_history_id", Integer, primary_key=True, autoincrement=True),
            Column("_version", Integer, nullable=False),
            Column("_operation", String(10), nullable=False),
            Column("_changed_at", DateTimeUTC(timezone=True), nullable=False),
        ]
        _tables[name] = Table(f"{name}_history", metadata, *cols)


@event.listens_for(Session, "before_flush")
def _flush(session: Session, *_: Any) -> None:
    for obj in session.dirty:
        if not getattr(obj.__class__, "__versioned__", False):
            continue
        if not session.is_modified(obj, include_collections=False):
            continue
        state = inspect(obj)
        vals = {c.name: state.committed_state.get(c.name, getattr(obj, c.name)) for c in obj.__table__.columns}
        _write(session, obj, vals, "UPDATE")
    
    for obj in session.deleted:
        if not getattr(obj.__class__, "__versioned__", False):
            continue
        vals = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
        _write(session, obj, vals, "DELETE")


def _write(session: Session, obj: Any, vals: dict, op: str) -> None:
    t = _tables.get(obj.__tablename__)
    if not t:
        return
    v = session.execute(select(func.coalesce(func.max(t.c._version), 0) + 1).where(t.c.id == obj.id)).scalar()
    vals.update(_version=v, _operation=op, _changed_at=datetime.datetime.now(datetime.timezone.utc))
    session.execute(t.insert().values(**vals))