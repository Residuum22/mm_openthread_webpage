
from fastapi import APIRouter
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String

router_database = APIRouter(
    prefix="/routers",
    tags=["routers"]
)

