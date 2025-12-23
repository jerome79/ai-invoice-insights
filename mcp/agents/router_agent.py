# mcp/agents/router_agent.py
from agent_base import Agent
from schemas import AgentContext, InvoiceResult

class RouterAgent(Agent):
    name = "router"

    def run(self, ctx: AgentContext, result: InvoiceResult) -> InvoiceResult:
        c = ctx.meta.get("classification", {})
        pipeline = ["vendor", "invoice_extraction", "validation"]

        # enable line items only if table-like
        if c.get("is_table_like"):
            pipeline.insert(2, "line_items")

        ctx.meta["pipeline"] = pipeline
        result.meta.setdefault("agents_ran", []).append(self.name)
        self.trace(ctx, "route", summary=f"pipeline={pipeline}", data={"pipeline": pipeline})
        return result
