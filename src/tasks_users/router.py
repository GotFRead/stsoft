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
    """Создание новой задачи для конкретного пользователя"""
    return await actions.create_new_task(task)


@router.patch("/patch_task")
async def create_new_task(task: schemas.PatchTask):
    """Исправление задачи для конкретного пользователя"""
    return await actions.patch_task(task)


@router.delete("/delete_task/{task_id}")
async def remove_task(task_id: int):
    """Это решение пункта номер 9"""
    task_info = schemas.DeleteTask
    task_info.id = task_id
    return await actions.delete_task(task_info)
