import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from backend.config import settings

# Ensure data directory exists
# In PyInstaller bundle: next to the executable
# In dev: next to project root
if getattr(sys, "frozen", False):
    data_dir = Path(sys.executable).parent / "data"
else:
    data_dir = Path(__file__).resolve().parent.parent.parent / "data"
data_dir.mkdir(exist_ok=True)

# Resolve database URL: replace relative path with absolute
db_url = settings.database_url
if db_url.startswith("sqlite:///./"):
    db_path = data_dir / db_url.replace("sqlite:///./data/", "")
    db_url = f"sqlite:///{db_path}"

engine = create_engine(
    db_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
