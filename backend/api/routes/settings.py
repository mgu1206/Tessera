import logging
import asyncio

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.core import notification_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["settings"])

TELEGRAM_API = "https://api.telegram.org"


class SettingsUpdate(BaseModel):
    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    imessage_enabled: bool = False
    imessage_recipients: list[str] = []
    poll_interval_seconds: int = 5
    report_interval_seconds: int = 300
    max_attempts: int = 0


@router.get("")
def get_settings():
    return notification_settings.get_all()


@router.put("")
def update_settings(body: SettingsUpdate):
    return notification_settings.update(body.model_dump())


@router.post("/notifications/test/telegram")
async def test_telegram():
    _, token, chat_id = notification_settings.get_telegram()
    if not token or not chat_id:
        raise HTTPException(400, "텔레그램 봇 토큰 또는 Chat ID가 설정되지 않았습니다.")

    url = f"{TELEGRAM_API}/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "[Tessera] 텔레그램 알림 테스트입니다.\n이 메시지가 보이면 알림이 정상 작동합니다.",
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            data = resp.json()
            if not data.get("ok"):
                desc = data.get("description", "알 수 없는 오류")
                raise HTTPException(502, f"Telegram API 오류: {desc}")
            return {"ok": True}
    except httpx.HTTPError as e:
        raise HTTPException(502, f"텔레그램 요청 실패: {repr(e)}")


@router.post("/notifications/test/imessage")
async def test_imessage():
    enabled, recipients = notification_settings.get_imessage()
    if not enabled or not recipients:
        raise HTTPException(400, "iMessage 수신자가 설정되지 않았습니다.")

    errors = []
    for recipient in recipients:
        script = (
            'tell application "Messages"\n'
            '    set targetService to 1st account whose service type = iMessage\n'
            f'    set targetBuddy to participant "{recipient}" of targetService\n'
            '    send "[Tessera] iMessage 알림 테스트입니다." to targetBuddy\n'
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
                errors.append(f"{recipient}: {stderr.decode().strip()}")
        except Exception as e:
            errors.append(f"{recipient}: {repr(e)}")

    if errors:
        raise HTTPException(502, f"일부 iMessage 전송 실패: {'; '.join(errors)}")
    return {"ok": True}
