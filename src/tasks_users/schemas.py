from typing import Annotated

from annotated_types import MinLen
from annotated_types import MaxLen

from pydantic import BaseModel


class CreateTask(BaseModel):
    id: int = -1
    task_id: Annotated[str, MaxLen(256)]
    description: Annotated[str, MaxLen(256)]
    owner: int
    activity: int


class PatchTask(CreateTask):
    id: int
    task_id: Annotated[str, MaxLen(256)] = (
        "This field will be not modified"
    )
    description: Annotated[str, MaxLen(256)] = (
        "This field will be not modified"
    )
    owner: int = "This field will be not modified"
    activity: int = "This field will be not modified"


class DeleteTask(BaseModel):
    id: int
