"""FastAPI wrapper for AI Invoice Insights.

This module provides a REST API interface for invoice processing.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Invoice Insights API",
    description="REST API for invoice processing and insights extraction",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InvoiceData(BaseModel):
    """Invoice data model."""
    content: str
    metadata: Optional[Dict[str, Any]] = None


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Invoice Insights API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/process-invoice")
async def process_invoice(invoice: InvoiceData):
    """Process invoice data.

    Args:
        invoice: Invoice data to process

    Returns:
        Processed invoice insights
    """
    try:
        logger.info("Processing invoice via API")
        # TODO: Implement actual invoice processing logic
        result = {
            "status": "success",
            "data": {
                "invoice_number": "INV-001",
                "amount": "100.00",
                "date": "2025-01-01"
            }
        }
        return result
    except Exception as e:
        logger.error(f"Error processing invoice: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload-invoice")
async def upload_invoice(file: UploadFile = File(...)):
    """Upload and process an invoice file.

    Args:
        file: Invoice file to upload

    Returns:
        Upload status and processing results
    """
    try:
        logger.info(f"Received file upload: {file.filename}")
        content = await file.read()
        # TODO: Implement file processing
        return {
            "status": "success",
            "filename": file.filename,
            "size": len(content)
        }
    except Exception as e:
        logger.error(f"Error uploading invoice: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
