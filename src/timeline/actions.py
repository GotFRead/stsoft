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
from copy import deepcopy

logger = create_logger("timeline_actions.log")

timeout_execute_command = 1000

ACTIVITY_TIME_FORMAT = "00:00"
DEFAULT_TIME = "--:--"
TIME_FORMAT = "%Y-%m-%d %H:%M"
NOT_COMPILE_TIME_FORMAT = "%Y-%m-%d 00:00"
DELTA_TIME_FORMAT = "%H:%M"
TODAY_END_TIME_FORMAT = "%Y-%m-%d 23:59"
DATE_FORMAT = "%Y-%m-%d"


async def get_all_timelines():
    """Запрос всех таймлайнов"""
    logger.log_start(get_all_timelines, dict())

    try:
        session = db_helper.get_scoped_session()

        request = select(models.TimeIntervals).order_by(models.TimeIntervals.id)
        result = await session.execute(request)
        result = result.scalars().all()  # (id, prod)
    except Exception as err:
        result = status.HTTP_500_INTERNAL_SERVER_ERROR
        logger.log_exception(get_all_timelines, dict(), err)

    logger.log_complete(get_all_timelines, dict())

    return result


async def delete_timeline(timeline_schema: schemas.DeleteTimeline):
    """Удаление таймлайна"""
    logger.log_start(delete_timeline, timeline_schema)

    try:
        result = await asyncio.wait_for(
            __delete_timeline(timeline_schema), timeout_execute_command
        )

    except asyncio.TimeoutError as err:
        logger.log_exception(delete_timeline, dict(), err)
        result = status.HTTP_500_INTERNAL_SERVER_ERROR

    except Exception as err:
        logger.log_exception(delete_timeline, dict(), err)
        result = status.HTTP_422_UNPROCESSABLE_ENTITY

    logger.log_complete(delete_timeline, dict())

    return result


async def __delete_timeline(timeline_schemas: schemas.DeleteTimeline):
    """Удаление таймлайна"""
    try:
        session = db_helper.get_scoped_session()

        removed_timeline: models.TimeIntervals = await get_timeline_via_id(
            session=session, timeline_id=timeline_schemas.id
        )
        await session.delete(removed_timeline)

        await __actualization_task(session, removed_timeline, False)

        await session.commit()

    except Exception as err:
        logger.log_exception(__delete_timeline, timeline_schemas, err)
        return status.HTTP_400_BAD_REQUEST
    return status.HTTP_200_OK


async def get_timeline_via_id(session: AsyncSession, task_id: int):
    """Получение таймлайна по id в бд"""
    return await session.get(models.TimeIntervals, task_id)


async def create_new_timeline(timeline_schema: schemas.InputTimeline):
    """Создание нового таймлайна"""
    logger.log_start(create_new_timeline, timeline_schema)

    try:
        result = await asyncio.wait_for(
            __create_timeline(timeline_schema), timeout_execute_command
        )

    except asyncio.TimeoutError as err:
        logger.log_exception(create_new_timeline, dict(), err)
        result = status.HTTP_500_INTERNAL_SERVER_ERROR

    except Exception as err:
        logger.log_exception(create_new_timeline, dict(), err)
        result = status.HTTP_422_UNPROCESSABLE_ENTITY

    logger.log_complete(create_new_timeline, dict())

    return result


async def patch_timeline(timeline_schema: schemas.PatchTimeline):
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
    """Остановка таймлайна по id"""
    logger.log_start(stop_timeline, timeline_schema)

    try:
        result = await asyncio.wait_for(
            __stop_timeline(timeline_schema), timeout_execute_command
        )

    except asyncio.TimeoutError as err:
        logger.log_exception(stop_timeline, timeline_schema, err)
        result = status.HTTP_500_INTERNAL_SERVER_ERROR

    except Exception as err:
        logger.log_exception(stop_timeline, timeline_schema, err)
        result = status.HTTP_422_UNPROCESSABLE_ENTITY

    logger.log_complete(stop_timeline, timeline_schema)

    return result


