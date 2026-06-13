"""
ShopMind AI — LLM Provider Abstraction
Primary: Gemini 2.5 Flash
Fallback: Groq
Secondary fallback: OpenRouter
"""

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct")


@dataclass
class LLMResponse:
    content: str
    provider: str
    model: str
    usage: Optional[Dict[str, Any]] = None


def _chat_payload(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 900,
    }


async def _call_gemini(system_prompt: str, user_prompt: str) -> LLMResponse:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not configured")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    body = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"System Instructions:\n{system_prompt}\n\nUser Prompt:\n{user_prompt}"}],
            }
        ],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 900},
    }
    headers = {"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=25.0) as client:
        res = await client.post(url, headers=headers, json=body)
    res.raise_for_status()
    data = res.json()

    candidates = data.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini returned no candidates")

    parts = candidates[0].get("content", {}).get("parts", [])
    text = "\n".join(str(p.get("text", "")) for p in parts if p.get("text"))
    if not text.strip():
        raise RuntimeError("Gemini returned empty text")

    return LLMResponse(
        content=text.strip(),
        provider="gemini",
        model=GEMINI_MODEL,
        usage=data.get("usageMetadata"),
    )


async def _call_groq(system_prompt: str, user_prompt: str) -> LLMResponse:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not configured")

    url = "https://api.groq.com/openai/v1/chat/completions"
    body = {
        **_chat_payload(system_prompt, user_prompt),
        "model": GROQ_MODEL,
    }
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=25.0) as client:
        res = await client.post(url, headers=headers, json=body)
    res.raise_for_status()
    data = res.json()

    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("Groq returned no choices")

    text = choices[0].get("message", {}).get("content", "")
    if not text.strip():
        raise RuntimeError("Groq returned empty text")

    return LLMResponse(
        content=text.strip(),
        provider="groq",
        model=GROQ_MODEL,
        usage=data.get("usage"),
    )


async def _call_openrouter(system_prompt: str, user_prompt: str) -> LLMResponse:
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY not configured")

    url = "https://openrouter.ai/api/v1/chat/completions"
    body = {
        **_chat_payload(system_prompt, user_prompt),
        "model": OPENROUTER_MODEL,
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://shopmind.ai",
        "X-Title": "ShopMind AI",
    }

    async with httpx.AsyncClient(timeout=25.0) as client:
        res = await client.post(url, headers=headers, json=body)
    res.raise_for_status()
    data = res.json()

    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("OpenRouter returned no choices")

    text = choices[0].get("message", {}).get("content", "")
    if not text.strip():
        raise RuntimeError("OpenRouter returned empty text")

    return LLMResponse(
        content=text.strip(),
        provider="openrouter",
        model=OPENROUTER_MODEL,
        usage=data.get("usage"),
    )


async def generate_with_failover(system_prompt: str, user_prompt: str) -> LLMResponse:
    """
    Try Gemini -> Groq -> OpenRouter with automatic failover.
    """
    attempts = [
        ("gemini", _call_gemini),
        ("groq", _call_groq),
        ("openrouter", _call_openrouter),
    ]

    errors: List[str] = []
    for name, fn in attempts:
        try:
            result = await fn(system_prompt=system_prompt, user_prompt=user_prompt)
            return result
        except Exception as exc:
            msg = f"{name}: {str(exc)[:180]}"
            errors.append(msg)
            logger.warning("LLM provider failed, switching fallback -> %s", msg)

    raise RuntimeError("All LLM providers failed: " + " | ".join(errors))
