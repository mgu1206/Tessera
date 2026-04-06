from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import Ticket

router = APIRouter(prefix="/api/groups", tags=["groups"])


def _ticket_to_brief(t: Ticket) -> dict:
    return {
        "ticket_id": t.id,
        "train_type": t.train_type or "SRT",
        "dep": t.dep,
        "arr": t.arr,
        "date": t.date,
        "time": t.time,
        "seat_type": t.seat_type,
        "status": t.status,
        "group_id": t.group_id,
        "manually_completed": bool(t.manually_completed),
        "reservation_info": t.reservation_info,
    }


@router.get("")
def list_groups(db: Session = Depends(get_db)):
    """그룹 ID별로 티켓을 묶어 반환."""
    tickets = db.query(Ticket).filter(Ticket.group_id.isnot(None)).order_by(Ticket.created_at.desc()).all()

    groups: dict[str, list] = {}
    for t in tickets:
        gid = t.group_id
        if gid not in groups:
            groups[gid] = []
        groups[gid].append(_ticket_to_brief(t))

    return [{"group_id": gid, "tickets": ticket_list} for gid, ticket_list in groups.items()]


@router.delete("/{group_id}")
async def delete_group(group_id: str, db: Session = Depends(get_db)):
    """그룹을 삭제 (티켓들의 group_id를 NULL로 초기화)."""
    tickets = db.query(Ticket).filter(Ticket.group_id == group_id).all()
    if not tickets:
        raise HTTPException(404, f"그룹 '{group_id}'를 찾을 수 없습니다.")

    for t in tickets:
        t.group_id = None
    db.commit()
    return {"ok": True, "ungrouped": len(tickets)}
