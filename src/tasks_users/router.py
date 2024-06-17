from . import actions
from . import schemas

# __fastapi_depend__

from fastapi import APIRouter
from fastapi import Request


# __router__

router = APIRouter(tags=["tasks"], prefix="/tasks")


@router.get("/")
async def get_all_tasks():
    return await actions.get_all_tasks()


@router.post("/create_task")
async def create_new_task(task: schemas.CreateTask):
    return await actions.create_new_task(task)


@router.delete("/delete_task")
async def remove_task(task: schemas.DeleteTask):
    return await actions.delete_task(task)
