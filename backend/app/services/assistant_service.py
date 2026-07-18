"""
Service cho AI Assistant (chatbot) - dùng bởi router /assistant/chat.
"""
import re
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Farm, YieldPrediction, DiseaseDetection, MarketPrice, Crop
from app.services import llm_client

CROP_NAME_VI = {
    "rice": "lúa",
    "coffee": "cà phê",
    "vegetable": "rau",
}

CROP_ALIASES = {
    "lúa": "rice",
    "gạo": "rice",
    "cà phê": "coffee",
    "caphe": "coffee",
    "rau": "vegetable",
}

_PERIOD_HINT_RE = re.compile(r"qu[ýy]\s*\d|n[ăa]m\s*\d{4}|q\d\s*[\-/]\s*\d{4}")


def _quarter_bounds(quarter: int, year: int) -> tuple[date, date]:
    start_month = (quarter - 1) * 3 + 1
    start = date(year, start_month, 1)
    end_month = start_month + 2
    end_year = year
    if end_month > 12:
        end_month -= 12
        end_year += 1
    end = date(end_year, end_month, 28)  # đơn giản hoá: ngày 28 an toàn cho mọi tháng
    return start, end


def _current_quarter() -> tuple[int, int]:
    today = date.today()
    return (today.month - 1) // 3 + 1, today.year


def _extract_period(text: str) -> tuple[tuple[date, date], str]:
    """Tìm 'quý X năm YYYY', 'QX-YYYY' hoặc chỉ 'năm YYYY'. Mặc định: quý hiện tại."""
    text_l = text.lower()

    m = re.search(r"qu[ýy]\s*(\d)\D{0,10}?(\d{4})", text_l)
    if m and 1 <= int(m.group(1)) <= 4:
        quarter, year = int(m.group(1)), int(m.group(2))
        return _quarter_bounds(quarter, year), f"quý {quarter}/{year}"

    m = re.search(r"\bq\s*(\d)\s*[\-/]\s*(\d{4})", text_l)
    if m and 1 <= int(m.group(1)) <= 4:
        quarter, year = int(m.group(1)), int(m.group(2))
        return _quarter_bounds(quarter, year), f"quý {quarter}/{year}"

    m = re.search(r"n[ăa]m\s*(\d{4})", text_l)
    if m:
        year = int(m.group(1))
        return (date(year, 1, 1), date(year, 12, 31)), f"năm {year}"

    quarter, year = _current_quarter()
    return _quarter_bounds(quarter, year), f"quý {quarter}/{year} (kỳ hiện tại)"


def _extract_crop(text: str) -> Optional[str]:
    text_l = text.lower()
    for alias, crop_name in CROP_ALIASES.items():
        if alias in text_l:
            return crop_name
    return None


def _resolve_context(message: str, history: list[dict]) -> str:
    """Bổ sung ngữ cảnh từ các lượt hỏi trước (role=user) nếu message hiện tại
    thiếu mốc thời gian hoặc cây trồng, để hỗ trợ câu hỏi nối tiếp."""
    has_period = bool(_PERIOD_HINT_RE.search(message.lower()))
    has_crop = _extract_crop(message) is not None

    if has_period and has_crop:
        return message

    extra = []
    for turn in reversed(history or []):
        if turn.get("role") != "user":
            continue
        content = turn.get("content", "") or ""
        if not has_period and _PERIOD_HINT_RE.search(content.lower()):
            extra.append(content)
            has_period = True
        if not has_crop and _extract_crop(content):
            extra.append(content)
            has_crop = True
        if has_period and has_crop:
            break

    return " ".join(extra + [message]) if extra else message


def _detect_topic(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["giá", "thị trường", "market"]):
        return "market"
    if any(k in t for k in ["sâu bệnh", "dịch bệnh", "bệnh"]):
        return "disease"
    if any(k in t for k in ["năng suất", "sản lượng", "mùa vụ", "yield"]):
        return "yield"
    return "all"


def _disease_summary(db: Session, start: date, end: date, crop_name: Optional[str]) -> str:
    q = db.query(DiseaseDetection).filter(
        DiseaseDetection.created_at >= start, DiseaseDetection.created_at <= end
    )
    if crop_name:
        q = q.filter(DiseaseDetection.crop_type == crop_name)
    detections = q.all()

    if not detections:
        return "- Sâu bệnh: không ghi nhận lượt phát hiện nào trong kỳ."

    counts: dict[str, int] = {}
    for d in detections:
        counts[d.disease_label] = counts.get(d.disease_label, 0) + 1
    top = sorted(counts.items(), key=lambda x: -x[1])[:3]
    top_str = ", ".join(f"{name} ({cnt} ca)" for name, cnt in top)
    return f"- Sâu bệnh: ghi nhận {len(detections)} lượt phát hiện, phổ biến nhất là {top_str}."


def _yield_summary(db: Session, start: date, end: date, crop_id: Optional[int]) -> str:
    q = db.query(YieldPrediction).join(Farm).filter(
        YieldPrediction.created_at >= start, YieldPrediction.created_at <= end
    )
    if crop_id:
        q = q.filter(Farm.crop_id == crop_id)
    preds = q.all()

    if not preds:
        return "- Năng suất: chưa có dự báo nào được ghi nhận trong kỳ."

    avg_yield = sum(p.predicted_yield for p in preds) / len(preds)
    return (
        f"- Năng suất: {len(preds)} dự báo được ghi nhận, "
        f"năng suất trung bình đạt {avg_yield:.2f} tấn/ha."
    )


