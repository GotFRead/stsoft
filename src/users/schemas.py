from typing import Annotated

from annotated_types import MinLen
from annotated_types import MaxLen

from pydantic import BaseModel


class CreateUser(BaseModel):
    id: int = -1
    fullname: Annotated[str, MinLen(2), MaxLen(256)]
    user_id: Annotated[str, MinLen(2), MaxLen(256)]


class PatchUser(CreateUser):
    id: int
    fullname: Annotated[str, MinLen(2), MaxLen(256)] = (
        "This field will be not modified"
    )
    user_id: Annotated[str, MinLen(2), MaxLen(256)] = (
        "This field will be not modified"
    )


class DeleteUser(BaseModel):
    id: int
