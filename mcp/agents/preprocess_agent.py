from __future__ import annotations

import re
from agent_base import Agent
from schemas import AgentContext, InvoiceResult


class TextPreprocessAgent(Agent):
    name = "preprocess"

    def run(self, ctx: AgentContext, result: InvoiceResult) -> InvoiceResult:
        text = ctx.raw_text or ""

        # Normalize whitespace and separators
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()

        ctx.cleaned_text = text
        result.meta.setdefault("agents_ran", []).append(self.name)
        self.trace(ctx, "clean text", summary=f"clean raw text", data={"clean text": ctx.cleaned_text,"raw_text": ctx.raw_text})
        return result
