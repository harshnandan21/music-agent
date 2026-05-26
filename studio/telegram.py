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


def send_duration_prompt(token: str):
    """Ask how long the video should be. Preset buttons + Custom option."""
    durations = [("~1 min", 1), ("~20 min", 20), ("~30 min", 30), ("~60 min", 60)]

    def _btn(label: str, minutes: int) -> dict:
        return {"text": label, "callback_data": f"DUR_{token}_{minutes}"}

    rows = [
        [_btn(l, m) for l, m in durations[:2]],
        [_btn(l, m) for l, m in durations[2:]],
        [{"text": "✏️ Custom", "callback_data": f"DUR_{token}_custom"}],
    ]
    requests.post(_url("sendMessage"), json={
        "chat_id":      CHAT_ID,
        "parse_mode":   "HTML",
        "text":         "<b>How long should the video be?</b>\n<i>No tap in 10 min = 20 min default</i>",
        "reply_markup": json.dumps({"inline_keyboard": rows}),
    }, timeout=15).raise_for_status()


def wait_for_duration(token: str, timeout_seconds: int = 600) -> int:
    """Poll for duration tap or typed number. Returns minutes. Default 20 on timeout."""
    deadline = time.time() + timeout_seconds
    try:
        r = requests.get(_url("getUpdates"), params={"limit": 1, "offset": -1}, timeout=10)
        results = r.json().get("result", [])
        offset = results[-1]["update_id"] + 1 if results else 0
    except Exception:
        offset = 0

    print("[telegram] Waiting up to 10 min for duration...")
    custom_mode = False  # True after user taps Custom — next text message is the answer

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
            cq   = upd.get("callback_query", {})
            data = cq.get("data", "")
            msg  = upd.get("message", {})

            # Preset button tapped
            if data.startswith(f"DUR_{token}_") and not data.endswith("_custom"):
                minutes = int(data.split("_")[-1])
                requests.post(_url("answerCallbackQuery"), json={
                    "callback_query_id": cq["id"], "text": f"~{minutes} min selected.",
                }, timeout=5)
                print(f"[telegram] Duration: ~{minutes} min")
                return minutes

            # Custom button tapped — ask user to type
            if data == f"DUR_{token}_custom":
                requests.post(_url("answerCallbackQuery"), json={
                    "callback_query_id": cq["id"], "text": "Type duration below.",
                }, timeout=5)
                send_text("Type duration in minutes (e.g. 8 or 25):")
                custom_mode = True

            # Text reply after Custom tap
            if custom_mode and msg.get("text", "").strip().isdigit():
                minutes = int(msg["text"].strip())
                send_text(f"Got it — ~{minutes} min.")
                print(f"[telegram] Duration (custom): ~{minutes} min")
                return minutes

    print("[telegram] No duration input — defaulting to 20 min.")
    return 20


def send_schedule_prompt(token: str):
    """Send preset schedule buttons + Custom option. Times are IST."""
    now = datetime.now(IST)

    def _btn(label: str, day_offset: int, hour: int) -> dict:
        return {"text": label, "callback_data": f"SCH_{token}_{day_offset}_{hour}"}

    slots_today = []
    for h, label in [(9, "9 AM"), (12, "12 PM"), (18, "6 PM"), (21, "9 PM")]:
        t = now.replace(hour=h, minute=0, second=0, microsecond=0)
        if t > now:
            slots_today.append(_btn(f"Today {label}", 0, h))

    slots_tomorrow = [_btn("Tomorrow 9 AM", 1, 9)]
    all_btns = slots_today + slots_tomorrow
    rows = [all_btns[i:i+2] for i in range(0, len(all_btns), 2)]
    rows.append([{"text": "✏️ Custom", "callback_data": f"SCH_{token}_custom"}])
    rows.append([{"text": "⚡ Publish Now", "callback_data": f"PUB_NOW_{token}"}])

    requests.post(_url("sendMessage"), json={
        "chat_id":      CHAT_ID,
        "parse_mode":   "HTML",
        "text":         "<b>When to publish?</b>\n<i>No tap in 3h = Publish Now</i>",
        "reply_markup": json.dumps({"inline_keyboard": rows}),
    }, timeout=15).raise_for_status()


def wait_for_schedule(token: str, timeout_seconds: int = 10800) -> str | None:
    """Poll for schedule tap or typed offset. Returns RFC3339 IST string or None."""
    deadline = time.time() + timeout_seconds
    try:
        r = requests.get(_url("getUpdates"), params={"limit": 1, "offset": -1}, timeout=10)
        results = r.json().get("result", [])
        offset = results[-1]["update_id"] + 1 if results else 0
    except Exception:
        offset = 0

    print("[telegram] Waiting up to 3h for schedule tap...")
    custom_mode = False  # True after Custom tap — next text message is minutes from now

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
            cq   = upd.get("callback_query", {})
            data = cq.get("data", "")
            msg  = upd.get("message", {})

            if data == f"PUB_NOW_{token}":
                requests.post(_url("answerCallbackQuery"), json={
                    "callback_query_id": cq["id"], "text": "Publishing now!",
                }, timeout=5)
                print("[telegram] Schedule: Publish Now")
                return None

            if data.startswith(f"SCH_{token}_") and not data.endswith("_custom"):
                parts = data.split("_")
                day_offset, hour = parts[-2], parts[-1]
                dt = (datetime.now(IST).replace(hour=int(hour), minute=0, second=0, microsecond=0)
                      + timedelta(days=int(day_offset)))
                label = dt.strftime("%d %b %Y %I:%M %p") + " IST"
                requests.post(_url("answerCallbackQuery"), json={
                    "callback_query_id": cq["id"], "text": f"Scheduled for {label}",
                }, timeout=5)
                print(f"[telegram] Schedule: {dt.isoformat()}")
                return dt.isoformat()

            if data == f"SCH_{token}_custom":
                requests.post(_url("answerCallbackQuery"), json={
                    "callback_query_id": cq["id"], "text": "Type minutes from now.",
                }, timeout=5)
                send_text("Type minutes from now to schedule (e.g. 45 or 120):")
                custom_mode = True

            if custom_mode and msg.get("text", "").strip().isdigit():
                minutes = int(msg["text"].strip())
                dt = datetime.now(IST) + timedelta(minutes=minutes)
                label = dt.strftime("%d %b %Y %I:%M %p") + " IST"
                send_text(f"Scheduled for {label}.")
                print(f"[telegram] Schedule (custom): +{minutes}min → {dt.isoformat()}")
                return dt.isoformat()

    print("[telegram] No schedule tap in 3h — publishing now.")
    return None


def new_token() -> str:
    return uuid.uuid4().hex[:10].upper()
