import os
import fitz
import requests
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from sqlmodel import Session

from db import init_db, get_session
from repository import create_run, update_run_ok, update_run_error, list_runs, get_run

import logging
logger = logging.getLogger("invoice-api")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Invoice API", version="1.0")

MCP_URL = os.getenv("MCP_URL", "http://mcp:8000/process")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN] if FRONTEND_ORIGIN != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    return "\n".join(page.get_text() for page in doc)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def health():
    return {"service": "api", "status": "ok"}

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    session = get_session()
    run = create_run(session, source_filename=file.filename)
    try:
        pdf_bytes = await file.read()
        text = extract_text_from_pdf(pdf_bytes)

        ##log the extracted text length
        logger.info("Received file: %s (%s)", file.filename, file.content_type)
        logger.info("Extracted text length: %s", len(text))
        logger.info("Calling MCP_URL=%s", MCP_URL)

        resp = requests.post(MCP_URL, json={"text": text}, timeout=120)

        ##log status code
        logger.info("MCP status=%s", resp.status_code)
        logger.info("MCP response preview=%s", resp.text[:200])
        data = resp.json()
        trace = data.get("trace", [])
        data = resp.json()
        # extract trace (default to empty list) and build result as data without the 'trace' key
        trace = []
        if isinstance(data, dict):
            trace = data.get("trace", [])
            result = {k: v for k, v in data.items() if k != "trace"}
        else:
            result = data

        logger.info("start persistence with status : %s", resp.status_code)
        run = update_run_ok(session, run, result=result, trace=trace)
        return {"run_id": run.id, "result": run.result_json, "trace": run.trace_json}

    except Exception as e:
        update_run_error(session, run, str(e))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@app.get("/runs")
def runs(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    session = get_session()
    try:
        items = list_runs(session, limit=limit, offset=offset)
        # keep payload light for list view
        return [
            {
                "id": r.id,
                "created_at": r.created_at.isoformat(),
                "status": r.status,
                "source_filename": r.source_filename,
                "vendor": r.vendor,
                "invoice_date": r.invoice_date,
                "amount_total": r.amount_total,
            }
            for r in items
        ]
    finally:
        session.close()



@app.get("/runs/{run_id}")
def run_details(run_id: str):
    session = get_session()
    try:
        r = get_run(session, run_id)
        if not r:
            raise HTTPException(status_code=404, detail="Run not found")
        return {
            "id": r.id,
            "created_at": r.created_at.isoformat(),
            "status": r.status,
            "error_message": r.error_message,
            "source_filename": r.source_filename,
            "result": r.result_json,
            "trace": r.trace_json,
        }
    finally:
        session.close()