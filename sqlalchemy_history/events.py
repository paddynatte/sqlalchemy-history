"""SQLAlchemy event handlers for audit tracking."""
from __future__ import annotations

import datetime
from contextvars import ContextVar
from typing import Any

from sqlalchemy import Table, Column, event, inspect, select, func
from sqlalchemy.orm import Session

from sqlalchemy_history.base import history_columns
from sqlalchemy_history.mixins import get_versioned_models


_history_tables: dict[str, Table] = {}

current_user: ContextVar[str | None] = ContextVar("current_user", default=None)


def set_user(user_id: str | None) -> None:
    """Set the current user for audit tracking."""
    current_user.set(user_id)


def get_history_table(tablename: str) -> Table | None:
    """Get history table by name."""
    return _history_tables.get(f"{tablename}_history")


def init_versioning(metadata: Any) -> None:
    """
    Initialize versioning system. Call after models are imported.
    
    Args:
        metadata: SQLAlchemy MetaData instance
    """
    for tablename, model in get_versioned_models().items():
        _create_history_table(model, metadata)


def _create_history_table(model: type, metadata: Any) -> Table:
    """Create a history table for a model."""
    name = f"{model.__tablename__}_history"
    
    if name in _history_tables:
        return _history_tables[name]
    
    exclude = set(getattr(model, "__versioned_exclude__", []))
    
    cols = []
    for col in model.__table__.columns:
        # Skip internal SQLAlchemy columns
        if col.name.startswith("sa_") or col.name.startswith("_sa_"):
            continue
        if col.name in exclude:
            continue
        c = col.copy()
        c.unique = c.primary_key = c.autoincrement = False
        c.nullable = True
        c.default = c.server_default = None
        c.foreign_keys.clear()
        cols.append(c)
    
    cols.extend(history_columns())
    
    table = Table(name, metadata, *cols)
    _history_tables[name] = table
    return table


def _write_history(session: Session, obj: Any, values: dict, operation: str) -> None:
    """Write a history record."""
    table = _history_tables.get(f"{obj.__tablename__}_history")
    if table is None:
        print(f"[versioning] No history table for {obj.__tablename__}")
        return
    
    try:
        version = session.execute(
            select(func.coalesce(func.max(table.c._version), 0) + 1)
            .where(table.c.id == obj.id)
        ).scalar() or 1
        
        values["_version"] = version
        values["_operation"] = operation
        values["_changed_at"] = datetime.datetime.now(datetime.timezone.utc)
        values["_changed_by"] = current_user.get()
        
        session.execute(table.insert().values(**values))
    except Exception as e:
        print(f"[versioning] Error writing history: {e}")
        # Don't re-raise for now - let the main operation succeed


@event.listens_for(Session, "before_flush")
def _before_flush(session: Session, flush_context: Any, instances: Any) -> None:
    """Capture changes before flush."""
    try:
        for obj in session.dirty:
            if not getattr(obj.__class__, "__versioned__", False):
                continue
            if not session.is_modified(obj, include_collections=False):
                continue
            
            exclude = set(getattr(obj.__class__, "__versioned_exclude__", []))
            state = inspect(obj)
            vals = {}
            for col in obj.__table__.columns:
                # Skip internal SQLAlchemy columns
                if col.name.startswith("sa_") or col.name.startswith("_sa_"):
                    continue
                if col.name in exclude:
                    continue
                vals[col.name] = state.committed_state.get(col.name, getattr(obj, col.name, None))
            
            _write_history(session, obj, vals, "UPDATE")
        
        for obj in session.deleted:
            if not getattr(obj.__class__, "__versioned__", False):
                continue
            
            exclude = set(getattr(obj.__class__, "__versioned_exclude__", []))
            vals = {}
            for c in obj.__table__.columns:
                # Skip internal SQLAlchemy columns
                if c.name.startswith("sa_") or c.name.startswith("_sa_"):
                    continue
                if c.name in exclude:
                    continue
                vals[c.name] = getattr(obj, c.name, None)
            _write_history(session, obj, vals, "DELETE")
    except Exception as e:
        import traceback
        print(f"[versioning] ERROR in before_flush: {e}")
        traceback.print_exc()