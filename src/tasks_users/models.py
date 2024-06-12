from models.base import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class Task(Base):
    __tablename__ = "tasks"
    task_id: Mapped[str]
    description: Mapped[str]
    owner: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete='CASCADE')) 
    activity: Mapped[int]
