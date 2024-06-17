import asyncio

from . import schemas
from . import models
from . import dependencies
from sqlalchemy import select

from fastapi import status
from models.db_helper import db_helper
from helpers.logger import create_logger
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime


ACTIVITY_TIME_FORMAT = "00:00"

logger = create_logger("timeline_actions.log")

timeout_execute_command = 1000


async def create_new_task(task_schemas: schemas.CreateTask):
    logger.log_start(create_new_task, task_schemas)

    try:
        result = await asyncio.wait_for(
            __create_new_task(task_schemas), timeout_execute_command
        )

    except asyncio.TimeoutError as err:
        logger.log_exception(create_new_task, task_schemas, err)
        result = status.HTTP_500_INTERNAL_SERVER_ERROR

    except Exception as err:
        logger.log_exception(create_new_task, task_schemas, err)
        result = status.HTTP_422_UNPROCESSABLE_ENTITY

    logger.log_complete(create_new_task, task_schemas)
    return result


async def __create_new_task(task_schemas: schemas.CreateTask):
    logger.info(f"Start create task - {task_schemas}")
    try:
        session = db_helper.get_scoped_session()

        schemas_mapping = task_schemas.dict()

        if not hasattr(task_schemas, "activity"):
            schemas_mapping["activity"] = (
                f"{datetime.today().strftime(ACTIVITY_TIME_FORMAT)}"
            )

        schemas_mapping["activity"] = datetime.strptime(
            schemas_mapping["activity"],
            schemas.ACTIVITY_TIME_FORMAT,
        )
        schemas_mapping["activity"] = dependencies.SummaryActivity(
            schemas_mapping["activity"].hour, 
            schemas_mapping["activity"].minute
        ).__str__()

        new_task = models.Tasks(**schemas_mapping)

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


async def delete_task(task_schemas: schemas.DeleteTask):
    logger.log_start(delete_task, task_schemas)

    try:
        result = await asyncio.wait_for(
            __delete_task(task_schemas), timeout_execute_command
        )

    except asyncio.TimeoutError as err:
        logger.log_exception(delete_task, task_schemas, err)
        result = status.HTTP_500_INTERNAL_SERVER_ERROR

    except Exception as err:
        logger.log_exception(delete_task, task_schemas, err)
        result = status.HTTP_422_UNPROCESSABLE_ENTITY

    logger.log_complete(delete_task, task_schemas)
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


async def __delete_task(task_schemas: schemas.DeleteTask):
    try:
        session = db_helper.get_scoped_session()

        logger.info(f"Start remove task - {task_schemas}")
        removed_task: models.Tasks = await get_task_via_id(
            session=session, task_id=task_schemas.id
        )
        await session.delete(removed_task)

        await session.commit()

    except Exception as err:
        logger.error(f"remove task raise exception - {err}")
        return status.HTTP_400_BAD_REQUEST
    return status.HTTP_200_OK


async def __update_task_info_partial(
    session: AsyncSession, task_schemas: schemas.CreateTask
):

    changed_user: models.Tasks = await get_task_via_id(
        session=session, user_id=task_schemas.id
    )

    for name, value in task_schemas.dict().items():
        if getattr(task_schemas, name) == "This field will be not modified":
            continue
        setattr(changed_user, name, value)

    return changed_user


async def get_task_via_id(session: AsyncSession, task_id: int):
    return await session.get(models.Tasks, task_id)


async def get_all_tasks():
    logger.log_start(get_all_tasks, dict())

    try:
        session = db_helper.get_scoped_session()
        request = select(models.Tasks).order_by(models.Tasks.id)
        result = await session.execute(request)
        timelines = result.scalars().all()  # (id, prod)
    except Exception as err:
        logger.log_exception(get_all_tasks, dict(), err)
        return status.HTTP_400_BAD_REQUEST

    logger.log_complete(get_all_tasks, dict())
    return timelines
