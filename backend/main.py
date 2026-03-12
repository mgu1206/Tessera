import os
import sys
import platform
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.db.database import engine
from backend.db import models
from backend.api.routes import tickets, events, auth, settings
from backend.core.auth import restore_from_keychain
from backend.core.poller import resume_polling


models.Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Restore credentials from OS keychain and resume polling
    if restore_from_keychain():
        await resume_polling()
    yield


app = FastAPI(title="Tessera", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(tickets.router)
app.include_router(events.router)
app.include_router(settings.router)


@app.get("/api/system/info")
def system_info():
    return {"platform": platform.system()}


# Serve static web files
# In PyInstaller bundle, _MEIPASS contains the extracted data files
if getattr(sys, "_MEIPASS", None):
    static_dir = Path(sys._MEIPASS) / "backend" / "static"
else:
    static_dir = Path(__file__).parent / "static"
if static_dir.is_dir():
    assets_dir = static_dir / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        return FileResponse(str(static_dir / "index.html"))
