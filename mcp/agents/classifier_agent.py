# mcp/agents/classifier_agent.py
import re
from agent_base import Agent
from schemas import AgentContext, InvoiceResult

class ClassifierAgent(Agent):
    name = "classifier"

    def run(self, ctx: AgentContext, result: InvoiceResult) -> InvoiceResult:
        text = ctx.raw_text

        is_table_like = bool(re.search(r"\bQty\b|\bUnit price\b|\bSubtotal\b|\bTax\b", text, re.IGNORECASE))
        has_eur = "€" in text or "EUR" in text
        has_usd = "$" in text or "USD" in text

        # naive language guess
        lang = "fr" if re.search(r"\bFacture\b|\bTVA\b|\bTotal TTC\b", text, re.IGNORECASE) else "en"

        ctx.meta["classification"] = {
            "lang": lang,
            "is_table_like": is_table_like,
            "has_eur": has_eur,
            "has_usd": has_usd,
        }
        result.meta.setdefault("agents_ran", []).append(self.name)
        self.trace(ctx, "classify", summary=f"lang={lang}, table_like={is_table_like}", data=ctx.meta["classification"])
        return result
