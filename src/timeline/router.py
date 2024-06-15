from . import actions
from . import schemas

# __fastapi_depend__

from fastapi import APIRouter


# __router__

router = APIRouter(tags=["time_interval"], prefix="/timelines")


@router.get("/")
async def get_all_timelines():
    return await actions.get_all_timelines()


@router.post("/create_new_timeline")
async def create_new_timelines(timeline_schema: schemas.CreateTimeline):
    return await actions.create_new_timeline(timeline_schema)


@router.post("/stop_timeline")
async def stop_timeline(timeline_schema: schemas.StopTimeline):
    return await actions.stop_timeline(timeline_schema)


@router.post("/get_timelines_all_users")
async def get_timelines_all_users(
    timeline_schema: schemas.GetTimelinesAllUsers,
):
    return await actions.get_timelines_all_users(timeline_schema)


@router.post("/get_timelines_for_specified_user")
async def get_timelines_for_specified_user(
    timeline_schema: schemas.GetTimelinesForSpecifiedUser,
):
    return await actions.get_all_timeline_in_the_range_for_specified_user(
        timeline_schema
    )


@router.post("/get_summary_timeline_for_specified_user")
async def get_summary_timeline_for_specified_user(
    timeline_schema: schemas.GetSummaryTimelinesForSpecifiedUser,
):
    return await actions.get_summary_timelines_for_specified_user(
        timeline_schema
    )