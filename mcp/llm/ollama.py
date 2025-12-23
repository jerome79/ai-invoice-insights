from __future__ import annotations

import json
import os
import requests


def ollama_generate(prompt: str) -> dict:
    """
    Calls Ollama HTTP API (generate) and returns parsed JSON when possible.
    """
    base_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3.2:latest")

    url = f"{base_url.rstrip('/')}/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False}

    r = requests.post(url, json=payload, timeout=120)
    r.raise_for_status()

    text = r.json().get("response", "") or ""
    # Try parse JSON directly
    try:
        return json.loads(text)
    except Exception:
        # Try to salvage JSON block
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                return {}
        return {}