async def get_timelines_all_users(
    timeline_schema: schemas.GetTimelinesAllUsers,
):
    """
    Это решение пункта номер 6 \n

    Получение таймланов всех пользователей
    """
    logger.log_start(get_timelines_all_users, timeline_schema)

    try:
        result = await asyncio.wait_for(
            __get_timelines_all_users(timeline_schema), timeout_execute_command
        )

    except asyncio.TimeoutError as err:
        logger.log_exception(get_timelines_all_users, timeline_schema, err)
        result = status.HTTP_500_INTERNAL_SERVER_ERROR

    except Exception as err:
        logger.log_exception(get_timelines_all_users, timeline_schema, err)
        result = status.HTTP_422_UNPROCESSABLE_ENTITY

    logger.log_complete(get_timelines_all_users, timeline_schema)
    return result


async def get_downtime_and_timelines_for_specified_user(
    timeline_schema: schemas.GetDowntimeForSpecifiedUser,
):
    """Это решение пункта номер 7 \n

    Формирование списка простоев и завершенных таймлайнов в указанных часах рабочего дня
    """
    logger.log_start(
        get_downtime_and_timelines_for_specified_user, timeline_schema
    )

    try:
        result = await asyncio.wait_for(
            __get_downtime_and_timelines_for_specified_user(timeline_schema),
            timeout_execute_command,
        )

    except asyncio.TimeoutError as err:
        logger.log_exception(
            get_downtime_and_timelines_for_specified_user, timeline_schema, err
        )

        result = status.HTTP_500_INTERNAL_SERVER_ERROR

    except Exception as err:
        logger.log_exception(
            get_downtime_and_timelines_for_specified_user, timeline_schema, err
        )
        result = status.HTTP_422_UNPROCESSABLE_ENTITY

    logger.log_complete(
        get_downtime_and_timelines_for_specified_user, timeline_schema
    )

    return result


async def __get_downtime_and_timelines_for_specified_user(
    timeline_schema: schemas.GetDowntimeForSpecifiedUser,
):
    """Формирование списка простоев и завершенных таймлайнов в указанных часах рабочего дня"""

    # конвертация старта и конца таймлайна в datatime
    timeline_schema.time_start = datetime.strptime(
        timeline_schema.time_start, DATE_FORMAT
    ).strftime(NOT_COMPILE_TIME_FORMAT)

    timeline_schema.time_end = datetime.strptime(
        timeline_schema.time_end, DATE_FORMAT
    ).strftime(TODAY_END_TIME_FORMAT)

    # запрос всех таймлайнов

    timelines: list[schemas.CreateTimeline] = await get_users_timelines(
        timeline_schema
    )

    # фомирование словаря с датами указанных пользователем
    date_hashmap = compile_date_hashmap(timeline_schema)

    # добавление завершенных таймлайнов в словарь
    add_timelines_to_hashmap(timelines, date_hashmap)
    # сортировка таймланов в каждой дате
    sort_timelines(date_hashmap)
    # добавление простоев в промежутки рабочего времени, незанятого таймлайнами
    add_downtimes_to_date_hashmap(date_hashmap, timeline_schema)
    # формирование итогового словаря
    convert_result_to_dict(date_hashmap)

    return date_hashmap


def convert_result_to_dict(date_hashmap):
    for date in date_hashmap:
        for interval_index in range(len(date_hashmap[date])):
            if hasattr(date_hashmap[date][interval_index], "dict"):
                date_hashmap[date][interval_index] = (
                    convert_schemas_class_to_dict(
                        date_hashmap[date][interval_index]
                    )
                )

            elif isinstance(
                date_hashmap[date][interval_index], models.TimeIntervals
            ):
                convert_models_mapping_to_dict(
                    date_hashmap[date][interval_index]
                )

            else:
                continue


