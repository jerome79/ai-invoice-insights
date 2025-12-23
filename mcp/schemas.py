from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TraceEvent(BaseModel):
    agent: str
    action: str
    status: str = "ok"  # ok|skip|warn|error
    summary: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class InvoiceRequest(BaseModel):
    text: str = Field(..., description="Raw invoice text extracted from PDF or OCR.")
    include_trace: bool = True


class InvoiceResult(BaseModel):
    # Core fields
    vendor: str = ""
    invoice_number: str = ""
    invoice_date: str = ""   # ISO preferred: YYYY-MM-DD
    due_date: str = ""     # ISO preferred: YYYY-MM-DD
    currency: str = ""
    subtotal: float = 0.0
    amount_tax: float = 0.0
    amount_total: float = 0.0

    # Optional
    line_items: List[Dict[str, Any]] = Field(default_factory=list)

    # Trust layer
    confidence: Dict[str, float] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)

    # Metadata
    meta: Dict[str, Any] = Field(default_factory=dict)

    #trace
    trace: List[TraceEvent] = Field(default_factory=list)


class AgentContext(BaseModel):
    """
    Shared context passed to agents.
    """
    raw_text: str
    cleaned_text: str = ""
    env: str = "dev"

    llm_backend: str = "none"
    llm_model: str = ""
    debug: bool = False

    # can store intermediate stuff (like token counts later)
    scratch: Dict[str, Any] = Field(default_factory=dict)

    # Metadata
    meta: Dict[str, Any] = Field(default_factory=dict)

    #trace
    trace: List[TraceEvent] = Field(default_factory=list)
