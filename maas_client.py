"""
Lanyun MaaS API client for chat/completions.

- Loads credentials from environment (.env supported via python-dotenv)
- Robust parsing and observability with optional debug dumps
- Retries with exponential backoff for transient errors
"""

from __future__ import annotations

import os
import time
import json
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

# Load .env once on import (no-op if missing)
load_dotenv()

DEFAULT_BASE_URL = "https://maas-api.lanyun.net/v1"
DEFAULT_MODEL = os.getenv("LANYUN_MODEL", "/maas/kimi/Kimi-K2-Instruct")


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
          "model": "/maas/kimi/Kimi-K2-Instruct",
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
          "model": "/maas/kimi/Kimi-K2-Instruct",
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
        Retries transient errors controlled by env:
          - LANYUN_TIMEOUT_SECS (float, default=timeout)
          - LANYUN_RETRIES (int, default=2)
          - LANYUN_BACKOFF_SECS (float, default=1.5)
          - LANYUN_DEBUG (truthy to dump outputs/maas_last_response.json)
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

        debug = os.getenv("LANYUN_DEBUG", "").strip().lower() not in ("", "0", "false", "no")

        def _debug_dump(obj: dict):
            if not debug:
                return
            try:
                os.makedirs("outputs", exist_ok=True)
                with open(os.path.join("outputs", "maas_last_response.json"), "w", encoding="utf-8") as f:
                    json.dump(obj, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

        # Env-based runtime config
        try:
            effective_timeout = float(os.getenv("LANYUN_TIMEOUT_SECS", str(timeout)))
        except Exception:
            effective_timeout = timeout
        try:
            retries = int(os.getenv("LANYUN_RETRIES", "2"))
        except Exception:
            retries = 2
        try:
            backoff = float(os.getenv("LANYUN_BACKOFF_SECS", "1.5"))
        except Exception:
            backoff = 1.5

        last_err: Optional[Exception] = None

        for attempt in range(retries + 1):
            try:
                with httpx.Client(timeout=effective_timeout) as client:
                    resp = client.post(url, headers=headers, json=payload)
                    status_code = resp.status_code
                    text_preview = resp.text[:2000] if isinstance(resp.text, str) else None
                    try:
                        data = resp.json()
                    except Exception as je:
                        _debug_dump({
                            "phase": "json_decode_error",
                            "attempt": attempt,
                            "http_status": status_code,
                            "text": text_preview,
                        })
                        resp.raise_for_status()
                        raise ValueError("Invalid JSON response from MaaS") from je

                    _debug_dump({"phase": "ok", "attempt": attempt, "http_status": status_code, "json": data})
                    resp.raise_for_status()

                # Parse OpenAI-like schema with fallbacks
                choices = data.get("choices")
                if not isinstance(choices, list) or not choices:
                    raise ValueError("Invalid response: missing choices")
                choice0 = choices[0] or {}

                content: Optional[str] = None

                # 1) message.content
                message = choice0.get("message")
                if isinstance(message, dict):
                    c = message.get("content")
                    if isinstance(c, str) and c.strip():
                        content = c

                # 2) messages[-1].content
                if content is None:
                    msgs = choice0.get("messages")
                    if isinstance(msgs, list) and msgs:
                        last = msgs[-1]
                        if isinstance(last, dict):
                            c = last.get("content")
                            if isinstance(c, str) and c.strip():
                                content = c

                # 3) delta.content (stream-style)
                if content is None:
                    delta = choice0.get("delta")
                    if isinstance(delta, dict):
                        c = delta.get("content")
                        if isinstance(c, str) and c.strip():
                            content = c

                # 4) text
                if content is None:
                    c = choice0.get("text")
                    if isinstance(c, str) and c.strip():
                        content = c

                if not isinstance(content, str) or not content.strip():
                    raise ValueError(f"Invalid response: cannot locate content in choices[0], keys={list(choice0.keys())}")

                return content.strip()

            except httpx.HTTPStatusError as e:
                last_err = e
                resp = getattr(e, "response", None)
                code = getattr(resp, "status_code", None)
                _debug_dump({
                    "phase": "http_status_error",
                    "attempt": attempt,
                    "error": str(e),
                    "http_status": code,
                    "text": getattr(resp, "text", None)[:2000] if resp is not None else None,
                })
                if code == 429 or (isinstance(code, int) and 500 <= code < 600):
                    if attempt < retries:
                        time.sleep(backoff * (2 ** attempt))
                        continue
                raise
            except httpx.RequestError as e:
                last_err = e
                _debug_dump({"phase": "request_error", "attempt": attempt, "error": str(e)})
                if attempt < retries:
                    time.sleep(backoff * (2 ** attempt))
                    continue
                raise
            except Exception as e:
                last_err = e
                _debug_dump({"phase": "parse_or_other_error", "attempt": attempt, "error": f"{e.__class__.__name__}: {e}"})
                # Parsing/other errors are not retried unless you want to; here we stop.
                raise

        # Shouldn't reach here; raise last error if any
        if last_err:
            raise last_err
        raise ValueError("MaaS chat_completion failed without specific error")