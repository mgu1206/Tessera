import asyncio
import json
import logging

import httpx
from telegram import Bot

from tgbot.config import settings

logger = logging.getLogger(__name__)


def _format_time(raw: str) -> str:
    if len(raw) >= 4:
        return f"{raw[:2]}:{raw[2:4]}"
    return raw


def _format_event(event_type: str, data: dict) -> str | None:
    ticket_id = data.get("ticket_id", "?")

    if event_type == "ticket.created":
        dep = data.get("dep", "?")
        arr = data.get("arr", "?")
        raw_date = data.get("date", "")
        date_str = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}" if len(raw_date) == 8 else raw_date
        raw_time = data.get("time", "")
        time_str = _format_time(raw_time)
        seat_type = data.get("seat_type", "GENERAL_FIRST")
        seat_labels = {
            "GENERAL_FIRST": "일반실",
            "GENERAL_ONLY": "일반실",
            "SPECIAL_FIRST": "특실",
            "SPECIAL_ONLY": "특실",
        }
        seat = seat_labels.get(seat_type, "일반실")
        passengers = data.get("passengers", {})
        pax_parts = []
        if passengers.get("adult", 0) > 0:
            pax_parts.append(f"성인 {passengers['adult']}명")
        if passengers.get("child", 0) > 0:
            pax_parts.append(f"어린이 {passengers['child']}명")
        if passengers.get("senior", 0) > 0:
            pax_parts.append(f"경로 {passengers['senior']}명")
        pax_str = ", ".join(pax_parts) if pax_parts else "성인 1명"
        return (
            f"[티켓 #{ticket_id}] 예매 시도를 시작합니다.\n"
            f"{dep} → {arr} | {date_str} {time_str}~\n"
            f"{seat} / {pax_str}"
        )

    if event_type == "ticket.polling":
        attempt_count = data.get("attempt_count", "?")
        created_at = data.get("created_at", "")
        elapsed_str = "?"
        if created_at:
            try:
                from datetime import datetime
                created = datetime.fromisoformat(created_at)
                elapsed_minutes = int((datetime.utcnow() - created).total_seconds() / 60)
                elapsed_str = str(elapsed_minutes)
            except Exception:
                pass
        return (
            f"[티켓 #{ticket_id}] 진행 중\n"
            f"경과: {elapsed_str}분 | 시도: {attempt_count}회\n"
            f"상태: 잔여석 없음, 계속 시도 중..."
        )

    if event_type == "ticket.success":
        info = data.get("reservation_info", {}) or {}
        dep = info.get("dep_station_name", data.get("dep", "?"))
        arr = info.get("arr_station_name", data.get("arr", "?"))
        dep_time = _format_time(info.get("dep_time", "?"))
        arr_time = _format_time(info.get("arr_time", "?"))
        total_cost = info.get("total_cost", "?")
        if isinstance(total_cost, (int, float)):
            price_str = f"{total_cost:,}원"
        else:
            price_str = str(total_cost)
        payment_date = info.get("payment_date", "?")
        payment_time = _format_time(info.get("payment_time", "?"))
        return (
            f"[티켓 #{ticket_id}] 예매 성공!\n"
            f"{dep} → {arr}\n"
            f"출발 {dep_time} / 도착 {arr_time}\n"
            f"{price_str} | 결제기한 {payment_date} {payment_time}"
        )

    if event_type == "ticket.failed":
        reason = data.get("reason", "알 수 없음")
        return f"[티켓 #{ticket_id}] 예매 실패\n사유: {reason}"

    if event_type == "ticket.cancelled":
        return f"[티켓 #{ticket_id}] 취소됨"

    return None


async def listen_events(bot: Bot, chat_id: str) -> None:
    url = f"{settings.backend_url}/api/events"

    while True:
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("GET", url) as resp:
                    resp.raise_for_status()
                    event_type = None
                    async for line in resp.aiter_lines():
                        if line.startswith("event:"):
                            event_type = line[len("event:"):].strip()
                        elif line.startswith("data:"):
                            raw_data = line[len("data:"):].strip()
                            if event_type and raw_data:
                                try:
                                    data = json.loads(raw_data)
                                except json.JSONDecodeError:
                                    logger.warning("Invalid JSON in SSE data: %s", raw_data)
                                    continue
                                message = _format_event(event_type, data)
                                if message:
                                    await bot.send_message(chat_id=chat_id, text=message)
                            event_type = None
                        elif line == "":
                            event_type = None
        except Exception:
            logger.exception("SSE connection error, reconnecting in 5 seconds")
        await asyncio.sleep(5)
