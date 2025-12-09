import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import re

load_dotenv()

ENV = os.getenv("ENV", "development")
API_ORIGIN = os.getenv("API_ORIGIN", "http://localhost:8080")

app = FastAPI(
    docs_url="/docs" if ENV == "development" else None,
    redoc_url="/redoc" if ENV == "development" else None,
    openapi_url="/openapi.json" if ENV == "development" else None,
)

# 🔐 allow only the API to call the MCP
app.add_middleware(
    CORSMiddleware,
    allow_origins=[API_ORIGIN],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InvoiceRequest(BaseModel):
    text: str


@app.post("/process")
def process_invoice(req: InvoiceRequest):
    text = req.text

    vendor = extract_vendor(text)
    date = extract_date(text)
    amount = extract_amount(text)

    return {
        "vendor": vendor,
        "invoice_date": date,
        "amount_total": amount
    }


# Simple extractors
def extract_vendor(text):
    for line in text.split("\n"):
        if "anthropic" in line.lower():
            return line.strip()
    return "Unknown Vendor"


def extract_date(text):
    m = re.search(
        r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}",
        text)
    return m.group(0) if m else "Unknown"


def extract_amount(text):
    m = re.search(r"\$[\d,]+\.\d{2}", text)
    return m.group(0) if m else "Unknown"
