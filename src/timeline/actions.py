import asyncio
from datetime import datetime
from datetime import timedelta

from . import schemas
from . import models
from tasks_users import actions as task_actions
from tasks_users import models as task_models
from tasks_users import dependencies as task_dependencies

from fastapi import status
from models.db_helper import db_helper
from helpers.logger import create_logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


logger = create_logger("timeline_actions.log")

timeout_execute_command = 1000

DEFAULT_TIME = "--:--"
TIME_FORMAT = "%Y-%m-%d %H:%M"
NOT_COMPILE_TIME_FORMAT = "%Y-%m-%d 00:00"
DELTA_TIME_FORMAT = "%H:%M"
TODAY_END_TIME_FORMAT = "%Y-%m-%d 23:59"


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


async def get_timelines_all_users(
    timeline_schema: schemas.GetTimelinesAllUsers,
):
    try:
        result = await asyncio.wait_for(
            __get_timelines_all_users(timeline_schema), timeout_execute_command
        )

    except asyncio.TimeoutError as err:
        logger.error(f"create_user raise exception - {err}")
        result = status.HTTP_500_INTERNAL_SERVER_ERROR

    except Exception as err:
        logger.error(f"create_user raise exception - {err}")
        result = status.HTTP_422_UNPROCESSABLE_ENTITY

    return result


async def __get_timelines_all_users(
    timeline_schema: schemas.GetTimelinesAllUsers,
):
    logger.info(f"Start get_all_timelines TimeIntervals - {timeline_schema}")
    try:

        compile_timelines_range(timeline_schema)

        timelines: list[schemas.CreateTimeline] = await get_all_timelines()

        result = __get_all_timeline_in_the_range(
            timeline_schema.time_start, timeline_schema.time_end, timelines
        )

    except Exception as err:
        logger.error(f"get_all_timelines raise exception - {err}")
        return status.HTTP_400_BAD_REQUEST

    return result


def compile_timelines_range(timeline_schema: schemas.GetTimelinesAllUsers):
    timeline_schema.time_start = prepare_timeline_time(
        timeline_schema.time_start
        if DEFAULT_TIME not in timeline_schema.time_start
        else datetime.now().strftime(NOT_COMPILE_TIME_FORMAT)
    )

    timeline_schema.time_end = prepare_timeline_time(
        timeline_schema.time_end
        if DEFAULT_TIME not in timeline_schema.time_end
        else datetime.now().strftime(TODAY_END_TIME_FORMAT)
    )


def __get_all_timeline_in_the_range(
    time_start: datetime,
    time_stop: datetime,
    timelines_list: list[schemas.CreateTimeline],
):
    result = []
    for current_timeline in timelines_list:
        # ? На подумать, нужно ли игнорировать не закрытые таймлайны
        # if not check_close_timeline(current_timeline):
        #     continue

        if (time_start <= current_timeline.time_start) and (
            current_timeline.time_end <= time_stop
        ):
            result.append(current_timeline)

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
            datetime.now().strftime(TIME_FORMAT)
        )

        __get_timeline_activity(timeline)

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
        if DEFAULT_TIME not in timeline_schema.time_start
        else datetime.now().strftime(TIME_FORMAT)
    )

    timeline_schema.time_end = (
        prepare_timeline_time(timeline_schema.time_end)
        if DEFAULT_TIME not in timeline_schema.time_end
        else prepare_timeline_time(
            datetime.now().strftime(NOT_COMPILE_TIME_FORMAT)
        )
    )
    if timeline_schema.time_end.strftime(
        TIME_FORMAT
    ) != datetime.now().strftime(NOT_COMPILE_TIME_FORMAT):
        __get_timeline_activity(timeline_schema)

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


def __get_timeline_activity(timeline_schema: schemas.CreateTimeline):
    delta = timeline_schema.time_end - datetime.strptime(
        timeline_schema.time_start.strftime(TIME_FORMAT), TIME_FORMAT
    )

    modified_task_summary_activity = get_summary_activity(
        int(schemas.ACTIVITY_TIME_FORMAT.split(":")[0]),
        int(schemas.ACTIVITY_TIME_FORMAT.split(":")[1]),
    )

    hours_delta, minute_delta = get_hours_and_minutes_from_delta(delta)

    modified_task_summary_activity.hours = (
        modified_task_summary_activity.hours + hours_delta
    )
    modified_task_summary_activity.minutes = (
        modified_task_summary_activity.minutes + minute_delta
    )

    timeline_schema.activity = str(modified_task_summary_activity)


async def __get_all_timeline_in_the_range_for_specified_user(
    timeline_schema: schemas.GetTimelinesAllUsers,
):
    logger.info(
        f"Start __get_all_timeline_in_the_range_for_specified_user TimeIntervals - {timeline_schema}"
    )
    try:

        compile_timelines_range(timeline_schema)

        timelines: list[schemas.CreateTimeline] = await get_all_timelines()

        result = __get_all_timeline_in_the_range(
            timeline_schema.time_start, timeline_schema.time_end, timelines
        )

    except Exception as err:
        logger.error(
            f"__get_all_timeline_in_the_range_for_specified_user raise exception - {err}"
        )
        return status.HTTP_400_BAD_REQUEST

    return result


async def __actualization_task(
    session: AsyncSession, timeline_schema: schemas.CreateTimeline
):

    if timeline_schema.time_end.strftime(
        TIME_FORMAT
    ) == datetime.now().strftime(NOT_COMPILE_TIME_FORMAT):
        return None

    modified_task: task_models.Tasks = await task_actions.get_task_via_id(
        session, timeline_schema.task_id
    )

    delta = timeline_schema.time_end - datetime.strptime(
        timeline_schema.time_start.strftime(TIME_FORMAT), TIME_FORMAT
    )

    modified_task_summary_activity = get_active_summary_activity_from_task(
        modified_task
    )

    hours_delta, minute_delta = get_hours_and_minutes_from_delta(delta)

    modified_task_summary_activity.hours = (
        modified_task_summary_activity.hours + hours_delta
    )
    modified_task_summary_activity.minutes = (
        modified_task_summary_activity.minutes + minute_delta
    )

    modified_task.activity = str(modified_task_summary_activity)


def get_hours_and_minutes_from_delta(delta) -> list[int]:
    hours_delta = delta.seconds // 3600
    minute_delta = (delta.seconds % 3600) // 60
    return [hours_delta, minute_delta]


def get_active_summary_activity_from_task(task: task_models.Tasks):
    return get_summary_activity(
        int(task.activity.split(":")[0]), int(task.activity.split(":")[1])
    )


def get_summary_activity(hours: int, minutes: int):
    return task_dependencies.SummaryActivity(hours, minutes)


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


def prepare_timeline_time(time: str):
    return datetime.strptime(
        time,
        TIME_FORMAT,
    )


async def get_timeline_via_id(session: AsyncSession, timeline_id: int):
    return await session.get(models.TimeIntervals, timeline_id)


def check_close_timeline(timeline):
    return timeline.time_end.strftime(TIME_FORMAT) != datetime.now().strftime(
        NOT_COMPILE_TIME_FORMAT
    )
