# SRTrain 패키지 사용 가이드

> 패키지: [`SRTrain`](https://github.com/ryanking13/SRT) (v2.6.7+)
> 설치: `pip install SRTrain`

---

## 목차

1. [초기화 및 로그인](#1-초기화-및-로그인)
2. [열차 조회](#2-열차-조회)
3. [예매](#3-예매)
4. [대기 예매](#4-대기-예매)
5. [예매 조회 및 취소](#5-예매-조회-및-취소)
6. [결제](#6-결제)
7. [클래스 레퍼런스](#7-클래스-레퍼런스)
8. [지원 역 목록](#8-지원-역-목록)
9. [예외 처리](#9-예외-처리)

---

## 1. 초기화 및 로그인

```python
from SRT import SRT

# auto_login=True (기본값): 인스턴스 생성 시 자동 로그인
srt = SRT("010-1234-5678", "password")          # 휴대폰 번호
srt = SRT("12345678", "password")               # 회원번호
srt = SRT("user@email.com", "password")         # 이메일

# 수동 로그인
srt = SRT("id", "pw", auto_login=False)
srt.login()

# 로그아웃
srt.logout()
```

**SRT 생성자 파라미터**

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `srt_id` | `str` | 필수 | 회원번호, 이메일, 휴대폰 번호 |
| `srt_pw` | `str` | 필수 | 비밀번호 |
| `auto_login` | `bool` | `True` | 자동 로그인 여부 |
| `verbose` | `bool` | `False` | 디버그 로그 출력 |

**발생 예외**: `SRTLoginError` (잘못된 자격증명 또는 IP 차단)

---

## 2. 열차 조회

```python
trains = srt.search_train(
    dep="수서",
    arr="부산",
    date="20260310",      # yyyyMMdd (기본값: 오늘)
    time="060000",        # hhmmss (기본값: "000000")
    time_limit="120000",  # 조회 종료 시간 (optional)
    available_only=True,  # 잔여석 있는 열차만 (기본값: True)
)

for train in trains:
    print(train)
```

**`search_train` 파라미터**

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `dep` | `str` | 필수 | 출발역 이름 |
| `arr` | `str` | 필수 | 도착역 이름 |
| `date` | `str` | 오늘 | 출발일 (`yyyyMMdd`) |
| `time` | `str` | `"000000"` | 출발 시간 이후 조회 (`hhmmss`) |
| `time_limit` | `str` | `None` | 출발 시간 이전 조회 (`hhmmss`) |
| `available_only` | `bool` | `True` | 예매 가능 열차만 반환 |

**반환값**: `list[SRTTrain]`

---

## 3. 예매

```python
from SRT import SRT
from SRT.passenger import Adult, Child, Senior, Disability1To3, Disability4To6

# 기본 예매 (성인 1명, 일반실 우선)
reservation = srt.reserve(trains[0])

# 승객 지정
reservation = srt.reserve(
    train=trains[0],
    passengers=[Adult(count=2), Child(count=1)],
)

# 좌석 등급 지정
from SRT.constants import SeatType

reservation = srt.reserve(
    train=trains[0],
    passengers=[Adult()],
    special_seat=SeatType.SPECIAL_FIRST,   # 특실 우선
    window_seat=True,                       # 창가 좌석 선호
)
```

**`reserve` 파라미터**

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `train` | `SRTTrain` | 필수 | 예매할 열차 |
| `passengers` | `list[Passenger]` | 성인 1명 | 승객 목록 |
| `special_seat` | `SeatType` | `GENERAL_FIRST` | 좌석 등급 |
| `window_seat` | `bool \| None` | `None` | 창가 선호 여부 |

**`SeatType` 값**

| 값 | 설명 |
|----|------|
| `SeatType.GENERAL_FIRST` | 일반실 우선 (기본값) |
| `SeatType.GENERAL_ONLY` | 일반실만 |
| `SeatType.SPECIAL_FIRST` | 특실 우선 |
| `SeatType.SPECIAL_ONLY` | 특실만 |

**`Passenger` 종류**

| 클래스 | 설명 |
|--------|------|
| `Adult(count=1)` | 어른/청소년 |
| `Child(count=1)` | 어린이 |
| `Senior(count=1)` | 경로 |
| `Disability1To3(count=1)` | 장애 1~3급 |
| `Disability4To6(count=1)` | 장애 4~6급 |

**반환값**: `SRTReservation`
**발생 예외**: `SRTNotLoggedInError`, `SRTResponseError`, `TypeError`, `ValueError`

---

## 4. 대기 예매

매진된 열차에 대해 대기 신청. 빈자리 발생 시 자동 배정.

```python
# 대기 예매 신청
reservation = srt.reserve_standby(
    train=trains[0],
    passengers=[Adult()],
    special_seat=SeatType.GENERAL_FIRST,
    mblPhone="010-1234-5678",   # SMS 수신 번호 (optional)
)

# 대기 예매 옵션 설정
srt.reserve_standby_option_settings(
    reservation=reservation,
    isAgreeSMS=True,            # SMS 동의
    isAgreeClassChange=False,   # 좌석 등급 변경 동의
    telNo="010-1234-5678",
)
```

---

## 5. 예매 조회 및 취소

```python
# 전체 예매 조회
reservations = srt.get_reservations()

# 결제 완료된 예매만 조회
reservations = srt.get_reservations(paid_only=True)

# 티켓 상세 정보
tickets = srt.ticket_info(reservation)
for ticket in tickets:
    print(f"{ticket.car}호차 {ticket.seat} ({ticket.seat_type}) - {ticket.price}원")

# 예매 취소
srt.cancel(reservation)          # SRTReservation 객체
srt.cancel(reservation_number)   # 예매 번호(int)도 가능
```

---

## 6. 결제

```python
success = srt.pay_with_card(
    reservation=reservation,
    number="1234567890123456",   # 카드 번호 (하이픈 없이)
    password="12",               # 카드 비밀번호 앞 2자리
    validation_number="900101",  # 생년월일 또는 사업자번호
    expire_date="2612",          # 유효기간 (YYMM)
    installment=0,               # 할부 개월 (0=일시불, 2~12, 24)
    card_type="J",               # "J"=개인, "S"=법인
)
```

> 주의: 실제 결제가 발생하므로 운영 환경에서만 사용

---

## 7. 클래스 레퍼런스

### SRTTrain

열차 조회 결과 객체.

| 속성 | 타입 | 설명 |
|------|------|------|
| `train_name` | `str` | 열차 이름 (SRT 등) |
| `train_number` | `str` | 열차 번호 |
| `dep_date` | `str` | 출발일 (`yyyyMMdd`) |
| `dep_time` | `str` | 출발 시간 (`hhmmss`) |
| `dep_station_name` | `str` | 출발역 이름 |
| `arr_date` | `str` | 도착일 |
| `arr_time` | `str` | 도착 시간 |
| `arr_station_name` | `str` | 도착역 이름 |
| `general_seat_state` | `str` | 일반실 상태 (`"예약가능"` 등) |
| `special_seat_state` | `str` | 특실 상태 |

| 메서드 | 반환 | 설명 |
|--------|------|------|
| `general_seat_available()` | `bool` | 일반실 예매 가능 여부 |
| `special_seat_available()` | `bool` | 특실 예매 가능 여부 |
| `seat_available()` | `bool` | 일반실 또는 특실 예매 가능 여부 |
| `reserve_standby_available()` | `bool` | 대기 예매 가능 여부 |

### SRTReservation

예매 결과 객체.

| 속성 | 타입 | 설명 |
|------|------|------|
| `reservation_number` | `int` | 예매 번호 |
| `total_cost` | `int` | 총 결제 금액 |
| `seat_count` | `int` | 예매 좌석 수 |
| `train_name` | `str` | 열차 이름 |
| `train_number` | `str` | 열차 번호 |
| `dep_date` | `str` | 출발일 |
| `dep_time` | `str` | 출발 시간 |
| `dep_station_name` | `str` | 출발역 |
| `arr_time` | `str` | 도착 시간 |
| `arr_station_name` | `str` | 도착역 |
| `payment_date` | `str` | 결제 기한 날짜 |
| `payment_time` | `str` | 결제 기한 시간 |
| `paid` | `bool` | 결제 완료 여부 |
| `tickets` | `list[SRTTicket]` | 개별 티켓 목록 (property) |

### SRTTicket

개별 티켓 객체.

| 속성 | 타입 | 설명 |
|------|------|------|
| `car` | `str` | 호차 번호 |
| `seat` | `str` | 좌석 번호 |
| `seat_type` | `str` | 좌석 유형 (일반실/특실) |
| `passenger_type` | `str` | 승객 유형 (어른 등) |
| `price` | `int` | 최종 금액 |
| `original_price` | `int` | 원래 금액 |
| `discount` | `int` | 할인 금액 |

---

## 8. 지원 역 목록

```
수서, 동탄, 평택지제, 천안아산, 오송, 대전, 김천(구미), 동대구, 서대구,
신경주/경주, 울산(통도사), 부산, 공주, 익산, 전주, 정읍, 광주송정,
나주, 목포, 여수EXPO, 여천, 순천, 곡성, 구례구, 남원, 밀양,
창원중앙, 창원, 마산, 진영, 진주, 포항
```

---

## 9. 예외 처리

| 예외 | 발생 상황 |
|------|-----------|
| `SRTLoginError` | 잘못된 로그인 정보 또는 IP 차단 |
| `SRTNotLoggedInError` | 로그인 없이 예매/조회 시도 |
| `SRTResponseError` | HTTP 오류 또는 서버 응답 오류 |

```python
from SRT.exceptions import SRTLoginError, SRTNotLoggedInError, SRTResponseError

try:
    srt = SRT("id", "wrong_password")
except SRTLoginError as e:
    print(f"로그인 실패: {e}")

try:
    reservation = srt.reserve(train)
except SRTResponseError as e:
    print(f"예매 실패: {e}")
```
