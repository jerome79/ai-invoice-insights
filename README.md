# AI Invoice Insights — Multi-Agent MCP (Ollama-ready)

## What this is
A multi-agent invoice intelligence product built with:
- **UI**: static frontend for uploading invoices and reviewing results
- **API service**: accepts PDF uploads, extracts text, calls MCP, persists runs
- **MCP service**: runs a multi-agent pipeline (preprocess → extract → validate → vendor normalize)

## Business problem
Invoices come in many layouts and languages. Rule-based parsers are brittle; black-box AI is hard to trust.
This project focuses on **explainable extraction** (results + warnings + trace), so users can review and correct.

## User journey (current)
1. Upload one invoice or a batch of invoices (PDF)
2. The system processes each invoice independently
3. For each invoice you get:
   - extracted key fields (vendor, invoice_date, amount_total, etc.)
   - warnings / confidence signals
   - an agent trace (for debugging and transparency)
4. Export JSON per invoice, and CSV/JSON for batch results (UI feature)

## Architecture
```
UI → API → MCP (/process) → Orchestrator → Agents → Structured Output (+ Trace)
```

### Services
- **UI**: calls API endpoints
- **API**:
  - `POST /analyze` (single PDF)
  - `POST /analyze/batch` (multiple PDFs in one request)
  - persists each invoice processing as a `Run` in SQLite (SQLModel)
- **MCP**:
  - `POST /process` with `{ "text": "..." }`
  - orchestrates agents and returns a stable schema + trace

## Key product choices (CPTO narrative)
- **Multi-agent over monolith**: enables incremental improvement per capability (preprocess/extract/validate/vendor).
- **MCP orchestration**: keeps routing and traceability explicit and testable.
- **Explainability first**: invoices are financial documents; partial extraction must be visible.
- **Batch processing for beta**: real users process sets of invoices, not one-by-one.

## Endpoints

### API
- Health: `GET http://localhost:8080/`
- Swagger: `http://localhost:8080/docs`

#### Single
- `POST http://localhost:8080/analyze`
  - `multipart/form-data`
  - field: `file` (PDF)

#### Batch
- `POST http://localhost:8080/analyze/batch`
  - `multipart/form-data`
  - field: `files` (repeat for multiple PDFs)
  - returns one result per invoice (and a `run_id` per invoice)

### MCP
- Health: `GET http://localhost:8000/`
- Swagger: `http://localhost:8000/docs`
- `POST http://localhost:8000/process`
  - JSON: `{ "text": "..." }`

## Local run (no Docker)
Install deps:
- `pip install -r api/requirements.txt`
- `pip install -r mcp/requirements.txt`

Run:
- `make run-mcp`
- `make run-api`

## Docker run
Start everything:
- `make dev`

Services:
- UI: http://localhost:5500
- API: http://localhost:8080/docs
- MCP: http://localhost:8000/docs

## Ollama setup (optional)
Install and run Ollama locally, then pull a model:
- `ollama pull llama3.2`

`.env.dev` typically uses:
- `LLM_BACKEND=ollama`
- `OLLAMA_URL=http://host.docker.internal:11434`
- `OLLAMA_MODEL=llama3.2:latest`

To run without LLM:
- set `LLM_BACKEND=none`

## Roadmap (high level)
**Now**
- Batch processing + UX feedback loop (private beta)
- Improve error messages, confidence display, trace readability

**Next**
- Classifier + Router (multi-agent routing story)
- Eval reports and regression tests on a growing invoice set

**Later**
- Auth, workspace management, integrations (Drive/Email/Accounting tools)
