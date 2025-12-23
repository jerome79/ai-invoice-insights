from __future__ import annotations

from abc import ABC, abstractmethod
from schemas import AgentContext, InvoiceResult, TraceEvent


class Agent(ABC):
    """
    Simple agent interface: agents read context and update the shared result.
    """

    name: str

    def trace(self, ctx: AgentContext, action: str, summary: str = None, status: str = "ok", data=None):
        ctx.trace.append(
            TraceEvent(agent=self.name, action=action, status=status, summary=summary, data=data or {})
        )

    @abstractmethod
    def run(self, ctx: AgentContext, result: InvoiceResult) -> InvoiceResult:
        raise NotImplementedError
