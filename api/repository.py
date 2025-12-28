from __future__ import annotations

from typing import Optional, Any, Dict, List
from sqlmodel import select
from sqlmodel import Session
from models import Run
import logging
logger = logging.getLogger("invoice-api")
logging.basicConfig(level=logging.INFO)

def create_run(session: Session, source_filename: Optional[str]) -> Run:
    run = Run(source_filename=source_filename, status="running", result_json={}, trace_json={})
    session.add(run)
    session.commit()
    session.refresh(run)
    return run

def update_run_ok(
    session: Session,
    run: Run,
    result: Dict[str, Any],
    trace: Any,
) -> Run:
    run.status = "ok"
    run.result_json = result or {}
    print(run.result_json)
    run.trace_json = {"trace": trace} if not isinstance(trace, dict) else trace
    logger.info("trace persisted : %s", run.trace_json)
    logger.info("result persisted : %s", run.result_json)

    # best-effort denormalization
    run.vendor = result.get("vendor") if isinstance(result, dict) else None
    run.invoice_date = result.get("invoice_date") if isinstance(result, dict) else None
    run.amount_total = result.get("amount_total") if isinstance(result, dict) else None
    #login
    logger.info("vendor persisted : %s", run.vendor)
    logger.info("invoice_date persisted : %s", run.invoice_date)
    logger.info("amount_total persisted : %s", run.amount_total)

    session.add(run)
    session.commit()
    session.refresh(run)
    return run

def update_run_error(session: Session, run: Run, msg: str) -> Run:
    run.status = "error"
    run.error_message = msg
    session.add(run)
    session.commit()
    session.refresh(run)
    return run

def list_runs(session: Session, limit: int = 50, offset: int = 0) -> List[Run]:
    stmt = select(Run).order_by(Run.created_at.desc()).offset(offset).limit(limit)
    return list(session.exec(stmt).all())

def get_run(session: Session, run_id: str) -> Optional[Run]:
    stmt = select(Run).where(Run.id == run_id)
    return session.exec(stmt).first()
