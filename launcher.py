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

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("tessera")

HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}"


def resource_path(relative: str) -> str:
    """Resolve path for both dev and PyInstaller bundle."""
    if getattr(sys, "_MEIPASS", None):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative)


def start_server():
    """Start uvicorn in a thread."""
    import uvicorn

    # Set working directory so relative paths (data/) resolve correctly
    os.chdir(resource_path("."))

    # Import app directly instead of string path for PyInstaller compatibility
    from backend.main import app

    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info",
    )


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
