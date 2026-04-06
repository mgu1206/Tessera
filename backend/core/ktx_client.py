"""KTX (Korail) client using korail2 library with DynaPath anti-bot patch."""
from __future__ import annotations

import asyncio
import base64
import logging
import random
import string
import time

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = "Dalvik/2.1.0 (Linux; U; Android 14; SM-S928N Build/UP1A.231005.007)"

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    _CRYPTO_OK = True
except ImportError:
    AES = None  # type: ignore
    pad = None  # type: ignore
    _CRYPTO_OK = False

try:
    from korail2 import (
        AdultPassenger,
        ChildPassenger,
        SeniorPassenger,
        Korail,
        KorailError,
        NeedToLoginError,
        NoResultsError,
        Passenger,
        ReserveOption,
        SoldOutError,
    )
    import korail2.korail2 as korail_mod
    from functools import reduce
    _KORAIL_OK = True
    _KORAIL_IMPORT_ERROR = None
except ImportError as e:
    _KORAIL_OK = False
    _KORAIL_IMPORT_ERROR = e
    # 스텁 클래스: korail2 미설치 시 import 오류 방지
    class Korail:  # type: ignore
        pass
    class AdultPassenger:  # type: ignore
        pass
    class ChildPassenger:  # type: ignore
        pass
    class SeniorPassenger:  # type: ignore
        pass
    class Passenger:  # type: ignore
        pass
    class KorailError(Exception):  # type: ignore
        pass
    class NeedToLoginError(Exception):  # type: ignore
        pass
    class NoResultsError(Exception):  # type: ignore
        pass
    class SoldOutError(Exception):  # type: ignore
        pass
    class ReserveOption:  # type: ignore
        GENERAL_FIRST = "GENERAL_FIRST"
    korail_mod = None  # type: ignore
    def reduce(fn, it, init=0):  # type: ignore
        result = init
        for x in it:
            result = fn(result, x)
        return result

# 세션 자동 갱신 주기 (초)
SESSION_REFRESH_INTERVAL = 300

KTX_STATIONS = [
    # 경부선
    "서울", "용산", "광명", "수원", "천안아산", "오송", "대전", "김천구미",
    "동대구", "경주", "울산", "부산",
    # 호남선
    "익산", "전주", "정읍", "광주송정", "목포",
    # 전라선
    "순천", "여수EXPO",
    # 경전선
    "창원중앙", "창원", "마산", "진주",
    # 동해선
    "포항",
    # 강릉선
    "만종", "둔내", "평창", "진부", "강릉",
    # 경부선 추가
    "구포", "밀양",
]

SEAT_OPTION_MAP = {
    "GENERAL_FIRST": "GENERAL_FIRST",
    "GENERAL_ONLY": "GENERAL_ONLY",
    "SPECIAL_FIRST": "SPECIAL_FIRST",
    "SPECIAL_ONLY": "SPECIAL_ONLY",
}


def _check_dependencies():
    if not _CRYPTO_OK:
        raise ImportError("pycryptodome이 설치되지 않았습니다: pip install pycryptodome")
    if not _KORAIL_OK:
        raise ImportError(f"korail2가 설치되지 않았습니다: pip install korail2 ({_KORAIL_IMPORT_ERROR})")


