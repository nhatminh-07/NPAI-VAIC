"""
Client gọi LLM qua OpenAI-compatible endpoint.

Cấu hình qua biến môi trường (xem .env.example ở thư mục backend/):
  OPENAI_API_KEY  - bắt buộc để bật tính năng LLM
  OPENAI_BASE_URL - mặc định https://api.openai.com/v1
  OPENAI_MODEL    - mặc định gpt-4o-mini

Nếu OPENAI_API_KEY rỗng, is_configured() trả về False - nơi gọi (assistant_service)
sẽ tự fallback sang câu trả lời rule-based, không có gì bị crash.
"""
import os
import requests

_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
_API_KEY = os.getenv("OPENAI_API_KEY", "")
_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
_TIMEOUT_SECONDS = 20


def is_configured() -> bool:
    return bool(_API_KEY)


def chat_completion(messages: list[dict], temperature: float = 0.3) -> str:
    """Gọi POST {_BASE_URL}/chat/completions, trả về nội dung text.

    Raise (requests.RequestException, KeyError, ...) nếu có lỗi mạng, HTTP,
    hoặc response không đúng định dạng mong đợi - bên gọi chịu trách nhiệm
    bắt lỗi và fallback nếu cần, để một lỗi tạm thời của LLM provider không
    làm sập cả endpoint /assistant/chat.
    """
    if not _API_KEY:
        raise RuntimeError("OPENAI_API_KEY chưa được cấu hình (xem .env.example).")

    resp = requests.post(
        f"{_BASE_URL.rstrip('/')}/chat/completions",
        headers={
            "Authorization": f"Bearer {_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": _MODEL,
            "messages": messages,
            "temperature": temperature,
        },
        timeout=_TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()
