from . import actions
from . import schemas

# __fastapi_depend__

from fastapi import APIRouter
from fastapi import Request

# __router__

router = APIRouter(prefix="/users", tags=["users"])

# __handlers__

@router.get("/")
async def get_all_users():
    return await actions.get_all_users()


@router.post("/")
async def create_user(user_info: schemas.CreateUser):
    """ Это решение пункта номер 1 """
    return await actions.create_user(user_info)


@router.patch("/")
async def patch_user(user_info: schemas.PatchUser):
    """ Это решение пункта номер 2 """
    return await actions.patch_user(user_info)


@router.delete("/{user_id}")
async def delete_user(user_id: int):
    """ Это решение пункта номер 10 """
    user_info = schemas.DeleteUser
    user_info.id = user_id
    return await actions.delete_user(user_info)
