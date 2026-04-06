import asyncio
import datetime
import logging
import math
import random

KST = datetime.timezone(datetime.timedelta(hours=9))

from backend.core import auth
from backend.core import notification_settings
from backend.core.event_bus import event_bus
from backend.core.notifier import notify_success, notify_failed
from backend.core.srt_client import SRTClient
from backend.db.database import SessionLocal
from backend.db.models import Ticket

logger = logging.getLogger(__name__)

_tasks: dict[str, asyncio.Task] = {}

_INTERVAL_MIN = 1.0
_INTERVAL_MAX = 30.0


def _calc_interval(ticket_date: str) -> float:
    try:
        target = datetime.datetime.strptime(ticket_date, "%Y%m%d").replace(tzinfo=KST)
    except ValueError:
        return random.uniform(_INTERVAL_MIN, _INTERVAL_MAX)

    now = datetime.datetime.now(KST)
    hours_left = max((target - now).total_seconds() / 3600, 0)

    scale = math.log(hours_left + 1) / math.log(721)
    scale = min(scale, 1.0)

    base_min = _INTERVAL_MIN + (_INTERVAL_MAX * 0.4) * scale
    base_max = _INTERVAL_MIN + _INTERVAL_MAX * scale
    base_max = max(base_max, base_min + 0.5)

    return random.uniform(base_min, base_max)


def _is_seat_available(train, train_type: str) -> bool:
    """열차 타입에 따라 좌석 가용 여부 확인."""
    if train_type == "KTX":
        if hasattr(train, "has_seat"):
            return train.has_seat()
        return False
    else:
        if hasattr(train, "seat_available"):
            return train.seat_available()
        return False


def _train_to_dict(train, train_type: str = "SRT") -> dict:
    if train_type == "KTX":
        general_avail = train.has_general_seat() if hasattr(train, "has_general_seat") else False
        special_avail = train.has_special_seat() if hasattr(train, "has_special_seat") else False
        return {
            "train_name": getattr(train, "train_name", "KTX"),
            "train_number": getattr(train, "train_no", getattr(train, "train_number", "")),
            "dep_time": getattr(train, "dep_time", ""),
            "arr_time": getattr(train, "arr_time", ""),
            "general_seat": "예약가능" if general_avail else "매진",
            "special_seat": "예약가능" if special_avail else "매진",
            "general_available": general_avail,
            "special_available": special_avail,
        }
    else:
        return {
            "train_name": getattr(train, "train_name", ""),
            "train_number": getattr(train, "train_number", ""),
            "dep_time": getattr(train, "dep_time", ""),
            "arr_time": getattr(train, "arr_time", ""),
            "general_seat": getattr(train, "general_seat_state", ""),
            "special_seat": getattr(train, "special_seat_state", ""),
            "general_available": train.general_seat_available() if hasattr(train, "general_seat_available") else False,
            "special_available": train.special_seat_available() if hasattr(train, "special_seat_available") else False,
        }


def _ticket_to_dict(ticket: Ticket) -> dict:
    return {
        "ticket_id": ticket.id,
        "train_type": ticket.train_type or "SRT",
        "dep": ticket.dep,
        "arr": ticket.arr,
        "date": ticket.date,
        "time": ticket.time,
        "time_limit": ticket.time_limit,
        "seat_type": ticket.seat_type,
        "passengers": ticket.passengers,
        "status": ticket.status,
        "attempt_count": ticket.attempt_count,
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        "reserved_at": ticket.reserved_at.isoformat() if ticket.reserved_at else None,
        "reservation_info": ticket.reservation_info,
        "last_searched_at": ticket.last_searched_at.isoformat() if ticket.last_searched_at else None,
        "last_search_results": ticket.last_search_results,
        "group_id": ticket.group_id,
        "manually_completed": bool(ticket.manually_completed),
    }


def _extract_ktx_reservation_info(reservation) -> dict:
    """korail2 Reservation 객체에서 예매 정보 추출."""
    return {
        "reservation_number": getattr(reservation, "rsv_id", getattr(reservation, "h_pnr_no", "")),
        "total_cost": getattr(reservation, "total_cost", 0),
        "train_name": getattr(reservation, "train_name", "KTX"),
        "train_number": getattr(reservation, "train_no", getattr(reservation, "train_number", "")),
        "dep_time": getattr(reservation, "dep_time", ""),
        "arr_time": getattr(reservation, "arr_time", ""),
        "dep_station_name": getattr(reservation, "dep_name", getattr(reservation, "dep_station_name", "")),
        "arr_station_name": getattr(reservation, "arr_name", getattr(reservation, "arr_station_name", "")),
        "payment_date": getattr(reservation, "buy_limit_date", getattr(reservation, "payment_date", "")),
        "payment_time": getattr(reservation, "buy_limit_time", getattr(reservation, "payment_time", "")),
    }


