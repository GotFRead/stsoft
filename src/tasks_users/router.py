from . import actions
from . import schemas

# __fastapi_depend__

from fastapi import APIRouter
from fastapi import Request


# __router__

router = APIRouter(tags=["tasks"])


@router.get("/")
async def get_all_tasks():
    return await actions.get_all_timelines()


@router.post("/create_task")
async def create_new_task(task: schemas.CreateTask):
    return await actions.create_new_task(task)


@router.patch("/stop_timeline")
async def stop_task(task: schemas.DeleteTask):
    return await actions.stop_timeline(task)


@router.delete("/")
async def remove_task(task: schemas.DeleteTask):
    return await actions.delete_task(task)
