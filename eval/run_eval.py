# eval/run_eval.py
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

import sys
import os
sys.path.insert(0, "mcp")
os.environ.setdefault("LLM_BACKEND", "ollama")
os.environ.setdefault("OLLAMA_MODEL", "gemma3:1b")

from orchestrator import run_pipeline


EVAL_DIR = Path("data/eval")
REPORTS_DIR = Path("reports")

FIELDS = ["vendor", "invoice_date", "amount_total","currency"]

def norm(s: str) -> str:
    if s is None:
        return ""
    if isinstance(s, float):
        s = f"{s:.2f}"
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s

def score_one(pred: Dict[str, Any], gold: Dict[str, Any]) -> Dict[str, Any]:
    per_field = {}
    correct = 0
    for f in FIELDS:
        p = norm(pred.get(f))
        g = norm(gold.get(f))
        ok = (p == g) and g != ""
        per_field[f] = {"pred": pred.get(f), "gold": gold.get(f), "ok": ok}
        if ok:
            correct += 1
    return {
        "fields": per_field,
        "field_accuracy": correct / len(FIELDS),
    }

def main():
    REPORTS_DIR.mkdir(exist_ok=True)

    items = sorted(EVAL_DIR.glob("*.txt"))
    print(f"nb of elements : {len(items)}")
    results = []
    totals = {f: 0 for f in FIELDS}
    n = 0

    for txt_path in items:
        base = txt_path.stem
        expected_path = EVAL_DIR / f"{base}.expected.json"
        if not expected_path.exists():
            continue

        text = txt_path.read_text(encoding="utf-8")
        gold = json.loads(expected_path.read_text(encoding="utf-8"))
        out = run_pipeline(text, include_trace=True).model_dump()

        pred = {k: out.get(k) for k in FIELDS}

        scored = score_one(pred, gold)
        n += 1
        for f in FIELDS:
            if scored["fields"][f]["ok"]:
                totals[f] += 1

        results.append({
            "id": base,
            "score": scored["field_accuracy"],
            "details": scored["fields"],
            "trace": out.get("trace", [])  # super helpful for debugging
        })


    summary = {
        "count": n,
        "per_field_accuracy": {f: (totals[f] / n if n else 0.0) for f in FIELDS},
        "avg_field_accuracy": (sum(r["score"] for r in results) / n if n else 0.0),
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }

    report = {"summary": summary, "results": results}

    fname = REPORTS_DIR / f"eval_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    fname.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"✅ Wrote report: {fname}")

if __name__ == "__main__":
    main()
