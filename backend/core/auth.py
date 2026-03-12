"""SRT credential store using OS keychain (macOS Keychain / Windows Credential Manager)."""

import json
import logging
import concurrent.futures

import keyring

logger = logging.getLogger(__name__)

SERVICE_NAME = "Tessera"
ACCOUNT_NAME = "srt_credentials"

_credentials: dict[str, str] | None = None

# 키체인 작업 타임아웃 (초)
_KEYCHAIN_TIMEOUT = 3


def _run_with_timeout(fn, *args, timeout=_KEYCHAIN_TIMEOUT):
    """키체인 작업을 별도 스레드에서 타임아웃과 함께 실행."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(fn, *args)
        return future.result(timeout=timeout)


def _save_to_keychain(srt_id: str, srt_password: str) -> None:
    try:
        data = json.dumps({"srt_id": srt_id, "srt_password": srt_password})
        _run_with_timeout(keyring.set_password, SERVICE_NAME, ACCOUNT_NAME, data)
        logger.info("자격증명 키체인에 저장 완료")
    except Exception as e:
        logger.warning(f"키체인 저장 실패: {repr(e)}")


def _load_from_keychain() -> dict[str, str] | None:
    try:
        data = _run_with_timeout(keyring.get_password, SERVICE_NAME, ACCOUNT_NAME)
        if data:
            creds = json.loads(data)
            if creds.get("srt_id") and creds.get("srt_password"):
                return creds
    except Exception as e:
        logger.warning(f"키체인 로드 실패: {repr(e)}")
    return None


def _delete_from_keychain() -> None:
    try:
        _run_with_timeout(keyring.delete_password, SERVICE_NAME, ACCOUNT_NAME)
        logger.info("키체인에서 자격증명 삭제 완료")
    except Exception as e:
        logger.warning(f"키체인 삭제 실패: {repr(e)}")


def login(srt_id: str, srt_password: str) -> None:
    global _credentials
    _credentials = {"srt_id": srt_id, "srt_password": srt_password}
    _save_to_keychain(srt_id, srt_password)
    logger.info(f"SRT 로그인 정보 저장: {srt_id}")


def logout() -> None:
    global _credentials
    _credentials = None
    _delete_from_keychain()
    logger.info("SRT 로그인 정보 제거")


def get_credentials() -> dict[str, str] | None:
    return _credentials


def is_logged_in() -> bool:
    return _credentials is not None


def restore_from_keychain() -> bool:
    """서버 시작 시 키체인에서 자격증명 복원. 성공 시 True."""
    global _credentials
    creds = _load_from_keychain()
    if creds:
        _credentials = creds
        logger.info(f"키체인에서 자격증명 복원: {creds['srt_id']}")
        return True
    return False
