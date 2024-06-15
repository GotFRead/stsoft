from models.base import Base
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from datetime import datetime


class TimeIntervals(Base):
    __tablename__ = "time_intervals"
    task_id: Mapped[int]
    owner_id: Mapped[int]
    time_start: Mapped[datetime] 
    time_end: Mapped[datetime]