def sort_timelines(date_hashmap: dict):
    for date in date_hashmap:
        date_hashmap[date] = qsort_timelines_for_time_start(date_hashmap[date])


def add_timelines_to_hashmap(timelines: schemas.CreateTimeline, hashmap: dict):
    """Добавление  таймлайна по дате в словарь"""
    for timeline in timelines:
        timeline_start_date = timeline.time_start.strftime(DATE_FORMAT)

        hashmap[timeline_start_date].append(timeline)


def convert_schemas_class_to_dict(schemas_class: schemas.CreateTimeline):
    key_and_values = dict(schemas_class.__dict__.items())
    schemas_class__ = {
        f"{key}": key_and_values[key] for key in schemas_class.model_fields
    }

    return schemas_class__


def convert_models_mapping_to_dict(models_mapping: models.TimeIntervals):
    models_mapping = {
        f"{key}": value
        for key, value in models_mapping.__table__.columns.items()
    }


def get_timeline_interval(time_start: datetime, time_end: datetime):
    """Получение форматированного временного интервала"""
    # ? После изменения схемы - не используется. Оставил до востребования
    timeline_start_time = time_start.strftime(DELTA_TIME_FORMAT)
    timeline_end_time = time_end.strftime(DELTA_TIME_FORMAT)

    return f"{timeline_start_time}-{timeline_end_time}"


def compile_date_hashmap(timeline_schema):
    """Формирование словаря с датами по схеме"""
    date_hashmap = dict()
    start_date = timeline_schema.time_start.date()
    end_date = timeline_schema.time_end.date()

    date_delta = end_date - start_date

    for day in range(date_delta.days + 1):
        _temp_date = datetime(
            start_date.year, start_date.month, start_date.day + day
        )
        date_hashmap[_temp_date.strftime(DATE_FORMAT)] = list()

    return date_hashmap


def add_downtimes_to_date_hashmap(
    date_hashmap: dict, timeline_schema: schemas.GetDowntimeForSpecifiedUser
):
    """Добавление таймлайнов простоя в сводную по времени"""
    for date in deepcopy(date_hashmap):
        if len(date_hashmap[date]) == 0:
            date_hashmap[date] = [
                convert_schemas_class_to_dict(
                    __compile_downtime_day(timeline_schema, date)
                )
            ]
            continue

        result = list()

        for timelines_index in range(len(date_hashmap[date])):
            timeline: models.TimeIntervals = deepcopy(
                date_hashmap[date][timelines_index]
            )
            if timelines_index == 0:
                compile_start_downtime_list(
                    timeline, timeline_schema, date, result
                )
            else:
                previous_timeline: models.TimeIntervals = date_hashmap[date][
                    timelines_index - 1
                ]
                compile_middle_downtime_list(
                    timeline, previous_timeline, timeline_schema, date, result
                )

            if timelines_index == len(date_hashmap[date]) - 1:
                compile_end_downtime_list(
                    timeline, timeline_schema, date, result
                )

        date_hashmap[date] = result

    return date_hashmap


def compile_start_downtime_list(
    timeline: models.TimeIntervals,
    timeline_schema: schemas.GetDowntimeForSpecifiedUser,
    exodus_date: str,
    downtime_list: list,
):
    """Фомирование начала списка временного интервала, для указания времени простоев"""
    if (
        timeline.time_start.strftime(DELTA_TIME_FORMAT)
        <= timeline_schema.time_start_work
    ):
        downtime_list.append(timeline)
        return

    downtime_timeline = compile_downtime_for_start_time_interval(
        exodus_date, timeline_schema, timeline
    )

    downtime_list.append(convert_schemas_class_to_dict(downtime_timeline))
    downtime_list.append(timeline)


