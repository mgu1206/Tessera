# Tessera

**[한국어](README_KO.md) | English**

A desktop app for automatic SRT (Korea's high-speed rail) ticket booking.

Automatically attempts to book tickets when seats become available, and sends notifications via Telegram or iMessage.

## Installation

Download from the [Releases](https://github.com/mgu1206/Tessera/releases) page:

| Platform | File |
|----------|------|
| macOS | `Tessera-macOS.zip` |
| Windows | `Tessera-Windows.zip` |

After extracting, run the app. A system tray icon will appear and a browser window will open automatically.

## Usage

1. **Login** — Enter your SRT member number (or email) and password
2. **Booking Request** — Set departure station, arrival station, date, time range, seat type, and number of passengers
3. **Auto Search** — Checks for available seats more frequently as the departure date approaches (log-scale interval)
4. **Booking Success** — Books immediately when a seat is found, sends notification through configured channels
5. **Settings** — Configure Telegram, iMessage (macOS) notifications and polling options

### Notification Channels

| Channel | Platform | Configuration |
|---------|----------|---------------|
| Telegram | All | Bot Token + Chat ID |
| iMessage | macOS | Up to 5 recipients |

### Credential Storage

SRT login credentials are encrypted and stored in your OS secure storage:
- macOS: Keychain
- Windows: Credential Manager

Credentials are automatically restored on app restart.

## Development

```bash
# Backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt

python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Frontend (dev server)
cd web
npm install
npm run dev

# Frontend (build)
npm run build
cp -r dist/ ../backend/static/
```

### Build

```bash
pip install pystray Pillow pyinstaller
python -m PyInstaller tessera.spec --noconfirm
# Output: dist/Tessera.app (macOS) or dist/Tessera/ (Windows)
```

Pushing a `v*` tag triggers GitHub Actions to automatically build for macOS + Windows and upload to Releases.

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy (SQLite), asyncio, SRTrain
- **Frontend**: React, TypeScript, Vite
- **Notifications**: Telegram Bot API, AppleScript (iMessage)
- **Packaging**: PyInstaller, pystray

## License

MIT