def _market_summary(db: Session, start: date, end: date, crop_name: Optional[str]) -> str:
    crop_list = [crop_name] if crop_name else list(CROP_NAME_VI.keys())
    lines = []
    for c in crop_list:
        crop_obj = db.query(Crop).filter(Crop.name == c).first()
        if not crop_obj:
            continue
        prices = (
            db.query(MarketPrice)
            .filter(
                MarketPrice.crop_id == crop_obj.id,
                MarketPrice.date >= start,
                MarketPrice.date <= end,
            )
            .order_by(MarketPrice.date)
            .all()
        )
        if not prices:
            continue
        first_price, last_price = prices[0].price, prices[-1].price
        change = ((last_price - first_price) / first_price * 100) if first_price else 0.0
        label = CROP_NAME_VI.get(c, c)
        if change > 1:
            lines.append(f"{label} tăng {change:.1f}% (từ {first_price:,.0f} lên {last_price:,.0f} VND/kg)")
        elif change < -1:
            lines.append(f"{label} giảm {abs(change):.1f}% (từ {first_price:,.0f} xuống {last_price:,.0f} VND/kg)")
        else:
            lines.append(f"{label} giữ giá ổn định quanh {last_price:,.0f} VND/kg")

    if not lines:
        return "- Giá thị trường: không có dữ liệu giá trong kỳ."
    return "- Giá thị trường: " + "; ".join(lines) + "."


def build_reply(db: Session, message: str, history: list[dict]) -> str:
    """Sinh câu trả lời tiếng Việt (plain text) cho endpoint POST /assistant/chat.

    Bước 1 (luôn chạy, rule-based): truy vấn DB thật để lấy các "sự kiện" -
    đây là nguồn sự thật, tránh LLM bịa số liệu.
    Bước 2 (tuỳ chọn, nếu đã cấu hình FPT_API_KEY): đưa dữ liệu ở bước 1 cho
    LLM (FPT AI Marketplace) diễn đạt lại thành câu trả lời tự nhiên hơn,
    có xét ngữ cảnh hội thoại (history). Nếu bước này lỗi (mạng, timeout,
    quota...), lặng lẽ fallback về kết quả rule-based của bước 1.
    """
    # Kiểm tra câu hỏi về khả năng của chatbot
    msg_lower = message.lower()
    if any(phrase in msg_lower for phrase in ["bạn có thể làm gì", "bạn làm được gì", "chức năng", "khả năng", "bạn có thể giúp gì"]):
        return _CAPABILITIES_ANSWER

    context_text = _resolve_context(message, history)
    (start, end), period_label = _extract_period(context_text)
    crop_name = _extract_crop(context_text)
    topic = _detect_topic(message)

    crop_id = None
    if crop_name:
        crop_obj = db.query(Crop).filter(Crop.name == crop_name).first()
        crop_id = crop_obj.id if crop_obj else None

    scope_note = f" cho {CROP_NAME_VI.get(crop_name, crop_name)}" if crop_name else ""
    lines = [
        f"Tổng hợp sự kiện {period_label}{scope_note} "
        f"(từ {start.strftime('%d/%m/%Y')} đến {end.strftime('%d/%m/%Y')}):"
    ]

    if topic in ("all", "disease"):
        lines.append(_disease_summary(db, start, end, crop_name))
    if topic in ("all", "yield"):
        lines.append(_yield_summary(db, start, end, crop_id))
    if topic in ("all", "market"):
        lines.append(_market_summary(db, start, end, crop_name))

    if len(lines) == 1:
        lines.append("Hiện chưa có dữ liệu nào được ghi nhận trong khoảng thời gian này.")

    rule_based_reply = "\n".join(lines)

    if llm_client.is_configured():
        try:
            return _synthesize_with_llm(message, history, rule_based_reply)
        except Exception:
            # Lỗi gọi LLM (mạng, timeout, quota, response sai định dạng...):
            # fallback im lặng về câu trả lời rule-based, không để lỗi
            # provider ngoài làm hỏng trải nghiệm chat.
            return rule_based_reply

    return rule_based_reply


_SYSTEM_PROMPT = (
    "Bạn là trợ lý AI của hệ thống AI Nông Nghiệp Điện Biên, hỗ trợ cán bộ/"
    "nông dân tra cứu thông tin nông nghiệp. "
    "Trả lời ngắn gọn, tự nhiên, thân thiện bằng tiếng Việt. "
    "Nếu được cung cấp dữ liệu, hãy diễn giải tự nhiên. "
    "Nếu không có dữ liệu phù hợp, hãy nói rõ và gợi ý câu hỏi khác. "
    "KHÔNG dùng Markdown hay ký tự đặc biệt."
)

_CAPABILITIES_ANSWER = (
    "Tôi có thể giúp bạn: "
    "1. Xem tình hình sâu bệnh cây trồng theo quý. "
    "2. Tra cứu năng suất và sản lượng dự kiến theo vụ mùa. "
    "3. Theo dõi giá thị trường các loại nông sản như lúa, cà phê, rau màu. "
    "4. Đặt câu hỏi về tình hình nông nghiệp Điện Biên. "
    "Bạn cần thông tin gì?"
)


def _synthesize_with_llm(message: str, history: list[dict], facts_text: str) -> str:
    messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
    for turn in (history or [])[-6:]:  # giới hạn ngữ cảnh để tránh prompt quá dài
        role = turn.get("role")
        content = turn.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({
        "role": "user",
        "content": (
            f"Câu hỏi: {message}\n\n"
            f"Dữ liệu tra cứu được:\n{facts_text}\n\n"
            "Hãy diễn giải dữ liệu trên thành câu trả lời tự nhiên cho câu hỏi."
        ),
    })
    reply = llm_client.chat_completion(messages)
    return reply if reply else facts_text