import os
import fitz
import requests
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
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

@app.get("/")
def health():
    return {"service": "api", "status": "ok"}

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
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

    resp.raise_for_status()
    return resp.json()