class DynaPathMasterEngine:
    APP_ID = "com.korail.talk"
    AS_VALUE = "%5B38ff229cb34c7dda8e28220a2d750cce%5D"
    DEVICE_MODEL = "SM-S928N"
    OS_TYPE = "Android"
    SDK_VERSION = "v1"

    def __init__(self) -> None:
        self.table = "3FE9jgRD4KdCyuawklqGJYmvfMn15P7US8XbxeLQtWT6OicBAopINs2Vh0HZrz"
        self.i8 = 161
        self.i9 = 30
        self.i10 = 2
        self.app_start_ts = str(int(time.time() * 1000))

    def string2xa1s(self, data: str) -> list[int]:
        result: list[int] = []
        idx = 0
        while idx < len(data):
            codepoint = ord(data[idx])
            idx += 1
            if codepoint < 128:
                result.append(codepoint)
            elif codepoint < 2048:
                result.append(128 | ((codepoint >> 7) & 15))
                result.append(codepoint & 127)
            elif codepoint >= 262144:
                result.append(160)
                result.append((codepoint >> 14) & 127)
                result.append((codepoint >> 7) & 127)
                result.append(codepoint & 127)
            elif (63488 & codepoint) != 55296:
                result.append(((codepoint >> 14) & 15) | 144)
                result.append((codepoint >> 7) & 127)
                result.append(codepoint & 127)
        return result

    def make_key(self, key: str) -> int:
        total = 0
        for char in key:
            codepoint = ord(char)
            bit = 32768
            for _ in range(16):
                if bit & codepoint:
                    break
                bit >>= 1
            total = (total * (bit << 1)) + codepoint
        return total

    def internal_char(self, base_table: str, remainder: int, current: str) -> str:
        seen = 0
        for char in base_table:
            if char in current:
                continue
            if seen == remainder:
                return char
            seen += 1
        return " "

    def make_encode_table(self, number: int, encode_size: int, base_table: str) -> str:
        chars = ""
        temp = number
        for index in range(encode_size):
            divisor = encode_size - index
            remainder = temp % divisor
            chars += self.internal_char(base_table, remainder, chars)
            temp //= divisor
        return chars

    def encode_normal_be(self, data: str, table: str) -> str:
        values = self.string2xa1s(data)
        output: list[str] = []
        digits = [0] * (self.i10 + 1)
        idx = 0
        tail = len(values) % self.i10
        body_size = len(values) - tail
        while idx < body_size:
            value = 0
            for _ in range(self.i10):
                value = (value * self.i8) + values[idx]
                idx += 1
            for digit_index in range(self.i10 + 1):
                digits[digit_index] = value % self.i9
                value //= self.i9
            for digit_index in range(self.i10, -1, -1):
                output.append(table[digits[digit_index]])
        if tail > 0:
            value = 0
            for _ in range(tail):
                value = (value * self.i8) + values[idx]
                idx += 1
            for digit_index in range(tail + 1):
                digits[digit_index] = value % self.i9
                value //= self.i9
            while tail >= 0:
                output.append(table[digits[tail]])
                tail -= 1
        return "".join(output)

    def generate_token(self, device_id: str, timestamp_ms: int, nonce: str) -> str:
        plaintext = (
            f"ai={self.APP_ID}&di={device_id}&as={self.AS_VALUE}&su=false&dbg=false&emu=false&hk=false"
            f"&it={self.app_start_ts}&ts={timestamp_ms}&rt=0&os=13&dm={self.DEVICE_MODEL}&st={self.OS_TYPE}&sv={self.SDK_VERSION}"
        )
        dyn_key = f"v1+{nonce}+{timestamp_ms}"
        key_encoded = self.encode_normal_be(dyn_key, self.table)
        table = self.make_encode_table(self.make_key(dyn_key), self.i9, self.table)
        body_encoded = self.encode_normal_be(plaintext, table)
        return f"bEeEP{self.table[len(key_encoded)]}{key_encoded}{body_encoded}"


