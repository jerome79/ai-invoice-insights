# AI Invoice Insights — Multi-Agent MCP (Ollama-ready)

## What this is
A multi-agent invoice intelligence backend built with:
- **API service**: accepts PDF upload, extracts text, calls MCP
- **MCP service**: runs a **multi-agent pipeline** (preprocess → extract → validate → vendor normalize)
- **UI**: simple static frontend calling the API

## Architecture (Priority 1)
UI → API → MCP (/process) → Orchestrator → Agents
- TextPreprocessAgent
- InvoiceExtractionAgent (LLM-first, with regex fallback)
- ValidationAgent (warnings + confidence)
- VendorAgent (normalization; optional LLM)

## Endpoints
- API: `POST http://localhost:8080/analyze` (multipart form-data file=PDF)
- MCP: `POST http://localhost:8000/process` (json: {"text": "..."})
- Health:
  - API: `GET http://localhost:8080/`
  - MCP: `GET http://localhost:8000/`

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

## Ollama setup
Install and run Ollama locally, then pull a model:
- `ollama pull llama3.2`

`.env.dev` uses:
- `LLM_BACKEND=ollama`
- `OLLAMA_URL=http://host.docker.internal:11434`
- `OLLAMA_MODEL=llama3.2:latest`

To run without LLM:
- set `LLM_BACKEND=none` in `.env.dev`

## Output format
MCP returns a stable schema with:
- extracted fields
- confidence per field
- warnings
- meta.agents_ran
