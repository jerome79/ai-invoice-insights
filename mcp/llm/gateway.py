from __future__ import annotations

import os
from llm.ollama import ollama_generate


def llm_enabled() -> bool:
    return os.getenv("LLM_BACKEND", "none").lower() != "none"


def llm_backend() -> str:
    return os.getenv("LLM_BACKEND", "none").lower()


def llm_model() -> str:
    # unify naming even if provider differs later
    if llm_backend() == "ollama":
        return os.getenv("OLLAMA_MODEL", "gemma3:1b")
    if llm_backend() == "openai":
        return os.getenv("OPENAI_MODEL", "gpt-4.1")
    return ""


def generate_json(prompt: str) -> dict:
    """
    Single entrypoint used by agents.
    """
    backend = llm_backend()
    if backend == "none":
        return {}
    if backend == "ollama":
        return ollama_generate(prompt)

    # Stubs for later providers
    raise ValueError(f"Unsupported LLM_BACKEND={backend}. Use 'ollama' or 'none' for now.")