def compile_middle_downtime_list(
    timeline: models.TimeIntervals,
    previous_timeline: models.TimeIntervals,
    timeline_schema: schemas.GetDowntimeForSpecifiedUser,
    exodus_date: str,
    downtime_list: list,
):
    """Фомирование середины списка временного интервала, для указания времени простоев"""
    if previous_timeline.time_end.strftime(
        DELTA_TIME_FORMAT
    ) == timeline.time_start.strftime(DELTA_TIME_FORMAT):
        return

    downtime_timeline = compile_downtime_for_middle_time_interval(
        exodus_date, timeline, previous_timeline, timeline_schema
    )

    downtime_list.append(convert_schemas_class_to_dict(downtime_timeline))
    downtime_list.append(timeline)


def compile_end_downtime_list(
    timeline: models.TimeIntervals,
    timeline_schema: schemas.GetDowntimeForSpecifiedUser,
    exodus_date: str,
    downtime_list: list,
):
    """Фомирование конца списка временного интервала, для указания времени простоев"""
    if (
        timeline.time_end.strftime(DELTA_TIME_FORMAT)
        >= timeline_schema.time_end_work
    ):
        return

    downtime_timeline = compile_downtime_for_end_time_interval(
        exodus_date, timeline, timeline_schema
    )

    downtime_list.append(convert_schemas_class_to_dict(downtime_timeline))


def compile_downtime_for_start_time_interval(
    date: str, timeline_schema, timeline: models.TimeIntervals
):
    """Формирование простоя в начале временного интервала"""
    return get_downtime_timeline(
        datetime(
            year=int(date.split("-")[0]),
            month=int(date.split("-")[1]),
            day=int(date.split("-")[2]),
            hour=int(timeline_schema.time_start_work.split(":")[0]),
            minute=int(timeline_schema.time_start_work.split(":")[1]),
        ),
        datetime(
            year=int(date.split("-")[0]),
            month=int(date.split("-")[1]),
            day=int(date.split("-")[2]),
            hour=int(timeline.time_start.hour),
            minute=int(timeline.time_start.minute),
        ),
        timeline_schema.user_id,
    )


def compile_downtime_for_middle_time_interval(
    date: str,
    timeline: models.TimeIntervals,
    previous_timeline: models.TimeIntervals,
    timeline_schema,
):
    """Формирование простоя в середине временного интервала"""
    return get_downtime_timeline(
        datetime(
            year=int(date.split("-")[0]),
            month=int(date.split("-")[1]),
            day=int(date.split("-")[2]),
            hour=int(previous_timeline.time_end.hour),
            minute=int(previous_timeline.time_end.minute),
        ),
        datetime(
            year=int(date.split("-")[0]),
            month=int(date.split("-")[1]),
            day=int(date.split("-")[2]),
            hour=int(timeline.time_start.hour),
            minute=int(timeline.time_start.minute),
        ),
        timeline_schema.user_id,
    )


def compile_downtime_for_end_time_interval(
    date: str,
    timeline: models.TimeIntervals,
    timeline_schema,
):
    """Формирование простоя в конце временного интервала"""
    return get_downtime_timeline(
        datetime(
            year=int(date.split("-")[0]),
            month=int(date.split("-")[1]),
            day=int(date.split("-")[2]),
            hour=int(timeline.time_end.hour),
            minute=int(timeline.time_end.minute),
        ),
        datetime(
            year=int(date.split("-")[0]),
            month=int(date.split("-")[1]),
            day=int(date.split("-")[2]),
            hour=int(timeline_schema.time_end_work.split(":")[0]),
            minute=int(timeline_schema.time_end_work.split(":")[1]),
        ),
        timeline_schema.user_id,
    )


def get_downtime_timeline(
    time_start: datetime, time_end: datetime, user_id: int
):
    return __create_temp_timeline(
        time_start,
        time_end,
        user_id,
    )


def __compile_downtime_day(
    timeline_schema: schemas.GetDowntimeForSpecifiedUser, date: str
):
    """Создание дня-простоя по схеме таймлайна"""
    return __create_downtime_via_timeline_schema(timeline_schema, date)


