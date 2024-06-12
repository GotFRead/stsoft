
# __fastapi_depend__

from fastapi import APIRouter
from fastapi import Request

from helpers.file_helper import get_static_file
# __router__

router = APIRouter(tags=["base"])