import os
import fitz
import requests
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()  # loads .env.dev or .env.prod

ENV = os.getenv("ENV", "development")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5050")

app = FastAPI(
    docs_url="/docs" if ENV == "development" else None,
    redoc_url="/redoc" if ENV == "development" else None,
    openapi_url="/openapi.json" if ENV == "development" else None,
)

# CORS (best practice)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

MCP_URL = os.getenv("MCP_URL", "http://localhost:8000/process")


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    try:
        pdf_bytes = await file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = "\n".join([page.get_text() for page in doc])

        response = requests.post(MCP_URL, json={"text": text})

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"MCP error: {response.text}")

        return response.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
