"""Base definitions for history tables."""
from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

if TYPE_CHECKING:
    from sqlalchemy import Table


def history_columns() -> list[Column]:
    """
    Standard columns added to every history table.
    
    - _history_id: Primary key for history record
    - _version: Version number of this snapshot
    - _operation: "UPDATE" or "DELETE"
    - _changed_at: When the change occurred
    - _changed_by: Who made the change (optional, set via context)
    """
    return [
        Column("_history_id", Integer, primary_key=True, autoincrement=True),
        Column("_version", Integer, nullable=False, index=True),
        Column("_operation", String(10), nullable=False),
        Column("_changed_at", DateTime(timezone=True), nullable=False, 
               default=lambda: datetime.datetime.now(datetime.timezone.utc)),
        Column("_changed_by", String(255), nullable=True),
    ]