# mcp/orchestrator.py
from schemas import AgentContext, InvoiceResult

from agents.classifier_agent import ClassifierAgent
from agents.router_agent import RouterAgent

from agents.vendor_agent import VendorAgent
from agents.preprocess_agent import TextPreprocessAgent
from agents.invoice_extraction_agent import InvoiceExtractionAgent
from agents.validation_agent import ValidationAgent
from agents.line_items_agent import LineItemsAgent

AGENTS = {
    "preprocess": TextPreprocessAgent(),
    "classifier": ClassifierAgent(),
    "router": RouterAgent(),
    "vendor": VendorAgent(),
    "invoice_extraction": InvoiceExtractionAgent(),
    "line_items": LineItemsAgent(),
    "validation": ValidationAgent(),
}

def run_pipeline(text: str, include_trace: bool = True) -> InvoiceResult:
    ctx = AgentContext(raw_text=text)
    res = InvoiceResult()

    # Always preprocess + classify + route first
    for key in ["preprocess", "classifier", "router"]:
        res = AGENTS[key].run(ctx, res)

    pipeline = ctx.meta.get("pipeline", ["vendor", "invoice_extraction", "validation"])

    for key in pipeline:
        res = AGENTS[key].run(ctx, res)

    # attach trace
    if include_trace:
        res.trace = ctx.trace
    else:
        res.trace = []

    return res
