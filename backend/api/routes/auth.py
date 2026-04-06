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


class KTXLoginRequest(BaseModel):
    ktx_id: str
    ktx_password: str


@router.post("/login")
async def login(body: LoginRequest):
    client = SRTClient(body.srt_id, body.srt_password)
    try:
        await asyncio.wait_for(
            asyncio.to_thread(client._get_client),
            timeout=30,
        )
    except asyncio.TimeoutError:
        raise HTTPException(408, "SRT 로그인 시간 초과: 서버 응답 없음")
    except Exception as e:
        raise HTTPException(401, f"SRT 로그인 실패: {repr(e)}")
    finally:
        try:
            await asyncio.to_thread(client._logout)
        except Exception:
            pass

    auth.login(body.srt_id, body.srt_password)
    return {"ok": True}


@router.post("/logout")
async def logout(db: Session = Depends(get_db)):
    poller.stop_all_polling()
    db.query(Ticket).delete()
    db.commit()
    auth.logout()
    logger.info("로그아웃 완료: 모든 폴링 중지 및 티켓 삭제")
    return {"ok": True}


@router.get("/status")
def status():
    creds = auth.get_credentials()
    ktx_creds = auth.get_ktx_credentials()
    return {
        "logged_in": auth.is_logged_in(),
        "srt_id": creds["srt_id"] if creds else None,
        "ktx_logged_in": auth.is_ktx_logged_in(),
        "ktx_id": ktx_creds["ktx_id"] if ktx_creds else None,
    }


@router.post("/ktx/login")
async def ktx_login(body: KTXLoginRequest):
    try:
        from backend.core.ktx_client import PatchedKorail, _check_dependencies
        _check_dependencies()

        def _do_login():
            client = PatchedKorail(body.ktx_id, body.ktx_password)
            if not client.logined:
                raise Exception("로그인 실패: ID/PW를 확인하세요.")
            return client

        await asyncio.wait_for(asyncio.to_thread(_do_login), timeout=30)
    except asyncio.TimeoutError:
        raise HTTPException(408, "KTX 로그인 시간 초과: 서버 응답 없음")
    except ImportError as e:
        raise HTTPException(503, f"KTX 기능 사용 불가: {e}")
    except Exception as e:
        raise HTTPException(401, f"KTX 로그인 실패: {repr(e)}")

    auth.ktx_login(body.ktx_id, body.ktx_password)
    return {"ok": True}


@router.post("/ktx/logout")
def ktx_logout():
    auth.ktx_logout()
    return {"ok": True}


@router.get("/ktx/status")
def ktx_status():
    ktx_creds = auth.get_ktx_credentials()
    return {
        "ktx_logged_in": auth.is_ktx_logged_in(),
        "ktx_id": ktx_creds["ktx_id"] if ktx_creds else None,
    }
