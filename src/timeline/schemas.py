from typing import Annotated

from annotated_types import MaxLen

from sqlalchemy.orm import Mapped
from pydantic import BaseModel

from datetime import datetime

TIME_FORMAT = "%Y-%m-%d %H:%M"
SHORT_TIME_FORMAT = "%Y-%m-%d"


class CreateTimeline(BaseModel):
    id: int = -1
    task_id: int
    owner_id: int
    time_start: str | datetime = (
        f"{datetime.now().strftime(SHORT_TIME_FORMAT)} --:--"
    )
    time_end: str | datetime = (
        f"{datetime.today().strftime(SHORT_TIME_FORMAT)} --:--"
    )


class PatchTimeline(CreateTimeline):
    id: int
    task_id: int = "This field will be not modified"
    owner_id: int = "This field will be not modified"
    description: Annotated[str, MaxLen(256)] = "This field will be not modified"
    time_start: str
    time_end: str = None


class StopTimeline(BaseModel):
    id: int = -1


class GetTimelinesAllUsers(BaseModel):
    time_start: str | datetime = (
        f"{datetime.today().strftime(SHORT_TIME_FORMAT)} --:--"
    )
    time_end: str | datetime = (
        f"{datetime.today().strftime(SHORT_TIME_FORMAT)} --:--"
    )


class DeleteTimeline(BaseModel):
    id: int
