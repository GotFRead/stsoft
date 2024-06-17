import asyncio

from . import schemas
from . import models

from fastapi import status
from models.db_helper import db_helper
from helpers.logger import create_logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


logger = create_logger("user_actions.log")

timeout_execute_command = 1000


async def get_all_users():
    logger.log_start(get_all_users, dict())

    try:
        session = db_helper.get_scoped_session()
        request = select(models.Users).order_by(models.Users.id)
        result = await session.execute(request)
        timelines = result.scalars().all()  # (id, prod)
    except Exception as err:
        logger.log_exception(get_all_users, dict(), err)
        return status.HTTP_400_BAD_REQUEST

    logger.log_complete(get_all_users, dict())
    return timelines


async def create_user(user_schemas: schemas.CreateUser):
    try:
        result = await asyncio.wait_for(
            __create_user(user_schemas), timeout_execute_command
        )

    except asyncio.TimeoutError as err:
        logger.error(f"create_user raise exception - {err}")
        result = status.HTTP_500_INTERNAL_SERVER_ERROR

    except Exception as err:
        logger.error(f"create_user raise exception - {err}")
        result = status.HTTP_422_UNPROCESSABLE_ENTITY

    return result


async def __create_user(user_schemas: schemas.CreateUser):
    logger.info(f"Start create user - {user_schemas}")
    try:
        session = db_helper.get_scoped_session()

        new_user = models.Users(**user_schemas.dict())

        session.add(new_user)

        await session.commit()

    except Exception as err:
        logger.error(f"create_user raise exception - {err}")
        return status.HTTP_400_BAD_REQUEST
    return status.HTTP_200_OK


async def patch_user(user_schemas: schemas.CreateUser):
    try:
        result = await asyncio.wait_for(
            __patch_user(user_schemas), timeout_execute_command
        )

    except asyncio.TimeoutError as err:
        logger.error(f"create_user raise exception - {err}")
        result = status.HTTP_500_INTERNAL_SERVER_ERROR

    except Exception as err:
        logger.error(f"create_user raise exception - {err}")
        result = status.HTTP_422_UNPROCESSABLE_ENTITY

    return result


async def delete_user(user_schemas: schemas.DeleteUser):
    try:
        result = await asyncio.wait_for(
            __delete_user(user_schemas), timeout_execute_command
        )

    except asyncio.TimeoutError as err:
        logger.error(f"create_user raise exception - {err}")
        result = status.HTTP_500_INTERNAL_SERVER_ERROR

    except Exception as err:
        logger.error(f"create_user raise exception - {err}")
        result = status.HTTP_422_UNPROCESSABLE_ENTITY

    return result


async def __patch_user(user_schemas: schemas.CreateUser):
    logger.info(f"Start patch user - {user_schemas}")
    try:
        session = db_helper.get_scoped_session()

        new_user = await __update_user_info_partial(session, user_schemas)

        session.add(new_user)

        await session.commit()

    except Exception as err:
        logger.error(f"patch user raise exception - {err}")
        return status.HTTP_400_BAD_REQUEST
    return status.HTTP_200_OK


async def __delete_user(user_schemas: schemas.DeleteUser):
    try:
        session = db_helper.get_scoped_session()

        logger.info(f"Start remove user - {user_schemas}")
        removed_user: models.Users = await __get_user_via_id(
            session=session, user_id=user_schemas.id
        )
        await session.delete(removed_user)

        await session.commit()

    except Exception as err:
        logger.error(f"remove user raise exception - {err}")
        return status.HTTP_400_BAD_REQUEST
    return status.HTTP_200_OK


async def __update_user_info_partial(
    session: AsyncSession, user_schemas: schemas.CreateUser
):

    changed_user: models.Users = await __get_user_via_id(
        session=session, user_id=user_schemas.id
    )

    for name, value in user_schemas.dict().items():
        if getattr(user_schemas, name) == "This field will be not modified":
            continue
        setattr(changed_user, name, value)

    return changed_user


async def __get_user_via_id(session: AsyncSession, user_id: int):
    return await session.get(models.Users, user_id)
