from __future__ import annotations

import re
from agent_base import Agent
from schemas import AgentContext, InvoiceResult
from llm.gateway import generate_json, llm_enabled,llm_backend


class VendorAgent(Agent):
    name = "vendor"

    def run(self, ctx: AgentContext, result: InvoiceResult) -> InvoiceResult:

        if not result.vendor or result.vendor!="":
            result.meta.setdefault("agents_ran", []).append(self.name)
            self.trace(ctx, "vendor normalization", summary=f"vendor={result.vendor}",
                       data={"confidence": None, "llm_enabled": False,
                             "llm_backend": None,"vendor empty": True})
            return result

        # quick normalization
        v = result.vendor.strip()
        v = re.sub(r"\s{2,}", " ", v)

        # optional LLM normalization (safe, but can be disabled)
        if llm_enabled():
            prompt = f"""
Normalize the vendor name into a canonical company name.
Return ONLY JSON: {{"vendor_canonical": ""}}
Input vendor: "{v}"
""".strip()
            data = generate_json(prompt) or {}
            v2 = (data.get("vendor_canonical") or "").strip()
            if v2:
                v = v2

        result.vendor = v
        result.confidence["vendor"] = max(result.confidence.get("vendor", 0.7), 0.9)

        result.meta.setdefault("agents_ran", []).append(self.name)
        self.trace(ctx, "vendor normalization", summary=f"vendor={result.vendor}", data={"confidence" : result.confidence["vendor"],"llm_enabled":llm_enabled(),"llm_backend":llm_backend()})
        return result
