from models.base import Base
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class Users(Base):
    __tablename__ = "users"
    user_id: Mapped[str]
    fullname: Mapped[str]