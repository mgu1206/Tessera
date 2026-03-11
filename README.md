# Tessera

SRT(수서고속철도) 자동 예매 데스크톱 앱.

잔여석이 발생하면 자동으로 예매를 시도하고, 텔레그램 또는 iMessage로 알림을 보냅니다.

## 설치

[Releases](https://github.com/mgu1206/Tessera/releases) 페이지에서 다운로드:

| 플랫폼 | 파일 |
|--------|------|
| macOS | `Tessera-macOS.zip` |
| Windows | `Tessera-Windows.zip` |

압축 해제 후 실행하면 시스템 트레이에 아이콘이 나타나고 브라우저가 자동으로 열립니다.

## 사용법

1. **로그인** — SRT 회원번호(또는 이메일)와 비밀번호 입력
2. **예매 요청** — 출발역, 도착역, 날짜, 시간 범위, 좌석 타입, 인원 설정 후 시작
3. **자동 조회** — 예약일이 가까울수록 빈번하게 잔여석 확인 (로그 스케일 인터벌)
4. **예매 성공** — 잔여석 발견 시 즉시 예매, 설정된 채널로 알림 발송
5. **설정** — 텔레그램, iMessage(macOS) 알림 설정 및 폴링 옵션

### 알림 채널

| 채널 | 플랫폼 | 설정 |
|------|--------|------|
| Telegram | 전체 | Bot Token + Chat ID |
| iMessage | macOS | 수신자 최대 5명 |

### 자격증명 저장

SRT 로그인 정보는 OS 보안 저장소에 암호화되어 저장됩니다:
- macOS: Keychain
- Windows: Credential Manager

앱 재시작 시 자동으로 복원됩니다.

## 개발

```bash
# 백엔드
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt

python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 프론트엔드 (개발 서버)
cd web
npm install
npm run dev

# 프론트엔드 (빌드)
npm run build
cp -r dist/ ../backend/static/
```

### 빌드

```bash
pip install pystray Pillow pyinstaller
python -m PyInstaller tessera.spec --noconfirm
# 결과: dist/Tessera.app (macOS) 또는 dist/Tessera/ (Windows)
```

`v*` 태그 푸시 시 GitHub Actions에서 macOS + Windows 빌드가 자동 실행되어 Release에 업로드됩니다.

## 기술 스택

- **백엔드**: FastAPI, SQLAlchemy (SQLite), asyncio, SRTrain
- **프론트엔드**: React, TypeScript, Vite
- **알림**: Telegram Bot API, AppleScript (iMessage)
- **패키징**: PyInstaller, pystray

## License

MIT