def __create_downtime_via_timeline_schema(
    timeline_schema: schemas.GetDowntimeForSpecifiedUser, date: str
):
    """Создание таймлайна-простоя по схеме таймлайна"""
    return __create_temp_timeline(
        datetime(
            year=int(date.split("-")[0]),
            month=int(date.split("-")[1]),
            day=int(date.split("-")[2]),
            hour=int(timeline_schema.time_start_work.split(":")[0]),
            minute=int(timeline_schema.time_start_work.split(":")[1]),
        ),
        datetime(
            year=int(date.split("-")[0]),
            month=int(date.split("-")[1]),
            day=int(date.split("-")[2]),
            hour=int(timeline_schema.time_end_work.split(":")[0]),
            minute=int(timeline_schema.time_end_work.split(":")[1]),
        ),
        timeline_schema.user_id,
    )


def __create_temp_timeline(
    time_start: datetime,
    time_end: datetime,
    owner_id: int,
    task_id: str = "EXECUTABLE TASK NOT FOUND!",
    description: str = "DOWNTIME",
    activity="00:00",
    id_: str = "This is downtime timeline, 'id' - NOT EXIST",
):
    """Создание таймлайна-затычки для указания простоя"""
    timeline = schemas.CreateTimeline
    timeline.time_start = time_start
    timeline.time_end = time_end
    timeline.owner_id = owner_id
    timeline.task_id = task_id
    timeline.activity = activity
    timeline.id = id_
    timeline.description = description

    __compile_activity(timeline, timeline)

    return timeline


async def get_summary_timelines_for_specified_user(
    timeline_schema: schemas.GetSummaryTimelinesForSpecifiedUser,
):
    """Это решение пункта номер 8"""
    logger.log_start(get_summary_timelines_for_specified_user, timeline_schema)
    try:
        result = await asyncio.wait_for(
            __get_summary_timelines_for_specified_user(timeline_schema),
            timeout_execute_command,
        )

    except asyncio.TimeoutError as err:
        logger.log_exception(
            get_summary_timelines_for_specified_user, timeline_schema, err
        )
        result = status.HTTP_500_INTERNAL_SERVER_ERROR

    except Exception as err:
        logger.log_exception(
            get_summary_timelines_for_specified_user, timeline_schema, err
        )
        result = status.HTTP_422_UNPROCESSABLE_ENTITY

    logger.log_complete(
        get_summary_timelines_for_specified_user, timeline_schema
    )
    return result


async def __get_summary_timelines_for_specified_user(
    timeline_schema: schemas.GetSummaryTimelinesForSpecifiedUser,
):
    summary_activity = {
        "user_id": timeline_schema.user_id,
        "summary": get_summary_activity(
            int(schemas.ACTIVITY_TIME_FORMAT.split(":")[0]),
            int(schemas.ACTIVITY_TIME_FORMAT.split(":")[1]),
        ),
    }

    timelines = await get_users_timelines(timeline_schema)

    for timeline in timelines:
        timeline_activity_ = get_active_summary_activity_from_task(timeline)
        summary_activity["summary"].hours += timeline_activity_.hours
        summary_activity["summary"].minutes += timeline_activity_.minutes

    return summary_activity


async def __get_timelines_all_users(
    timeline_schema: schemas.GetTimelinesAllUsers,
):
    """Получение таймлайнов всех пользователей"""
    logger.log_start(__get_timelines_all_users, timeline_schema)
    try:

        compile_timelines_range(timeline_schema)

        timelines: list[schemas.CreateTimeline] = await get_all_timelines()

        result = __get_all_timeline_in_the_range(
            timeline_schema.time_start, timeline_schema.time_end, timelines
        )

    except Exception as err:
        logger.log_exception(__get_timelines_all_users, timeline_schema, err)
        return status.HTTP_400_BAD_REQUEST

    logger.log_complete(__get_timelines_all_users, timeline_schema)
    return result


