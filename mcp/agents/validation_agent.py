from __future__ import annotations

from agent_base import Agent
from schemas import AgentContext, InvoiceResult


class ValidationAgent(Agent):
    name = "validate"

    def run(self, ctx: AgentContext, result: InvoiceResult) -> InvoiceResult:
        warnings = result.warnings

        # totals sanity
        if result.amount_total <= 0:
            warnings.append("MISSING_AMOUNT_TOTAL")
            result.confidence["amount_total"] = min(result.confidence.get("amount_total", 0.2), 0.2)
        else:
            # If subtotal+tax approximates total, boost confidence
            if result.subtotal > 0 and result.amount_tax >= 0:
                approx = result.subtotal + result.amount_tax
                if approx == 0:
                    pass
                else:
                    rel_err = abs(approx - result.amount_total) / max(result.amount_total, 1e-6)
                    if rel_err < 0.02:
                        result.confidence["amount_total"] = max(result.confidence.get("amount_total", 0.7), 0.9)
                    elif rel_err < 0.1:
                        warnings.append("TOTAL_MAY_NOT_MATCH_SUBTOTAL_TAX")
                        result.confidence["amount_total"] = max(result.confidence.get("amount_total", 0.7), 0.7)
                    else:
                        warnings.append("TOTAL_MISMATCH_SUBTOTAL_TAX")
                        result.confidence["amount_total"] = min(result.confidence.get("amount_total", 0.7), 0.5)

        # vendor sanity
        if not result.vendor:
            warnings.append("MISSING_VENDOR")
            result.confidence["vendor"] = min(result.confidence.get("vendor", 0.2), 0.2)
        else:
            result.confidence["vendor"] = max(result.confidence.get("vendor", 0.7), 0.85)

        # date sanity
        if not result.invoice_date:
            warnings.append("MISSING_INVOICE_DATE")

        result.meta.setdefault("agents_ran", []).append(self.name)
        self.trace(ctx, "validation of the result",
                   summary=f"extract vendor={result.vendor}, amount_total={result.amount_total}, tax amount={result.amount_tax}",
                   data={"confidence vendor": result.confidence["vendor"],
                         "confidence total amount": result.confidence["amount_total"]})
        return result
