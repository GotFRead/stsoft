import asyncio
from datetime import datetime

from . import schemas
from . import models
from tasks_users import actions as task_actions
from tasks_users import models as task_models

from fastapi import status
from models.db_helper import db_helper
from helpers.logger import create_logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


logger = create_logger("timeline_actions.log")

timeout_execute_command = 1000

DEFAULT_TIME = "00:00:00"


async def get_all_timelines():

    session = db_helper.get_scoped_session()

    request = select(models.TimeIntervals).order_by(models.TimeIntervals.id)
    result = await session.execute(request)
    timelines = result.scalars().all()  # (id, prod)
    return timelines


async def create_new_timeline(timeline_schema: schemas.CreateTimeline):
    try:
        result = await asyncio.wait_for(
            __create_timeline(timeline_schema), timeout_execute_command
        )

    except asyncio.TimeoutError as err:
        logger.error(f"create_user raise exception - {err}")
        result = status.HTTP_500_INTERNAL_SERVER_ERROR

    except Exception as err:
        logger.error(f"create_user raise exception - {err}")
        result = status.HTTP_422_UNPROCESSABLE_ENTITY

    return result


async def start_timeline(timeline_schema: schemas.CreateTimeline):
    try:
        result = await asyncio.wait_for(
            __patch_timeline(timeline_schema), timeout_execute_command
        )

    except asyncio.TimeoutError as err:
        logger.error(f"create_user raise exception - {err}")
        result = status.HTTP_500_INTERNAL_SERVER_ERROR

    except Exception as err:
        logger.error(f"create_user raise exception - {err}")
        result = status.HTTP_422_UNPROCESSABLE_ENTITY

    return result


async def stop_timeline(timeline_schema: schemas.StopTimeline):
    try:
        result = await asyncio.wait_for(
            __stop_timeline(timeline_schema), timeout_execute_command
        )

    except asyncio.TimeoutError as err:
        logger.error(f"create_user raise exception - {err}")
        result = status.HTTP_500_INTERNAL_SERVER_ERROR

    except Exception as err:
        logger.error(f"create_user raise exception - {err}")
        result = status.HTTP_422_UNPROCESSABLE_ENTITY

    return result


async def __stop_timeline(timeline_schema: schemas.StopTimeline):
    logger.info(f"Start stop TimeIntervals - {timeline_schema}")

    try:

        session = db_helper.get_scoped_session()
        timeline: schemas.CreateTimeline = await get_timeline_via_id(
            session, timeline_schema.dict()
        )

        if check_close_timeline(timeline):
            raise Exception("This is timeline CLOSE!")

        timeline.time_end = prepare_timeline_time(
            datetime.now().strftime("%H:%M:%S")
        )

        session.add(timeline)

        await __actualization_task(session, timeline)

        await session.commit()

    except Exception as err:
        logger.error(f"__stop_timeline raise exception - {err}")
        return status.HTTP_400_BAD_REQUEST

    return status.HTTP_200_OK


async def __create_timeline(timeline_schema: schemas.CreateTimeline):
    logger.info(f"Start create TimeIntervals - {timeline_schema}")

    timeline_schema.time_start = prepare_timeline_time(
        timeline_schema.time_start
        if timeline_schema.time_start != DEFAULT_TIME
        else datetime.now().strftime("%H:%M:%S")
    )

    timeline_schema.time_end = prepare_timeline_time(timeline_schema.time_end)

    try:
        session = db_helper.get_scoped_session()

        new_timeline = models.TimeIntervals(**timeline_schema.dict())

        session.add(new_timeline)

        await __actualization_task(session, timeline_schema)

        await session.commit()

    except Exception as err:
        logger.error(f"__create_timeline raise exception - {err}")
        return status.HTTP_400_BAD_REQUEST

    return status.HTTP_200_OK


async def __actualization_task(
    session: AsyncSession, timeline_schema: schemas.CreateTimeline
):
    if timeline_schema.time_end != prepare_timeline_time(DEFAULT_TIME):
        modified_task: task_models.Tasks = await task_actions.get_task_via_id(
            session, timeline_schema.task_id
        )

        delta = timeline_schema.time_end - datetime.strptime(
            timeline_schema.time_start.strftime("%H:%M:%S"), "%H:%M:%S"
        )
        modified_task.activity += delta.seconds // 3600

        task_actions.patch_task(modified_task)


async def __patch_timeline(
    session: AsyncSession, new_timeline_schema: schemas.CreateTimeline
):
    logger.info(f"Start create TimeIntervals - {new_timeline_schema}")
    try:

        changed_timeline: models.TimeIntervals = await get_timeline_via_id(
            session=session, timeline_id=new_timeline_schema.id
        )

        for name, value in new_timeline_schema.dict().items():
            if (
                getattr(changed_timeline, name)
                == "This field will be not modified"
            ):
                continue
            setattr(changed_timeline, name, value)

        return changed_timeline

    except Exception as err:
        logger.error(f"__patch_timeline raise exception - {err}")
        return status.HTTP_400_BAD_REQUEST
    return status.HTTP_200_OK


def prepare_timeline_time(time: str):
    return datetime.strptime(
        (time + ":00" if len(time.split(":")) == 2 else time),
        "%H:%M:%S",
    )


async def get_timeline_via_id(session: AsyncSession, timeline_id: int):
    return await session.get(models.TimeIntervals, timeline_id)


def check_close_timeline(timeline):
    return timeline.time_end.strftime("%H:%M:%S") != DEFAULT_TIME
