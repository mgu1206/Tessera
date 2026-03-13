"""Tessera system tray launcher.

Starts the FastAPI backend and provides a system tray icon
with options to open the browser, restart, or quit.
"""

import os
import sys
import signal
import threading
import webbrowser
import logging
import traceback

# Log to file next to the executable for diagnosis
if getattr(sys, "frozen", False):
    _log_path = os.path.join(os.path.dirname(sys.executable), "tessera.log")
else:
    _log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tessera.log")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s [%(name)s]: %(message)s",
    handlers=[
        logging.FileHandler(_log_path, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("tessera")

HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}"


def resource_path(relative: str) -> str:
    """Resolve path for both dev and PyInstaller bundle."""
    if getattr(sys, "frozen", False):
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative)


def start_server():
    """Start uvicorn in a thread."""
    try:
        import sys
        
        # Override sys.stdout / sys.stderr safely for pyinstaller noconsole
        if getattr(sys, "frozen", False):
            class _DummyStream:
                def write(self, *args, **kwargs): pass
                def flush(self, *args, **kwargs): pass
                def isatty(self): return False
            sys.stdout = _DummyStream()
            sys.stderr = _DummyStream()

        import uvicorn

        base = resource_path(".")
        logger.info(f"Resource base: {base}")
        logger.info(f"_MEIPASS: {getattr(sys, '_MEIPASS', 'N/A')}")
        logger.info(f"sys.executable: {sys.executable}")
        logger.info(f"frozen: {getattr(sys, 'frozen', False)}")

        # Set working directory so relative paths resolve correctly
        os.chdir(base)

        # Check static files
        static_dir = os.path.join(base, "backend", "static")
        logger.info(f"Static dir exists: {os.path.isdir(static_dir)}")
        if os.path.isdir(static_dir):
            logger.info(f"Static contents: {os.listdir(static_dir)}")

        # Import app directly for PyInstaller compatibility
        from backend.main import app

        logger.info("App imported successfully, starting uvicorn...")

        uvicorn.run(
            app,
            host=HOST,
            port=PORT,
            log_config=None,
        )
    except Exception:
        logger.error(f"Server failed to start:\n{traceback.format_exc()}")


def create_icon_image():
    """Create a simple T icon for the tray."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGBA", (64, 64), (79, 142, 247, 255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 40)
        except (OSError, IOError):
            font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), "T", font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (64 - tw) // 2 - bbox[0]
    y = (64 - th) // 2 - bbox[1]
    draw.text((x, y), "T", fill="white", font=font)
    return img


def main():
    import pystray

    logger.info(f"Tessera launcher starting (log: {_log_path})")

    # Start server in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Wait briefly for server to start, then open browser
    def open_browser():
        import time
        time.sleep(2)
        webbrowser.open(URL)

    threading.Thread(target=open_browser, daemon=True).start()

    # Tray menu
    def on_open(icon, item):
        webbrowser.open(URL)

    def on_quit(icon, item):
        icon.stop()
        os.kill(os.getpid(), signal.SIGTERM)

    icon = pystray.Icon(
        "Tessera",
        create_icon_image(),
        "Tessera - SRT 자동 예매",
        menu=pystray.Menu(
            pystray.MenuItem("브라우저 열기", on_open, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("종료", on_quit),
        ),
    )

    logger.info(f"Tessera started at {URL}")
    icon.run()


if __name__ == "__main__":
    main()