class PatchedKorail(Korail):
    _device = "AD"
    _version = "250601002"
    _sid_key = b"2485dd54d9deaa36"
    _device_id = "558a4f02041657ea"

    def __init__(self, korail_id: str, korail_pw: str, auto_login: bool = True, want_feedback: bool = False):
        import requests
        self._session = requests.session()
        self._session.headers.update({"User-Agent": DEFAULT_USER_AGENT})
        self._engine = DynaPathMasterEngine()
        super().__init__(korail_id, korail_pw, auto_login=False, want_feedback=want_feedback)
        self._session.headers.update({"User-Agent": DEFAULT_USER_AGENT})
        if auto_login:
            self.login(korail_id, korail_pw)

    def _generate_sid(self, timestamp_ms: int) -> str:
        plaintext = f"{self._device}{timestamp_ms}".encode("utf-8")
        cipher = AES.new(self._sid_key, AES.MODE_CBC, iv=self._sid_key)
        return base64.b64encode(cipher.encrypt(pad(plaintext, 16))).decode("utf-8") + "\n"

    def _auth_headers_and_sid(self, url: str) -> tuple[dict[str, str], str | None]:
        import json as _json
        headers: dict[str, str] = {}
        timestamp_ms = int(time.time() * 1000)
        nonce = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        headers["x-dynapath-m-token"] = self._engine.generate_token(self._device_id, timestamp_ms, nonce)
        sid = self._generate_sid(timestamp_ms)
        return headers, sid

    def login(self, korail_id: str | None = None, korail_pw: str | None = None) -> bool:
        import json as _json
        import re as _re
        if korail_id is None:
            korail_id = self.korail_id
        else:
            self.korail_id = korail_id
        if korail_pw is None:
            korail_pw = self.korail_pw
        else:
            self.korail_pw = korail_pw

        if korail_mod.EMAIL_REGEX.match(korail_id):
            input_flag = "5"
        elif korail_mod.PHONE_NUMBER_REGEX.match(korail_id):
            input_flag = "4"
        else:
            input_flag = "2"

        headers, sid = self._auth_headers_and_sid(korail_mod.KORAIL_LOGIN)
        payload = {
            "Device": self._device,
            "Version": self._version,
            "txtInputFlg": input_flag,
            "txtMemberNo": korail_id,
            "txtPwd": self._Korail__enc_password(korail_pw),
            "idx": self._idx,
        }
        if sid:
            payload["Sid"] = sid

        response = self._session.post(korail_mod.KORAIL_LOGIN, data=payload, headers=headers)
        data = _json.loads(response.text)
        if data["strResult"] == "SUCC" and data.get("strMbCrdNo") is not None:
            self._key = data["Key"]
            self.membership_number = data["strMbCrdNo"]
            self.name = data["strCustNm"]
            self.email = data["strEmailAdr"]
            self.logined = True
            return True
        self.logined = False
        return False

    def search_train(
        self,
        dep: str,
        arr: str,
        date: str | None = None,
        time_value: str | None = None,
        train_type: str = "100",  # KTX train type code
        passengers: list | None = None,
        include_no_seats: bool = False,
        include_waiting_list: bool = False,
    ):
        import json as _json
        from korail2 import TrainType
        if date is None:
            from datetime import datetime, timezone, timedelta
            date = datetime.now(timezone(timedelta(hours=9))).strftime("%Y%m%d")
        if time_value is None:
            from datetime import datetime, timezone, timedelta
            time_value = datetime.now(timezone(timedelta(hours=9))).strftime("%H%M%S")
        if passengers is None:
            passengers = [AdultPassenger()]

        passengers = Passenger.reduce(passengers)
        adult_count = reduce(lambda total, p: total + p.count, [p for p in passengers if isinstance(p, AdultPassenger)], 0)
        child_count = reduce(lambda total, p: total + p.count, [p for p in passengers if isinstance(p, ChildPassenger)], 0)
        senior_count = reduce(lambda total, p: total + p.count, [p for p in passengers if isinstance(p, SeniorPassenger)], 0)
        toddler_count = 0

        headers, sid = self._auth_headers_and_sid(korail_mod.KORAIL_SEARCH_SCHEDULE)
        payload = {
            "Device": self._device,
            "radJobId": "1",
            "selGoTrain": train_type,
            "txtCardPsgCnt": "0",
            "txtGdNo": "",
            "txtGoAbrdDt": date,
            "txtGoEnd": arr,
            "txtGoHour": time_value,
            "txtGoStart": dep,
            "txtJobDv": "",
            "txtMenuId": "11",
            "txtPsgFlg_1": adult_count,
            "txtPsgFlg_2": child_count,
            "txtPsgFlg_8": toddler_count,
            "txtPsgFlg_3": senior_count,
            "txtPsgFlg_4": "0",
            "txtPsgFlg_5": "0",
            "txtSeatAttCd_2": "000",
            "txtSeatAttCd_3": "000",
            "txtSeatAttCd_4": "015",
            "txtTrnGpCd": train_type,
            "Version": self._version,
        }
        if sid:
            payload["Sid"] = sid

        response = self._session.post(korail_mod.KORAIL_SEARCH_SCHEDULE, params=payload, headers=headers)
        data = _json.loads(response.text)
        if self._result_check(data):
            trains = [korail_mod.Train(info) for info in data["trn_infos"]["trn_info"]]
            trains = [t for t in trains if t.dep_name == dep and t.arr_name == arr]
            return trains
        return []

    def reserve(self, train, passengers=None, option=None):
        import json as _json
        if option is None:
            option_str = "GENERAL_FIRST"
        elif hasattr(option, 'value'):
            option_str = option.value
        else:
            option_str = str(option)

        if not train.has_seat():
            raise SoldOutError()

        if "GENERAL_ONLY" in option_str:
            if train.has_general_seat():
                seat_type = "1"
            else:
                raise SoldOutError()
        elif "SPECIAL_ONLY" in option_str:
            if train.has_special_seat():
                seat_type = "2"
            else:
                raise SoldOutError()
        elif "SPECIAL_FIRST" in option_str:
            seat_type = "2" if train.has_special_seat() else "1"
        else:  # GENERAL_FIRST
            seat_type = "1" if train.has_general_seat() else "2"

        if passengers is None:
            passengers = [AdultPassenger()]
        passengers = Passenger.reduce(passengers)
        passenger_count = reduce(lambda total, p: total + p.count, passengers, 0)

        headers, sid = self._auth_headers_and_sid(korail_mod.KORAIL_TICKETRESERVATION)
        payload = {
            "Device": self._device,
            "Version": self._version,
            "Key": self._key,
            "txtGdNo": "",
            "txtJobId": "1101",
            "txtTotPsgCnt": passenger_count,
            "txtSeatAttCd1": "000",
            "txtSeatAttCd2": "000",
            "txtSeatAttCd3": "000",
            "txtSeatAttCd4": "015",
            "txtSeatAttCd5": "000",
            "hidFreeFlg": "N",
            "txtStndFlg": "N",
            "txtMenuId": "11",
            "txtSrcarCnt": "0",
            "txtJrnyCnt": "1",
            "txtJrnySqno1": "001",
            "txtJrnyTpCd1": "11",
            "txtDptDt1": train.dep_date,
            "txtDptRsStnCd1": train.dep_code,
            "txtDptTm1": train.dep_time,
            "txtArvRsStnCd1": train.arr_code,
            "txtTrnNo1": train.train_no,
            "txtRunDt1": train.run_date,
            "txtTrnClsfCd1": train.train_type,
            "txtPsrmClCd1": seat_type,
            "txtTrnGpCd1": train.train_group,
            "txtChgFlg1": "",
            "txtJrnySqno2": "",
            "txtJrnyTpCd2": "",
            "txtDptDt2": "",
            "txtDptRsStnCd2": "",
            "txtDptTm2": "",
            "txtArvRsStnCd2": "",
            "txtTrnNo2": "",
            "txtRunDt2": "",
            "txtTrnClsfCd2": "",
            "txtPsrmClCd2": "",
            "txtChgFlg2": "",
        }
        if sid:
            payload["Sid"] = sid

        for index, passenger in enumerate(passengers, start=1):
            payload.update(passenger.get_dict(index))

        response = self._session.get(korail_mod.KORAIL_TICKETRESERVATION, params=payload, headers=headers)
        data = _json.loads(response.text)
        if self._result_check(data):
            reservation_id = data["h_pnr_no"]
            for reservation in self.reservations():
                if reservation.rsv_id == reservation_id:
                    return reservation
            raise KorailError(f"예약 {reservation_id} 생성됐으나 조회 불가")

    def reservations(self):
        import json as _json
        payload = {"Device": self._device, "Version": self._version, "Key": self._key}
        response = self._session.get(korail_mod.KORAIL_MYRESERVATIONLIST, params=payload)
        data = _json.loads(response.text)
        try:
            if self._result_check(data):
                return [
                    korail_mod.Reservation(train_info)
                    for journey in data["jrny_infos"]["jrny_info"]
                    for train_info in journey["train_infos"]["train_info"]
                ]
        except NoResultsError:
            return []
        return []