def compile_timelines_range(timeline_schema: schemas.GetTimelinesAllUsers):
    """Формирование старта и начала таймлайна"""
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
    """Получение всех таймлайнов в диапазоне времени"""
    result = []
    for current_timeline in timelines_list:
        # ? На подумать, нужно ли игнорировать не закрытые таймлайны
        # ? В задаче не было описано данной ситуации - поэтому не игнорирую
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


async def __create_timeline(timeline_schema: schemas.InputTimeline):
    """Создание таймлайна"""

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

    # создание временной схемы
    prepared_timeline_schema = prepare_timeline_schemas(timeline_schema)
    if prepared_timeline_schema.time_end.strftime(
        TIME_FORMAT
    ) != datetime.now().strftime(NOT_COMPILE_TIME_FORMAT):

        # Проверка корректности указания старта и конца таймлайна
        if (
            prepared_timeline_schema.time_end
            < prepared_timeline_schema.time_start
        ):
            raise Exception(
                f"End timeline - {prepared_timeline_schema.time_end } > {prepared_timeline_schema.time_start}"
            )

        checked_delta = (
            prepared_timeline_schema.time_end
            - prepared_timeline_schema.time_start
        )

        # Если таймлайн больше одного дня - он будет считаться некорректным
        if checked_delta.days != 0:
            raise Exception(
                f"Detect incorrect delta between {prepared_timeline_schema.time_end } and {prepared_timeline_schema.time_start} delta - {checked_delta}"
            )

    # Если таймаут создан, но не имеет даты в конце, то он не считается закрытым, и не имеет просчитанной активности
    if prepared_timeline_schema.time_end.strftime(
        TIME_FORMAT
    ) != datetime.now().strftime(NOT_COMPILE_TIME_FORMAT):
        __get_timeline_activity(prepared_timeline_schema)

    schemas_mapping = prepare_schemas_mapping(prepared_timeline_schema)

    try:
        session = db_helper.get_scoped_session()

        new_timeline = models.TimeIntervals(**schemas_mapping)

        session.add(new_timeline)

        # актуализирую задачу, к которой отнесен создаваемый таймлайн
        await __actualization_task(session, prepared_timeline_schema)

        await session.commit()

    except Exception as err:
        logger.log_exception(
            __create_timeline,
            timeline_schema,
            err,
        )
        return status.HTTP_400_BAD_REQUEST

    return status.HTTP_200_OK


def prepare_schemas_mapping(timeline_schema: schemas.PatchTimeline):
    """Конвертация схемы в словарь"""
    result = convert_schemas_class_to_dict(timeline_schema)
    del result["id"]
    return result


def prepare_timeline_schemas(timeline_schema: schemas.CreateTimeline):
    """Формирование подготовленной схемы на основе patch- схемы"""
    prepared_timeline_schema = schemas.PatchTimeline
    prepared_timeline_schema.id = "terminator"
    prepared_timeline_schema.task_id = timeline_schema.task_id
    prepared_timeline_schema.owner_id = timeline_schema.owner_id
    prepared_timeline_schema.description = timeline_schema.description
    prepared_timeline_schema.time_start = timeline_schema.time_start
    prepared_timeline_schema.time_end = timeline_schema.time_end
    prepared_timeline_schema.activity = (
        f"{datetime.today().strftime(ACTIVITY_TIME_FORMAT)}"
    )
    return prepared_timeline_schema


def __get_timeline_activity(timeline_schema: schemas.CreateTimeline):
    """Получение протяженности таймлайна по схеме"""
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


async def get_all_timeline_in_the_range_for_specified_user(
    timeline_schema: schemas.GetTimelinesForSpecifiedUser,
):
    """Это решение пункта номер 5 \n

    Получение всех таймлайнов в диапазоне, для конкретного пользователя
    """
    logger.log_start(
        get_all_timeline_in_the_range_for_specified_user, timeline_schema
    )
    try:

        result = qsort_timelines_for_activity(
            await get_users_timelines(timeline_schema)
        )

    except Exception as err:
        logger.log_exception(
            get_all_timeline_in_the_range_for_specified_user,
            timeline_schema,
            err,
        )
        return status.HTTP_400_BAD_REQUEST

    logger.log_complete(
        get_all_timeline_in_the_range_for_specified_user, timeline_schema
    )

    return result


