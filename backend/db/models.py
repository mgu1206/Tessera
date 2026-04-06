import datetime
from sqlalchemy import Column, String, Integer, DateTime, JSON, Boolean
from backend.db.database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(String(4), primary_key=True)
    train_type = Column(String(3), nullable=False, default="SRT")  # "SRT" or "KTX"
    dep = Column(String, nullable=False)
    arr = Column(String, nullable=False)
    date = Column(String(8), nullable=False)   # yyyyMMdd
    time = Column(String(6), nullable=False)   # hhmmss
    time_limit = Column(String(6), nullable=True)
    seat_type = Column(String, nullable=False, default="GENERAL_FIRST")
    passengers = Column(JSON, nullable=False)  # {adult, child, senior}
    status = Column(String, nullable=False, default="PENDING")
    attempt_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))))
    reserved_at = Column(DateTime, nullable=True)
    reservation_info = Column(JSON, nullable=True)
    last_searched_at = Column(DateTime, nullable=True)
    last_search_results = Column(JSON, nullable=True)  # [{train_number, dep_time, arr_time, general, special}, ...]
    # 그룹화
    group_id = Column(String, nullable=True)
    manually_completed = Column(Boolean, default=False, nullable=False)
