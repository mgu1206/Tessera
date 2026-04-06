"""SRT/KTX credential store using OS keychain (macOS Keychain / Windows Credential Manager)."""

import json
import logging
import concurrent.futures

import keyring

logger = logging.getLogger(__name__)

SERVICE_NAME = "Tessera"
ACCOUNT_NAME = "srt_credentials"
KTX_ACCOUNT_NAME = "ktx_credentials"

_credentials: dict[str, str] | None = None
_ktx_credentials: dict[str, str] | None = None

# 키체인 작업 타임아웃 (초)
_KEYCHAIN_TIMEOUT = 3


def _run_with_timeout(fn, *args, timeout=_KEYCHAIN_TIMEOUT):
    """키체인 작업을 별도 스레드에서 타임아웃과 함께 실행."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(fn, *args)
        return future.result(timeout=timeout)


def _save_to_keychain(account: str, data: dict) -> None:
    try:
        _run_with_timeout(keyring.set_password, SERVICE_NAME, account, json.dumps(data))
        logger.info(f"자격증명 키체인에 저장 완료: {account}")
    except Exception as e:
        logger.warning(f"키체인 저장 실패 ({account}): {repr(e)}")


def _load_from_keychain(account: str) -> dict | None:
    try:
        data = _run_with_timeout(keyring.get_password, SERVICE_NAME, account)
        if data:
            return json.loads(data)
    except Exception as e:
        logger.warning(f"키체인 로드 실패 ({account}): {repr(e)}")
    return None


def _delete_from_keychain(account: str) -> None:
    try:
        _run_with_timeout(keyring.delete_password, SERVICE_NAME, account)
        logger.info(f"키체인에서 삭제 완료: {account}")
    except Exception as e:
        logger.warning(f"키체인 삭제 실패 ({account}): {repr(e)}")


# SRT auth
def login(srt_id: str, srt_password: str) -> None:
    global _credentials
    _credentials = {"srt_id": srt_id, "srt_password": srt_password}
    _save_to_keychain(ACCOUNT_NAME, _credentials)
    logger.info(f"SRT 로그인 정보 저장: {srt_id}")


def logout() -> None:
    global _credentials
    _credentials = None
    _delete_from_keychain(ACCOUNT_NAME)
    logger.info("SRT 로그인 정보 제거")


def get_credentials() -> dict[str, str] | None:
    return _credentials


def is_logged_in() -> bool:
    return _credentials is not None


def restore_from_keychain() -> bool:
    global _credentials
    creds = _load_from_keychain(ACCOUNT_NAME)
    if creds and creds.get("srt_id") and creds.get("srt_password"):
        _credentials = creds
        logger.info(f"키체인에서 SRT 자격증명 복원: {creds['srt_id']}")
        return True
    return False


# KTX auth
def ktx_login(ktx_id: str, ktx_password: str) -> None:
    global _ktx_credentials
    _ktx_credentials = {"ktx_id": ktx_id, "ktx_password": ktx_password}
    _save_to_keychain(KTX_ACCOUNT_NAME, _ktx_credentials)
    logger.info(f"KTX 로그인 정보 저장: {ktx_id}")


def ktx_logout() -> None:
    global _ktx_credentials
    _ktx_credentials = None
    _delete_from_keychain(KTX_ACCOUNT_NAME)
    logger.info("KTX 로그인 정보 제거")


def get_ktx_credentials() -> dict[str, str] | None:
    return _ktx_credentials


def is_ktx_logged_in() -> bool:
    return _ktx_credentials is not None


def restore_ktx_from_keychain() -> bool:
    global _ktx_credentials
    creds = _load_from_keychain(KTX_ACCOUNT_NAME)
    if creds and creds.get("ktx_id") and creds.get("ktx_password"):
        _ktx_credentials = creds
        logger.info(f"키체인에서 KTX 자격증명 복원: {creds['ktx_id']}")
        return True
    return False
