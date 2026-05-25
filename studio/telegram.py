"""Minimal Telegram helpers for studio — send messages, photo+approval, long-poll."""
import json, os, time, uuid
import requests

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")


def _url(method):
    return f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"


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


def new_token() -> str:
    return uuid.uuid4().hex[:10].upper()
