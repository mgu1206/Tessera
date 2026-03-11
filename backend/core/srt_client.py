import asyncio
import logging
import time
from SRT import SRT
from SRT.passenger import Adult, Child, Senior
from SRT.errors import SRTNotLoggedInError, SRTResponseError
try:
    from SRT.seat_type import SeatType
except ImportError:
    from SRT.constants import SeatType

logger = logging.getLogger(__name__)

SEAT_TYPE_MAP = {
    "GENERAL_FIRST": SeatType.GENERAL_FIRST,
    "GENERAL_ONLY": SeatType.GENERAL_ONLY,
    "SPECIAL_FIRST": SeatType.SPECIAL_FIRST,
    "SPECIAL_ONLY": SeatType.SPECIAL_ONLY,
}

STATIONS = [
    "수서", "동탄", "평택지제", "천안아산", "오송", "대전", "김천(구미)",
    "동대구", "서대구", "신경주", "경주", "울산(통도사)", "부산",
    "공주", "익산", "전주", "정읍", "광주송정", "나주", "목포",
    "여수EXPO", "여천", "순천", "곡성", "구례구", "남원", "밀양",
    "창원중앙", "창원", "마산", "진영", "진주", "포항",
]

# 세션 자동 갱신 주기 (초)
SESSION_REFRESH_INTERVAL = 300


def build_passengers(passengers: dict) -> list:
    result = []
    if passengers.get("adult", 0) > 0:
        result.append(Adult(count=passengers["adult"]))
    if passengers.get("child", 0) > 0:
        result.append(Child(count=passengers["child"]))
    if passengers.get("senior", 0) > 0:
        result.append(Senior(count=passengers["senior"]))
    return result or [Adult()]


class SRTClient:
    def __init__(self, srt_id: str, srt_password: str):
        self.srt_id = srt_id
        self.srt_password = srt_password
        self._srt: SRT | None = None
        self._login_time: float = 0

    def _get_client(self) -> SRT:
        if self._srt is None:
            logger.info("SRT 로그인 시도")
            self._srt = SRT(self.srt_id, self.srt_password)
            self._login_time = time.monotonic()
            logger.info("SRT 로그인 성공")
        return self._srt

    def _logout(self):
        if self._srt is not None:
            try:
                self._srt.logout()
                logger.info("SRT 로그아웃 완료")
            except Exception:
                pass
        self._srt = None
        self._login_time = 0

    def _refresh_if_needed(self):
        """주기적으로 로그아웃 후 재로그인하여 세션 만료를 방지한다."""
        if self._srt is not None and (time.monotonic() - self._login_time) >= SESSION_REFRESH_INTERVAL:
            logger.info("세션 갱신: 주기적 로그아웃/재로그인")
            self._logout()
            self._get_client()

    async def search_train(
        self,
        dep: str,
        arr: str,
        date: str,
        time_: str,
        time_limit: str | None = None,
    ):
        """모든 열차를 조회한다 (available_only=False)."""
        def _search():
            self._refresh_if_needed()
            srt = self._get_client()
            return srt.search_train(
                dep, arr, date, time_,
                time_limit=time_limit,
                available_only=False,
            )

        try:
            return await asyncio.to_thread(_search)
        except (SRTNotLoggedInError, SRTResponseError) as e:
            logger.warning(f"search_train 세션 오류, 재로그인 후 재시도: {e}")
            self._logout()
            try:
                return await asyncio.to_thread(_search)
            except Exception:
                self._logout()
                raise
        except Exception:
            self._logout()
            raise

    async def reserve(self, train, passengers: dict, seat_type: str):
        def _reserve():
            srt = self._get_client()
            pax = build_passengers(passengers)
            st = SEAT_TYPE_MAP.get(seat_type, SeatType.GENERAL_FIRST)
            return srt.reserve(train, passengers=pax, special_seat=st)

        try:
            return await asyncio.to_thread(_reserve)
        except (SRTNotLoggedInError, SRTResponseError) as e:
            logger.warning(f"reserve 세션 오류, 재로그인: {e}")
            self._logout()
            raise
        except Exception:
            self._logout()
            raise
