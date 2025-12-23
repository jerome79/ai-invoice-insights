from __future__ import annotations

import re
from datetime import datetime
from agent_base import Agent
from schemas import AgentContext, InvoiceResult
from llm.gateway import generate_json, llm_backend, llm_model


def _try_parse_money(s: str) -> float:
    s = (s or "").strip()
    s = s.replace(",", ".")
    s = re.sub(r"[^0-9.]", "", s)
    try:
        return float(s) if s else 0.0
    except Exception:
        return 0.0


def _regex_fallback(text: str) -> dict:
    # Very light fallback (better than empty)
    vendor = ""
    first_line = (text.splitlines()[0].strip() if text else "")
    vendor = first_line[:80] if first_line else ""

    total = 0.0
    m_total = re.search(r"(Amount due|Total)\s*[:\n ]*\$?€?\s*([0-9][0-9\.,]*)", text, re.IGNORECASE)
    if m_total:
        total = _try_parse_money(m_total.group(2))

    # Date: tries “July 6, 2025” or “06/07/2025”
    issue_date = ""
    m_date = re.search(r"(Date of issue|Date)\s*[:\n ]*([A-Za-z]+\s+\d{1,2},\s+\d{4})", text, re.IGNORECASE)
    if m_date:
        issue_date = m_date.group(2).strip()

    return {
        "vendor": vendor,
        "invoice_date": issue_date,
        "amount_total": total
    }


def _normalize_date_to_iso(value: str) -> str:
    v = (value or "").strip()
    if not v:
        return ""
    # already ISO?
    if re.match(r"^\d{4}-\d{2}-\d{2}$", v):
        return v
    # Try common formats
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(v, fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    return v  # keep raw if cannot parse


class InvoiceExtractionAgent(Agent):
    name = "extract"

    def run(self, ctx: AgentContext, result: InvoiceResult) -> InvoiceResult:
        text = ctx.cleaned_text or ctx.raw_text or ""
        fallback = _regex_fallback(text)

        # LLM prompt
        prompt = f"""
You are an expert accounting assistant.
Extract invoice fields from the text below.

Return ONLY a valid JSON object with this schema:
{{
  "vendor": "",
  "invoice_number": "",
  "invoice_date": "",
  "due_date": "",
  "currency": "",
  "subtotal": 0.0,
  "amount_tax": 0.0,
  "amount_total": 0.0
}}

Rules:
- Dates should be output as YYYY-MM-DD when possible.
- If a field is not found, return an empty string or 0.00.
- if an amount is using , as decimal separator, convert it to . and 2 decimal places
- Use standard 3 letters currency codes (e.g., USD, EUR, GBP, JPY, ZAR).
- Convert amounts to float numbers.
- Convert currency symbols to currency codes
- Do not include any extra keys. Do not include explanations.

Invoice text:
{text}
""".strip()

        data = generate_json(prompt) or {}

        # Merge LLM → result with fallback
        result.vendor = data.get("vendor") or result.vendor or fallback.get("vendor", "")
        result.invoice_number = data.get("invoice_number") or result.invoice_number
        result.invoice_date = _normalize_date_to_iso(data.get("invoice_date") or result.issue_date or fallback.get("invoice_date", ""))
        result.due_date = _normalize_date_to_iso(data.get("due_date") or result.due_date)
        result.currency = data.get("currency") or result.currency

        # numeric
        result.subtotal = float(data.get("subtotal") or result.subtotal or 0.0)
        result.amount_tax = float(data.get("amount_tax") or result.amount_tax or 0.0)
        result.amount_total = float(data.get("amount_total") or result.amount_total or fallback.get("amount_total", 0.0))

        # initial confidence (very rough; refined by ValidationAgent)
        result.confidence.setdefault("vendor", 0.7 if result.vendor else 0.2)
        result.confidence.setdefault("amount_total", 0.7 if result.amount_total else 0.2)

        result.meta.setdefault("llm_backend", llm_backend())
        result.meta.setdefault("llm_model", llm_model())
        result.meta.setdefault("agents_ran", []).append(self.name)
        self.trace(ctx, "invoice extraction", summary=f"extract vendor={result.vendor}, amount_total={result.amount_total}",
                   data={"LLM extraction":data,
                         "fall back":fallback})
        return result
