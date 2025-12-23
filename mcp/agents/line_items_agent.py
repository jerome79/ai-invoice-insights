from __future__ import annotations

from agent_base import Agent
from schemas import AgentContext, InvoiceResult


class LineItemsAgent(Agent):
    """
    Scaffold for later: keep in pipeline but can be disabled by env/config.
    """
    name = "line_items"

    def run(self, ctx: AgentContext, result: InvoiceResult) -> InvoiceResult:
        # No-op for Priority 1 (or implement minimal LLM extraction later)
        result.meta.setdefault("agents_ran", []).append(self.name)
        return result