async def get_users_timelines(timeline_schema):

    compile_timelines_range(timeline_schema)

    timelines: list[schemas.CreateTimeline] = await get_all_timelines()

    suitable_timelines = __get_all_timeline_in_the_range(
        timeline_schema.time_start, timeline_schema.time_end, timelines
    )

    return get_timelines_for_specified_user(
        suitable_timelines, timeline_schema.user_id
    )


def get_activity_second(activity: str):
    hours, minutes = activity.split(":")

    return int(hours) * 3600 + int(minutes) * 60


def sort(array):
    """Sort the array by using quicksort."""

    less = []
    equal = []
    greater = []

    if len(array) > 1:
        pivot = array[0]
        for x in array:
            if x[1] < pivot[1]:
                less.append(x)
            elif x[1] == pivot[1]:
                equal.append(x)
            elif x[1] > pivot[1]:
                greater.append(x)
        return sort(less) + equal + sort(greater)
    else:
        return array


def qsort_timelines_for_time_start(array):
    """Сортировка таймлайнов по времени старта"""
    result = []
    tasks_seconds_array = [(x, array[x].time_start) for x in range(len(array))]

    res = qsort_timelines(tasks_seconds_array)

    for x in res:
        result.append(array[x[0]])

    return result


def qsort_timelines_for_activity(array):
    """Сортировка таймлайнов по активности"""
    result = []
    tasks_seconds_array = [
        (x, get_activity_second(array[x].activity)) for x in range(len(array))
    ]

    res = qsort_timelines(tasks_seconds_array)[::-1]

    for x in res:
        result.append(array[x[0]])

    return result


def qsort_timelines(array):
    """Быстрая сортировка массива"""

    result = []

    res = sort(array)

    for x in res:
        result.append(array[x[0]])

    return result


def get_timelines_for_specified_user(
    timelines: list[schemas.CreateTimeline], user_id: int
):
    """Получение таймлайнов конкретного пользователя"""
    result = []
    for timeline in timelines:
        if timeline.owner_id == user_id:
            result.append(timeline)

    return result


async def __actualization_task(
    session: AsyncSession,
    timeline_schema: schemas.CreateTimeline,
    add_timeline: bool = True,
):
    """Актуализация задач"""

    if timeline_schema.time_end.strftime(
        TIME_FORMAT
    ) == datetime.now().strftime(NOT_COMPILE_TIME_FORMAT):
        return None

    modified_task: task_models.Tasks = await task_actions.get_task_via_id(
        session, timeline_schema.task_id
    )

    __compile_activity(timeline_schema, modified_task, add_timeline)


def __compile_activity(
    timeline_schema: schemas.CreateTimeline,
    modified_activity_object: object,
    add_timeline: bool = True,
):
    """Формирование активности"""

    delta = timeline_schema.time_end - datetime.strptime(
        timeline_schema.time_start.strftime(TIME_FORMAT), TIME_FORMAT
    )

    if isinstance(modified_activity_object, task_models.Tasks):
        modified_summary_activity = get_active_summary_activity_from_task(
            modified_activity_object
        )
    elif modified_activity_object == schemas.CreateTimeline:
        modified_summary_activity = get_summary_activity_from_timeline_schema(
            modified_activity_object
        )
    elif modified_activity_object == schemas.PatchTimeline:
        modified_summary_activity = get_summary_activity_from_timeline_schema(
            modified_activity_object
        )
    else:
        raise Exception("Found UNKNOWN class modified_activity_object !")

    hours_delta, minute_delta = get_hours_and_minutes_from_delta(delta)

    if add_timeline:
        # Просчет суммарной активности при добавлении таймлайна
        modified_summary_activity.hours = (
            modified_summary_activity.hours + hours_delta
        )
        modified_summary_activity.minutes = (
            modified_summary_activity.minutes + minute_delta
        )
    else:
        # Просчет суммарной активности при удалении таймлайна
        modified_summary_activity.hours = (
            modified_summary_activity.hours - hours_delta
        )
        modified_summary_activity.minutes = (
            modified_summary_activity.minutes - minute_delta
        )

    modified_activity_object.activity = str(modified_summary_activity)


