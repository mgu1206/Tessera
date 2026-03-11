import asyncio
import logging

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.core import auth, poller
from backend.core.srt_client import SRTClient
from backend.db.database import get_db
from backend.db.models import Ticket

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    srt_id: str
    srt_password: str


@router.post("/login")
async def login(body: LoginRequest):
    # Validate credentials by attempting SRT login
    client = SRTClient(body.srt_id, body.srt_password)
    try:
        await asyncio.to_thread(client._get_client)
    except Exception as e:
        raise HTTPException(401, f"SRT 로그인 실패: {repr(e)}")
    finally:
        try:
            client._logout()
        except Exception:
            pass

    auth.login(body.srt_id, body.srt_password)
    return {"ok": True}


@router.post("/logout")
async def logout(db: Session = Depends(get_db)):
    poller.stop_all_polling()

    # Delete all tickets from DB
    db.query(Ticket).delete()
    db.commit()

    auth.logout()
    logger.info("로그아웃 완료: 모든 폴링 중지 및 티켓 삭제")
    return {"ok": True}


@router.get("/status")
def status():
    creds = auth.get_credentials()
    return {
        "logged_in": auth.is_logged_in(),
        "srt_id": creds["srt_id"] if creds else None,
    }
