"""Minimal Telegram helpers for studio — send messages, photo+approval, long-poll."""
import io, json, os, time, uuid
from datetime import datetime, timezone, timedelta
import requests

IST = timezone(timedelta(hours=5, minutes=30))

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")


def _url(method):
    return f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"


def send_document(filename: str, content: str, caption: str = ""):
    """Send a plain-text file as a Telegram document (easy to open & copy on phone)."""
    buf = io.BytesIO(content.encode("utf-8"))
    resp = requests.post(_url("sendDocument"), data={
        "chat_id": CHAT_ID,
        "caption": caption,
    }, files={"document": (filename, buf, "text/plain")}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def send_photo(image_path: str, caption: str):
    """Send a photo with caption (no buttons)."""
    img_bytes = _compress_for_telegram(image_path)
    resp = requests.post(_url("sendPhoto"), data={
        "chat_id": CHAT_ID,
        "caption": caption,
    }, files={"photo": ("preview.jpg", img_bytes, "image/jpeg")}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def send_text(text: str):
    resp = requests.post(_url("sendMessage"), json={
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _compress_for_telegram(image_path: str) -> bytes:
    """Return JPEG bytes under 9MB, resizing if needed."""
    from PIL import Image
    import io
    img = Image.open(image_path).convert("RGB")
    for quality in (85, 70, 55, 40):
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        if buf.tell() < 9 * 1024 * 1024:
            return buf.getvalue()
    # Last resort: halve dimensions
    img = img.resize((img.width // 2, img.height // 2), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=70)
    return buf.getvalue()


def send_approval(image_path: str | None, caption: str, token: str):
    """Send photo (or text) with APPROVE / REJECT inline buttons."""
    keyboard = {"inline_keyboard": [[
        {"text": "✅ APPROVE", "callback_data": f"APPROVE_{token}"},
        {"text": "❌ REJECT",  "callback_data": f"REJECT_{token}"},
    ]]}
    if image_path and os.path.exists(image_path):
        img_bytes = _compress_for_telegram(image_path)
        resp = requests.post(_url("sendPhoto"), data={
            "chat_id":      CHAT_ID,
            "caption":      caption,
            "reply_markup": json.dumps(keyboard),
        }, files={"photo": ("preview.jpg", img_bytes, "image/jpeg")}, timeout=30)
    else:
        resp = requests.post(_url("sendMessage"), json={
            "chat_id":      CHAT_ID,
            "text":         caption,
            "reply_markup": keyboard,
        }, timeout=15)
    resp.raise_for_status()
    return resp.json()


def wait_for_decision(token: str, timeout_seconds: int = 21600) -> str:
    """Long-poll until APPROVE/REJECT button tapped. Returns 'approved'/'rejected'/'timeout'."""
    deadline = time.time() + timeout_seconds
    try:
        r = requests.get(_url("getUpdates"), params={"limit": 1, "offset": -1}, timeout=10)
        results = r.json().get("result", [])
        offset = results[-1]["update_id"] + 1 if results else 0
    except Exception:
        offset = 0

    print(f"[telegram] Waiting up to {timeout_seconds // 3600}h for approval...")
    while time.time() < deadline:
        remaining = int(deadline - time.time())
        wait = min(30, remaining)
        if wait <= 0:
            break
        try:
            r = requests.get(_url("getUpdates"), params={
                "offset": offset, "timeout": wait, "limit": 10,
            }, timeout=wait + 5)
            updates = r.json().get("result", [])
        except Exception as e:
            print(f"[telegram] Poll error: {e}")
            time.sleep(5)
            continue
        for upd in updates:
            offset = upd["update_id"] + 1
            cq = upd.get("callback_query", {})
            data = cq.get("data", "")
            if data == f"APPROVE_{token}":
                requests.post(_url("answerCallbackQuery"), json={
                    "callback_query_id": cq["id"], "text": "✅ Uploading now...",
                }, timeout=5)
                print("[telegram] Decision: APPROVED")
                return "approved"
            if data == f"REJECT_{token}":
                requests.post(_url("answerCallbackQuery"), json={
                    "callback_query_id": cq["id"], "text": "❌ Skipped.",
                }, timeout=5)
                print("[telegram] Decision: REJECTED")
                return "rejected"
    print(f"[telegram] No reply after {timeout_seconds // 3600}h — auto-approved.")
    return "timeout"


def send_schedule_prompt(token: str):
    """Send preset schedule buttons. Times are IST. No typing needed."""
    now = datetime.now(IST)

    def _btn(label: str, day_offset: int, hour: int) -> dict:
        key = f"SCH_{token}_{day_offset}_{hour}"
        return {"text": label, "callback_data": key}

    # Build future-only time slots for today
    slots_today = []
    for h, label in [(9, "9 AM"), (12, "12 PM"), (18, "6 PM"), (21, "9 PM")]:
        t = now.replace(hour=h, minute=0, second=0, microsecond=0)
        if t > now:
            slots_today.append(_btn(f"Today {label}", 0, h))

    # Always offer tomorrow 9 AM
    slots_tomorrow = [_btn("Tomorrow 9 AM", 1, 9)]
    publish_now_btn = [{"text": "⚡ Publish Now", "callback_data": f"PUB_NOW_{token}"}]

    # Lay out in rows of 2
    all_btns = slots_today + slots_tomorrow
    rows = [all_btns[i:i+2] for i in range(0, len(all_btns), 2)]
    rows.append(publish_now_btn)

    requests.post(_url("sendMessage"), json={
        "chat_id":      CHAT_ID,
        "parse_mode":   "HTML",
        "text":         "<b>When to publish?</b>\n<i>No tap in 3h = Publish Now</i>",
        "reply_markup": json.dumps({"inline_keyboard": rows}),
    }, timeout=15).raise_for_status()


def wait_for_schedule(token: str, timeout_seconds: int = 10800) -> str | None:
    """Poll for schedule button tap. Returns RFC3339 IST string or None to publish now."""
    deadline = time.time() + timeout_seconds
    try:
        r = requests.get(_url("getUpdates"), params={"limit": 1, "offset": -1}, timeout=10)
        results = r.json().get("result", [])
        offset = results[-1]["update_id"] + 1 if results else 0
    except Exception:
        offset = 0

    print("[telegram] Waiting up to 3h for schedule tap...")
    while time.time() < deadline:
        remaining = int(deadline - time.time())
        wait = min(30, remaining)
        if wait <= 0:
            break
        try:
            r = requests.get(_url("getUpdates"), params={
                "offset": offset, "timeout": wait, "limit": 10,
            }, timeout=wait + 5)
            updates = r.json().get("result", [])
        except Exception as e:
            print(f"[telegram] Poll error: {e}")
            time.sleep(5)
            continue
        for upd in updates:
            offset = upd["update_id"] + 1
            cq = upd.get("callback_query", {})
            data = cq.get("data", "")

            if data == f"PUB_NOW_{token}":
                requests.post(_url("answerCallbackQuery"), json={
                    "callback_query_id": cq["id"], "text": "Publishing now!",
                }, timeout=5)
                print("[telegram] Schedule: Publish Now")
                return None

            if data.startswith(f"SCH_{token}_"):
                _, _, _, day_offset, hour = data.split("_", 4)
                dt = (datetime.now(IST).replace(hour=int(hour), minute=0, second=0, microsecond=0)
                      + __import__("datetime").timedelta(days=int(day_offset)))
                label = dt.strftime("%d %b %Y %I:%M %p") + " IST"
                requests.post(_url("answerCallbackQuery"), json={
                    "callback_query_id": cq["id"], "text": f"Scheduled for {label}",
                }, timeout=5)
                print(f"[telegram] Schedule: {dt.isoformat()}")
                return dt.isoformat()

    print("[telegram] No schedule tap in 3h — publishing now.")
    return None


def new_token() -> str:
    return uuid.uuid4().hex[:10].upper()
