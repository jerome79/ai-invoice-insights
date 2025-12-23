from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from schemas import InvoiceRequest
from orchestrator import run_pipeline

app = FastAPI(title="Invoice MCP", version="1.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later for prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health():
    return {"service": "mcp", "status": "ok"}

@app.post("/process")
def process(req: InvoiceRequest):
    return run_pipeline(req.text,include_trace=req.include_trace).model_dump()
