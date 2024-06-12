import asyncio

from . import schemas
from . import models

from fastapi import status
from models.db_helper import db_helper
from helpers.logger import create_logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


logger = create_logger("timeline_actions.log")

timeout_execute_command = 1000


async def create_new_task(task_schemas: schemas.CreateTask):
    try:
        result = await asyncio.wait_for(
            __create_new_task(task_schemas), timeout_execute_command
        )

    except asyncio.TimeoutError as err:
        logger.error(f"create_user raise exception - {err}")
        result = status.HTTP_500_INTERNAL_SERVER_ERROR

    except Exception as err:
        logger.error(f"create_user raise exception - {err}")
        result = status.HTTP_422_UNPROCESSABLE_ENTITY

    return result


async def __create_new_task(task_schemas: schemas.CreateTask):
    logger.info(f"Start create task - {task_schemas}")
    try:
        session = db_helper.get_scoped_session()

        new_task = models.Tasks(**task_schemas.dict())

        session.add(new_task)

        await session.commit()

    except Exception as err:
        logger.error(f"create_user raise exception - {err}")
        return status.HTTP_400_BAD_REQUEST
    return status.HTTP_200_OK


async def patch_task(task_schemas: schemas.PatchTask):
    try:
        result = await asyncio.wait_for(
            __patch_task(task_schemas), timeout_execute_command
        )

    except asyncio.TimeoutError as err:
        logger.error(f"create_user raise exception - {err}")
        result = status.HTTP_500_INTERNAL_SERVER_ERROR

    except Exception as err:
        logger.error(f"create_user raise exception - {err}")
        result = status.HTTP_422_UNPROCESSABLE_ENTITY

    return result


async def delete_task(user_schemas: schemas.DeleteTask):
    try:
        result = await asyncio.wait_for(
            __delete_task(user_schemas), timeout_execute_command
        )

    except asyncio.TimeoutError as err:
        logger.error(f"create_user raise exception - {err}")
        result = status.HTTP_500_INTERNAL_SERVER_ERROR

    except Exception as err:
        logger.error(f"create_user raise exception - {err}")
        result = status.HTTP_422_UNPROCESSABLE_ENTITY

    return result


async def __patch_task(user_schemas: schemas.CreateTask):
    logger.info(f"Start patch task - {user_schemas}")
    try:
        session = db_helper.get_scoped_session()

        new_user = await __update_task_info_partial(session, user_schemas)

        session.add(new_user)

        await session.commit()

    except Exception as err:
        logger.error(f"patch task raise exception - {err}")
        return status.HTTP_400_BAD_REQUEST
    return status.HTTP_200_OK


async def __delete_task(user_schemas: schemas.DeleteTask):
    try:
        session = db_helper.get_scoped_session()

        logger.info(f"Start remove task - {user_schemas}")
        removed_user: models.Users = await __get_task_via_id(
            session=session, user_id=user_schemas.id
        )
        await session.delete(removed_user)

        await session.commit()

    except Exception as err:
        logger.error(f"remove task raise exception - {err}")
        return status.HTTP_400_BAD_REQUEST
    return status.HTTP_200_OK


async def __update_task_info_partial(
    session: AsyncSession, task_schemas: schemas.CreateTask
):

    changed_user: models.Tasks = await __get_task_via_id(
        session=session, user_id=task_schemas.id
    )

    for name, value in task_schemas.dict().items():
        if getattr(task_schemas, name) == "This field will be not modified":
            continue
        setattr(changed_user, name, value)

    return changed_user


async def __get_task_via_id(session: AsyncSession, user_id: int):
    return await session.get(models.Tasks, user_id)