def get_hours_and_minutes_from_delta(delta) -> list[int]:
    """Получение часов и минут из datatime.delta"""
    hours_delta = delta.seconds // 3600
    minute_delta = (delta.seconds % 3600) // 60
    return [hours_delta, minute_delta]


def get_active_summary_activity_from_task(task: task_models.Tasks):
    """Получение сводной активности из задачи"""
    return get_summary_activity(
        int(task.activity.split(":")[0]), int(task.activity.split(":")[1])
    )


def get_summary_activity_from_timeline_schema(
    timeline_schema: schemas.CreateTimeline,
):
    """Получение сводной активности из схемы таймлайна"""
    return get_summary_activity(
        int(timeline_schema.activity.split(":")[0]),
        int(timeline_schema.activity.split(":")[1]),
    )


def get_summary_activity(hours: int, minutes: int):
    return task_dependencies.SummaryActivity(hours, minutes)


async def __patch_timeline(new_timeline_schema: schemas.PatchTimeline):
    """Изменение таймлайна"""
    logger.info(f"Start create TimeIntervals - {new_timeline_schema}")
    try:

        session = db_helper.get_scoped_session()

        changed_timeline: models.TimeIntervals = await get_timeline_via_id(
            session=session, timeline_id=new_timeline_schema.id
        )

        copy_for_change_task = deepcopy(changed_timeline)

        changed_timeline: models.TimeIntervals = override_changed_property(
            new_timeline_schema, changed_timeline
        )

        changed_timeline = convert_str_to_datetime(changed_timeline)

        __get_timeline_activity(changed_timeline)

        # Удаляем часы с задачи которой был прикреплен таймлайн
        await __actualization_task(session, copy_for_change_task, False)

        # Добавляем часы к соответствующей задаче
        await __actualization_task(session, changed_timeline)

        session.add(changed_timeline)

        await session.commit()

    except Exception as err:
        logger.error(f"__patch_timeline raise exception - {err}")
        return status.HTTP_400_BAD_REQUEST

    return status.HTTP_200_OK


def override_changed_property(
    new_timeline_schema: schemas.PatchTimeline,
    changed_timeline: models.TimeIntervals,
):

    for name, value in new_timeline_schema.dict().items():
        attr = getattr(new_timeline_schema, name)
        if isinstance(attr, str) and "This field will be not modified" in attr:
            # Проверка поля (при указанном значении поле будет проигнорировано)
            continue
        setattr(changed_timeline, name, value)

    return changed_timeline


def convert_str_to_datetime(timeline: schemas.CreateTimeline):
    for time_section in ["time_end", "time_start"]:
        attr = getattr(timeline, time_section)
        if isinstance(attr, str):
            setattr(timeline, time_section, prepare_timeline_time(attr))
        continue

    return timeline


def prepare_timeline_time(time: str):
    """Формирование datatime по разметке"""
    return datetime.strptime(
        time,
        TIME_FORMAT,
    )


async def get_timeline_via_id(session: AsyncSession, timeline_id: int):
    """Получение таймлайна по номеру в бд"""
    return await session.get(models.TimeIntervals, timeline_id)


def check_close_timeline(timeline):
    """Проверка закрытости таймлайна"""
    return timeline.time_end.strftime(TIME_FORMAT) != datetime.now().strftime(
        NOT_COMPILE_TIME_FORMAT
    )
