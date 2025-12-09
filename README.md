# AI Invoice Insights — MCP-Powered Micro-SaaS
Instantly extract invoice insights with a lightweight MCP server and a FastAPI wrapper.
No LLM required for the MVP.

## Features
- Extract vendor, amount, dates, VAT
- Simple anomaly engine
- PDF → Text extraction (PyMuPDF)
- MCP server with modular tools
- FastAPI endpoint for easy integration
- Optional LLM extension
- Dockerized & deployable on OVH

## Tech Stack
- Python 3.11
- FastAPI
- PyMuPDF
- MCP Tools (custom)
- Docker

## Run Locally
docker-compose up --build


## API Usage
POST /analyze
file: PDF

## Output
{
"vendor": "ACME Corp",
"invoice_date": "2024-05-10",
"due_date": "2024-06-10",
"amount_total": "392.50",
"vat_rate": "20%",
"anomalies": ["Missing invoice number"]
}


## Upgrade Paths
- Add LLM extraction (GPT, Mistral, Llama)
- Add duplicate invoice detection
- Add subscription recognition
- Add expense categorization