async def _poll(ticket_id: str):
    db = SessionLocal()
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            return
        train_type = ticket.train_type or "SRT"
    finally:
        db.close()

    if train_type == "KTX":
        creds = auth.get_ktx_credentials()
        if not creds:
            logger.warning(f"[{ticket_id}] KTX 로그인 정보 없음, 폴링 중단")
            return
        try:
            from backend.core.ktx_client import KTXClient
            client = KTXClient(creds["ktx_id"], creds["ktx_password"])
        except ImportError as e:
            logger.error(f"[{ticket_id}] KTXClient 로드 실패: {e}")
            return
    else:
        creds = auth.get_credentials()
        if not creds:
            logger.warning(f"[{ticket_id}] SRT 로그인 정보 없음, 폴링 중단")
            return
        client = SRTClient(creds["srt_id"], creds["srt_password"])

    last_report = datetime.datetime.now(KST)

    while True:
        db = SessionLocal()
        reserved = False
        ticket_date = None
        try:
            ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
            if not ticket or ticket.status in ("CANCELLED", "SUCCESS", "FAILED"):
                break
            ticket_date = ticket.date

            try:
                all_trains = await client.search_train(
                    ticket.dep, ticket.arr, ticket.date, ticket.time, ticket.time_limit
                )
                ticket.attempt_count += 1
                ticket.last_searched_at = datetime.datetime.now(KST)
                ticket.last_search_results = [_train_to_dict(t, train_type) for t in all_trains]
                db.commit()

                trains = [t for t in all_trains if _is_seat_available(t, train_type)]
                if trains:
                    for train in trains:
                        try:
                            reservation = await client.reserve(
                                train, ticket.passengers, ticket.seat_type
                            )
                        except asyncio.CancelledError:
                            raise
                        except Exception as e:
                            logger.warning(f"[{ticket_id}] reserve failed: {repr(e)}")
                            continue

                        ticket.status = "SUCCESS"
                        ticket.reserved_at = datetime.datetime.now(KST)

                        if train_type == "KTX":
                            ticket.reservation_info = _extract_ktx_reservation_info(reservation)
                        else:
                            ticket.reservation_info = {
                                "reservation_number": reservation.reservation_number,
                                "total_cost": reservation.total_cost,
                                "train_name": reservation.train_name,
                                "train_number": reservation.train_number,
                                "dep_time": reservation.dep_time,
                                "arr_time": reservation.arr_time,
                                "dep_station_name": reservation.dep_station_name,
                                "arr_station_name": reservation.arr_station_name,
                                "payment_date": reservation.payment_date,
                                "payment_time": reservation.payment_time,
                            }

                        db.commit()
                        ticket_data = _ticket_to_dict(ticket)
                        await event_bus.publish("ticket.success", ticket_data)
                        await notify_success(ticket_data)
                        reserved = True
                        break

                if reserved:
                    break

                now = datetime.datetime.now(KST)
                polling_cfg = notification_settings.get_polling()
                if (now - last_report).total_seconds() >= polling_cfg["report_interval_seconds"]:
                    await event_bus.publish("ticket.polling", _ticket_to_dict(ticket))
                    last_report = now

                if polling_cfg["max_attempts"] > 0 and ticket.attempt_count >= polling_cfg["max_attempts"]:
                    ticket.status = "FAILED"
                    db.commit()
                    failed_data = {**_ticket_to_dict(ticket), "reason": "최대 시도 횟수 초과"}
                    await event_bus.publish("ticket.failed", failed_data)
                    await notify_failed(failed_data)
                    break

            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"[{ticket_id}] polling error: {repr(e)}")
                db.rollback()

        finally:
            db.close()

        interval = _calc_interval(ticket_date) if ticket_date else random.uniform(_INTERVAL_MIN, _INTERVAL_MAX)
        await asyncio.sleep(interval)


def start_polling(ticket_id: str):
    task = asyncio.create_task(_poll(ticket_id))
    _tasks[ticket_id] = task
    task.add_done_callback(lambda _: _tasks.pop(ticket_id, None))


def stop_polling(ticket_id: str):
    task = _tasks.pop(ticket_id, None)
    if task:
        task.cancel()


def stop_all_polling():
    for ticket_id in list(_tasks.keys()):
        stop_polling(ticket_id)
    logger.info("모든 폴링 중지됨")


async def resume_polling():
    db = SessionLocal()
    try:
        tickets = db.query(Ticket).filter(Ticket.status == "POLLING").all()
        for ticket in tickets:
            if ticket.id not in _tasks:
                start_polling(ticket.id)
                logger.info(f"Resumed polling: {ticket.id}")
    finally:
        db.close()