def _build_ktx_passengers(passengers: dict) -> list:
    _check_dependencies()
    result = []
    if passengers.get("adult", 0) > 0:
        result.append(AdultPassenger(count=passengers["adult"]))
    if passengers.get("child", 0) > 0:
        result.append(ChildPassenger(count=passengers["child"]))
    if passengers.get("senior", 0) > 0:
        result.append(SeniorPassenger(count=passengers["senior"]))
    return result or [AdultPassenger()]


class KTXClient:
    def __init__(self, ktx_id: str, ktx_password: str):
        _check_dependencies()
        self.ktx_id = ktx_id
        self.ktx_password = ktx_password
        self._korail: PatchedKorail | None = None
        self._login_time: float = 0

    def _get_client(self) -> PatchedKorail:
        if self._korail is None:
            logger.info("KTX(Korail) 로그인 시도")
            self._korail = PatchedKorail(self.ktx_id, self.ktx_password)
            if not self._korail.logined:
                self._korail = None
                raise NeedToLoginError()
            self._login_time = time.monotonic()
            logger.info("KTX 로그인 성공")
        return self._korail

    def _logout(self):
        self._korail = None
        self._login_time = 0

    def _refresh_if_needed(self):
        if self._korail is not None and (time.monotonic() - self._login_time) >= SESSION_REFRESH_INTERVAL:
            logger.info("KTX 세션 갱신")
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
        def _search():
            self._refresh_if_needed()
            client = self._get_client()
            trains = client.search_train(
                dep, arr, date, time_value=time_, include_no_seats=True
            )
            if time_limit:
                trains = [t for t in trains if getattr(t, "dep_time", "000000") <= time_limit]
            return trains

        try:
            return await asyncio.to_thread(_search)
        except (NeedToLoginError,) as e:
            logger.warning(f"KTX search_train 세션 오류, 재로그인: {e}")
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
            client = self._get_client()
            pax = _build_ktx_passengers(passengers)
            return client.reserve(train, passengers=pax, option=seat_type)

        try:
            return await asyncio.to_thread(_reserve)
        except (NeedToLoginError,) as e:
            logger.warning(f"KTX reserve 세션 오류: {e}")
            self._logout()
            raise
        except Exception:
            self._logout()
            raise
