# __fastapi_depend__

from fastapi import APIRouter
from fastapi import Request

from src.helpers.file_helper import get_static_file
# __router__

router = APIRouter(tags=["time_interval"])