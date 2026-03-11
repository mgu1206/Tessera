import datetime
import random
import string

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.core import poller
from backend.core.event_bus import event_bus
from backend.core.srt_client import STATIONS
from backend.db.database import get_db
from backend.db.models import Ticket

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


class PassengersIn(BaseModel):
    adult: int = 1
    child: int = 0
    senior: int = 0


class TicketCreate(BaseModel):
    dep: str
    arr: str
    date: str
    time: str
    time_limit: str | None = None
    seat_type: str = "GENERAL_FIRST"
    passengers: PassengersIn = PassengersIn()


def _generate_id(db: Session) -> str:
    chars = string.ascii_uppercase + string.digits
    while True:
        tid = "".join(random.choices(chars, k=4))
        if not db.query(Ticket).filter(Ticket.id == tid).first():
            return tid


def _to_dict(t: Ticket) -> dict:
    return {
        "ticket_id": t.id,
        "dep": t.dep,
        "arr": t.arr,
        "date": t.date,
        "time": t.time,
        "time_limit": t.time_limit,
        "seat_type": t.seat_type,
        "passengers": t.passengers,
        "status": t.status,
        "attempt_count": t.attempt_count,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "reserved_at": t.reserved_at.isoformat() if t.reserved_at else None,
        "reservation_info": t.reservation_info,
        "last_searched_at": t.last_searched_at.isoformat() if t.last_searched_at else None,
        "last_search_results": t.last_search_results,
    }


@router.get("")
def list_tickets(db: Session = Depends(get_db)):
    tickets = db.query(Ticket).order_by(Ticket.created_at.desc()).all()
    return [_to_dict(t) for t in tickets]


@router.post("", status_code=201)
async def create_ticket(body: TicketCreate, db: Session = Depends(get_db)):
    if body.dep not in STATIONS:
        raise HTTPException(400, f"출발역 '{body.dep}'은 SRT 지원 역이 아닙니다.")
    if body.arr not in STATIONS:
        raise HTTPException(400, f"도착역 '{body.arr}'은 SRT 지원 역이 아닙니다.")
    if body.dep == body.arr:
        raise HTTPException(400, "출발역과 도착역이 같습니다.")
    total = body.passengers.adult + body.passengers.child + body.passengers.senior
    if total < 1:
        raise HTTPException(400, "승객이 최소 1명 이상이어야 합니다.")
    if total > 9:
        raise HTTPException(400, "승객은 최대 9명까지 가능합니다.")

    tid = _generate_id(db)
    ticket = Ticket(
        id=tid,
        dep=body.dep,
        arr=body.arr,
        date=body.date,
        time=body.time,
        time_limit=body.time_limit,
        seat_type=body.seat_type,
        passengers=body.passengers.model_dump(),
        status="POLLING",
        attempt_count=0,
        created_at=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))),
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    poller.start_polling(tid)
    await event_bus.publish("ticket.created", _to_dict(ticket))
    return _to_dict(ticket)


@router.get("/{ticket_id}")
def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(404, "티켓을 찾을 수 없습니다.")
    return _to_dict(ticket)


@router.delete("/{ticket_id}")
async def cancel_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(404, "티켓을 찾을 수 없습니다.")

    if ticket.status in ("POLLING", "PENDING"):
        poller.stop_polling(ticket_id)
        ticket.status = "CANCELLED"
        db.commit()
        await event_bus.publish("ticket.cancelled", {"ticket_id": ticket_id})
    else:
        db.delete(ticket)
        db.commit()
        await event_bus.publish("ticket.deleted", {"ticket_id": ticket_id})

    return {"ok": True}
