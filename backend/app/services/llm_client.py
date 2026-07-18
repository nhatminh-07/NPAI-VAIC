"""
Client gọi LLM qua endpoint OpenAI-compatible của FPT AI Marketplace
(https://marketplace.fptcloud.com). Dùng thẳng `requests` (đã có sẵn trong
requirements.txt) thay vì thêm SDK `openai` làm dependency mới.

Cấu hình qua biến môi trường (xem .env.example ở thư mục backend/):
  FPT_API_KEY   - bắt buộc để bật tính năng LLM. Tạo tại
                  marketplace.fptcloud.com/en/my-account#my-api-key
  FPT_BASE_URL  - mặc định https://mkp-api.fptcloud.com/v1
  FPT_MODEL     - mặc định gemma-4-31B-it

Nếu FPT_API_KEY rỗng, is_configured() trả về False - nơi gọi (assistant_service)
sẽ tự fallback sang câu trả lời rule-based, không có gì bị crash.
"""
import requests

from app.config import FPT_API_KEY, FPT_BASE_URL, FPT_MODEL

_TIMEOUT_SECONDS = 20


def is_configured() -> bool:
    return bool(FPT_API_KEY)


def chat_completion(messages: list[dict], temperature: float = 0.3) -> str:
    """Gọi POST {FPT_BASE_URL}/chat/completions, trả về nội dung text.

    Raise (requests.RequestException, KeyError, ...) nếu có lỗi mạng, HTTP,
    hoặc response không đúng định dạng mong đợi - bên gọi chịu trách nhiệm
    bắt lỗi và fallback nếu cần, để một lỗi tạm thời của LLM provider không
    làm sập cả endpoint /assistant/chat.
    """
    if not FPT_API_KEY:
        raise RuntimeError("FPT_API_KEY chưa được cấu hình (xem .env.example).")

    resp = requests.post(
        f"{FPT_BASE_URL.rstrip('/')}/chat/completions",
        headers={
            "Authorization": f"Bearer {FPT_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": FPT_MODEL,
            "messages": messages,
            "temperature": temperature,
        },
        timeout=_TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()