"""
Lanyun MaaS API client for chat/completions.

- Loads credentials from environment (.env supported via python-dotenv)
- Matches the API schema you provided
- Safe defaults and small helper utilities
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

# Load .env once on import (no-op if missing)
load_dotenv()

DEFAULT_BASE_URL = "https://maas-api.lanyun.net/v1"  # per user's latest spec
DEFAULT_MODEL = os.getenv("LANYUN_MODEL", "Kimi-K2-instruct")


def load_maas_config(default_base_url: str = DEFAULT_BASE_URL) -> Dict[str, str]:
    """
    Returns a dict with api_key, base_url, model.
    Env:
      - LANYUN_API_KEY or LANYUN_MAAS_API_KEY
      - LANYUN_MAAS_BASE_URL (optional)
      - LANYUN_MODEL (optional)
    """
    api_key = os.getenv("LANYUN_API_KEY") or os.getenv("LANYUN_MAAS_API_KEY") or ""
    base_url = os.getenv("LANYUN_MAAS_BASE_URL", default_base_url).rstrip("/")
    model = os.getenv("LANYUN_MODEL", DEFAULT_MODEL)
    return {"api_key": api_key, "base_url": base_url, "model": model}


class LanyunMaaSClient:
    """
    Minimal client for /chat/completions
    Request (per spec):
      POST {base_url}/chat/completions
      headers:
        - Content-Type: application/json
        - Authorization: Bearer {api_key}
      body:
        {
          "model": "/maas/deepseek-ai/DeepSeek-R1",
          "messages": [
            {"role":"system","content":"You are a helpful assistant."},
            {"role":"user","content":"Hello!"}
          ],
          "temperature": 0.3
        }

    Response (relevant subset):
        {
          "choices": [
            {
              "index": 0,
              "message": {"role":"assistant","content":"..."},
              "finish_reason": "stop"
            }
          ],
          "model": "/maas/deepseek-ai/DeepSeek-R1",
          "usage": { ... }
        }
    """

    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL) -> None:
        if not api_key:
            raise ValueError("Missing Lanyun API key")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.3,
        timeout: float = 20.0,
    ) -> str:
        """
        Returns assistant message content string.
        Raises httpx.HTTPError on transport/status errors, or ValueError on schema issues.
        """
        the_model = model or DEFAULT_MODEL
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": the_model,
            "messages": messages,
            "temperature": temperature,
        }

        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        # Parse OpenAI-like schema
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Invalid response: missing choices")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not isinstance(content, str):
            raise ValueError("Invalid response: missing message.content")

        return content.strip()