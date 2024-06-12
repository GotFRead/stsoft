from models.base import Base
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from datetime import datetime


class Storage(Base):
    __tablename__ = "time_intervals"
    task_id: Mapped[str]
    task_owner: Mapped[str]
    time_start: Mapped[datetime]
    time_end: Mapped[datetime]
