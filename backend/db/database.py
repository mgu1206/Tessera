import sys
from pathlib import Path
from sqlalchemy import create_engine, text
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


def run_migrations():
    """기존 DB에 새 컬럼을 추가하는 간단한 마이그레이션."""
    migrations = [
        "ALTER TABLE tickets ADD COLUMN train_type VARCHAR(3) DEFAULT 'SRT'",
        "ALTER TABLE tickets ADD COLUMN group_id VARCHAR",
        "ALTER TABLE tickets ADD COLUMN manually_completed BOOLEAN DEFAULT 0",
    ]
    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception:
                pass  # 컬럼이 이미 존재하면 무시
