import os
import uuid
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import fitz
import requests
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from db import init_db, get_session
from repository import (
    create_run,
    update_run_ok,
    update_run_error,
    list_runs,
    get_run,
)

logger = logging.getLogger("invoice-api")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Invoice API", version="1.1")

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


def call_mcp(text: str, timeout_s: int = 120) -> Dict[str, Any]:
    """
    Calls the MCP server with extracted text and returns parsed JSON.
    Raises an exception with helpful context if MCP is unreachable or returns invalid JSON.
    """
    logger.info("Calling MCP_URL=%s", MCP_URL)
    resp = requests.post(MCP_URL, json={"text": text}, timeout=timeout_s)

    logger.info("MCP status=%s", resp.status_code)
    preview = (resp.text or "")[:400]
    logger.info("MCP response preview=%s", preview)

    if resp.status_code >= 400:
        # Preserve MCP error body for debugging
        raise RuntimeError(f"MCP error {resp.status_code}: {preview}")

    try:
        return resp.json()
    except Exception as e:
        raise RuntimeError(f"MCP returned non-JSON response: {preview}") from e


def split_result_and_trace(mcp_payload: Any) -> tuple[Any, Any]:
    """
    If MCP returns {"trace": [...], ...fields...} => separate trace and result.
    Otherwise just return the payload as result with empty trace.
    """
    if isinstance(mcp_payload, dict):
        trace = mcp_payload.get("trace", [])
        result = {k: v for k, v in mcp_payload.items() if k != "trace"}
        return result, trace
    return mcp_payload, []


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def health():
    return {"service": "api", "status": "ok", "time": datetime.utcnow().isoformat()}


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    session = get_session()
    run = create_run(session, source_filename=file.filename)

    try:
        pdf_bytes = await file.read()
        text = extract_text_from_pdf(pdf_bytes)

        logger.info("Received file: %s (%s)", file.filename, file.content_type)
        logger.info("Extracted text length: %s", len(text))

        mcp_payload = call_mcp(text)
        result, trace = split_result_and_trace(mcp_payload)

        run = update_run_ok(session, run, result=result if isinstance(result, dict) else {"result": result}, trace=trace)

        return {
            "run_id": run.id,
            "status": run.status,
            "result": run.result_json,
            "trace": run.trace_json,
        }

    except Exception as e:
        update_run_error(session, run, str(e))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@app.post("/analyze/batch")
async def analyze_batch(files: List[UploadFile] = File(...)):
    """
    Upload multiple PDFs and process them invoice-by-invoice.
    IMPORTANT: Batch never fails entirely because of one invoice.
    """
    batch_id = f"b_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    session = get_session()
    results: List[Dict[str, Any]] = []
    ok = warn = err = 0

    try:
        for f in files:
            run = create_run(session, source_filename=f.filename)
            item: Dict[str, Any] = {
                "run_id": run.id,
                "filename": f.filename,
                "status": "running",
                "result": None,
                "trace": None,
                "error": None,
            }

            try:
                pdf_bytes = await f.read()
                text = extract_text_from_pdf(pdf_bytes)

                mcp_payload = call_mcp(text)
                result, trace = split_result_and_trace(mcp_payload)

                # Persist
                run = update_run_ok(
                    session,
                    run,
                    result=result if isinstance(result, dict) else {"result": result},
                    trace=trace,
                )

                item["status"] = "ok"
                item["result"] = run.result_json
                item["trace"] = run.trace_json

                # Simple warning heuristic (optional): if MCP/validator provides warnings, expose them
                warnings = None
                if isinstance(item["result"], dict):
                    warnings = item["result"].get("warnings") or item["result"].get("validation_warnings")
                if warnings:
                    item["status"] = "warning"
                    warn += 1
                else:
                    ok += 1

            except Exception as e:
                update_run_error(session, run, str(e))
                item["status"] = "error"
                item["error"] = {"message": str(e)}
                err += 1

            results.append(item)

        return {
            "batch_id": batch_id,
            "created_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_files": len(files),
                "ok": ok,
                "warning": warn,
                "error": err,
            },
            "results": results,
        }

    finally:
        session.close()


@app.get("/runs")
def runs(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    session = get_session()
    try:
        items = list_runs(session, limit=limit, offset=offset)
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
