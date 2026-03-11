import asyncio
import logging

import httpx

from backend.core import notification_settings

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org"


def _format_time(raw: str) -> str:
    if len(raw) >= 4:
        return f"{raw[:2]}:{raw[2:4]}"
    return raw


async def _send_telegram(text: str) -> None:
    enabled, token, chat_id = notification_settings.get_telegram()
    if not enabled or not token or not chat_id:
        return

    url = f"{TELEGRAM_API}/bot{token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json={"chat_id": chat_id, "text": text})
            if not resp.json().get("ok"):
                logger.warning(f"Telegram 전송 실패: {resp.text}")
    except Exception as e:
        logger.error(f"Telegram 전송 오류: {repr(e)}")


async def _send_imessage(text: str) -> None:
    enabled, recipients = notification_settings.get_imessage()
    if not enabled or not recipients:
        return

    # Escape quotes in text for AppleScript
    safe_text = text.replace('\\', '\\\\').replace('"', '\\"')

    for recipient in recipients:
        script = (
            'tell application "Messages"\n'
            '    set targetService to 1st account whose service type = iMessage\n'
            f'    set targetBuddy to participant "{recipient}" of targetService\n'
            f'    send "{safe_text}" to targetBuddy\n'
            'end tell'
        )
        try:
            proc = await asyncio.create_subprocess_exec(
                "osascript", "-e", script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()
            if proc.returncode != 0:
                logger.warning(f"iMessage 전송 실패 ({recipient}): {stderr.decode().strip()}")
        except Exception as e:
            logger.error(f"iMessage 전송 오류 ({recipient}): {repr(e)}")


async def _notify(text: str) -> None:
    await asyncio.gather(
        _send_telegram(text),
        _send_imessage(text),
        return_exceptions=True,
    )


async def notify_success(data: dict) -> None:
    info = data.get("reservation_info") or {}
    ticket_id = data.get("ticket_id", "?")
    dep = info.get("dep_station_name", data.get("dep", "?"))
    arr = info.get("arr_station_name", data.get("arr", "?"))
    dep_time = _format_time(info.get("dep_time", "?"))
    arr_time = _format_time(info.get("arr_time", "?"))
    total_cost = info.get("total_cost", "?")
    price_str = f"{total_cost:,}원" if isinstance(total_cost, (int, float)) else str(total_cost)
    train = f"{info.get('train_name', '')} {info.get('train_number', '')}".strip()
    payment_date = info.get("payment_date", "?")
    payment_time = _format_time(info.get("payment_time", "?"))

    text = (
        f"[티켓 #{ticket_id}] 예매 성공!\n"
        f"{dep} → {arr}\n"
        f"{train} | 출발 {dep_time} / 도착 {arr_time}\n"
        f"{price_str} | 결제기한 {payment_date} {payment_time}"
    )
    await _notify(text)


async def notify_failed(data: dict) -> None:
    ticket_id = data.get("ticket_id", "?")
    reason = data.get("reason", "알 수 없음")
    await _notify(f"[티켓 #{ticket_id}] 예매 실패\n사유: {reason}")


async def notify_created(data: dict) -> None:
    ticket_id = data.get("ticket_id", "?")
    dep = data.get("dep", "?")
    arr = data.get("arr", "?")
    raw_date = data.get("date", "")
    date_str = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}" if len(raw_date) == 8 else raw_date
    time_str = _format_time(data.get("time", ""))
    await _notify(
        f"[티켓 #{ticket_id}] 예매 시도를 시작합니다.\n"
        f"{dep} → {arr} | {date_str} {time_str}~"
    )
