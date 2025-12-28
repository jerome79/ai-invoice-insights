from __future__ import annotations

from typing import Optional, Any, Dict, List
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy import JSON
import uuid

class Run(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    status: str = Field(default="running", index=True)  # running | ok | error
    error_message: Optional[str] = Field(default=None)

    source_filename: Optional[str] = Field(default=None, index=True)

    # denormalized “list view” fields
    vendor: Optional[str] = Field(default=None, index=True)
    invoice_date: Optional[str] = Field(default=None, index=True)
    amount_total: Optional[str] = Field(default=None, index=True)

    # full payloads
    result_json: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=True))
    trace_json: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=True))

