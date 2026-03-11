# Tessera - SRT 자동 예매 프레임워크

## 프로젝트 개요

한국 SRT 기차표를 자동으로 예매하는 프레임워크.
백엔드 API + 웹 UI 구성. 텔레그램 봇은 선택적 별도 프로세스.

---

## 서비스 구성

```
tessera/
  backend/     # FastAPI + SQLite + 폴링 엔진
  web/         # React 프론트엔드 (빌드 → backend/static/)
  tgbot/       # 텔레그램 봇 (선택적)
```

---

## 1. Backend

### 기술 스택
- FastAPI, SQLAlchemy (SQLite), asyncio, SRTrain, httpx

### 디렉토리 구조

```
backend/
  api/routes/
    auth.py        # SRT 로그인/로그아웃
    tickets.py     # 티켓 CRUD
    events.py      # SSE 이벤트 스트림
    settings.py    # 알림/폴링 설정 + 테스트
  core/
    auth.py               # 인메모리 자격증명 저장
    srt_client.py         # SRTrain 래퍼
    poller.py             # 폴링 엔진 (로그스케일 인터벌)
    event_bus.py          # 이벤트 pub/sub
    notifier.py           # 텔레그램 + iMessage(macOS) 알림
    notification_settings.py  # 인메모리 설정 저장
  db/
    models.py      # Ticket 모델
    database.py    # DB 연결
  config.py        # DATABASE_URL만 관리
  main.py          # FastAPI 앱
```

### REST API

| Method | Endpoint | 설명 |
|--------|----------|------|
| `POST` | `/api/auth/login` | SRT 로그인 (자격증명 검증) |
| `POST` | `/api/auth/logout` | 로그아웃 + 전체 폴링 중지 + 티켓 삭제 |
| `GET` | `/api/auth/status` | 로그인 상태 확인 |
| `GET` | `/api/tickets` | 티켓 목록 |
| `POST` | `/api/tickets` | 티켓 생성 + 폴링 시작 |
| `DELETE` | `/api/tickets/{id}` | 티켓 취소/삭제 |
| `GET` | `/api/events` | SSE 이벤트 스트림 |
| `GET` | `/api/settings` | 설정 조회 |
| `PUT` | `/api/settings` | 설정 저장 |
| `POST` | `/api/settings/notifications/test/telegram` | 텔레그램 테스트 |
| `POST` | `/api/settings/notifications/test/imessage` | iMessage 테스트 (macOS) |
| `GET` | `/api/system/info` | 플랫폼 정보 |

### 인증 흐름
- 서버 시작 시 자격증명 없음 → 웹 로그인 필요
- 로그인: SRT 계정 검증 후 인메모리 저장
- 로그아웃: 모든 폴링 중지, DB 티켓 삭제, 자격증명 초기화

### 알림 설정 (인메모리)
- 텔레그램: Bot Token + Chat ID
- iMessage: macOS에서만 활성, 최대 5명 수신자
- 폴링: 리포트 주기, 최대 시도 횟수

---

## 2. Web

### 기술 스택
- Vite + React + TypeScript

### 페이지 구성
- **로그인**: SRT 계정 입력
- **메인**: 예매 폼 + 티켓 현황 (SSE 실시간 갱신)
- **설정**: 텔레그램, iMessage(macOS), 폴링 설정

---

## 3. Telegram Bot (선택적)

### 기술 스택
- python-telegram-bot, httpx

### 명령어
- `/book 출발역 도착역 날짜 시작시간 [종료시간] [좌석] [인원]`
- 예: `/book 수서 부산 20260315 0700 1200 특실우선 성인2`

---

## 개발

```bash
# 백엔드
cd tessera
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 프론트엔드 (개발)
cd web
npm install
npm run dev

# 프론트엔드 (빌드 → 백엔드 정적 파일)
npm run build
cp -r dist/ ../backend/static/
```
