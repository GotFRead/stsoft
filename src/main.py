from fastapi import FastAPI
from contextlib import asynccontextmanager
from models.db_helper import db_helper
from models.base import Base
from alembic.config import Config
from alembic import command

# __routers__

from routes import router
from users.router import router as usr_router
from tasks_users.router import router as tasks_users_router
from timeline.router import router as time_interval_router

import uvicorn
import asyncio


loop = asyncio.get_event_loop()

# __lifespan__


def run_migrations():
    alembic_config = Config("alembic.ini")
    command.upgrade(alembic_config, "718bcd5cfff0")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # run_migrations()    

    async with db_helper.engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield


# __web_server__
app = FastAPI(lifespan=lifespan, debug=True)

app.include_router(router)
app.include_router(usr_router)
app.include_router(tasks_users_router)
app.include_router(time_interval_router)


def run_server():
    uvicorn.run("main:app", host="0.0.0.0", port=8000, loop="asyncio")


if __name__ == "__main__":
    run_server()
