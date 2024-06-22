from typing import Annotated

from annotated_types import MinLen
from annotated_types import MaxLen

from pydantic import BaseModel
from datetime import datetime


ACTIVITY_TIME_FORMAT = "00:00"


class CreateTask(BaseModel):
    task_id: Annotated[str, MaxLen(256)]
    description: Annotated[str, MaxLen(256)]
    owner_id: int


class PatchTask(CreateTask):
    id: int
    task_id: Annotated[str, MaxLen(256)] = "This field will be not modified"
    description: Annotated[str, MaxLen(256)] = "This field will be not modified"
    owner_id: int | str = "This field will be not modified"


class DeleteTask(BaseModel):
    id: int
