from contextlib import asynccontextmanager

from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.handlers import not_found_handler
from app.middlewares.auth_middleware import auth_middleware
from app.middlewares.log_middleware import log_middleware
from app.routers import (
    login_router,
    users_router,
    employees_router,
    exercises_router,
    api_router,
    complexes_router,
    courses_router,
    mailing_router,
    index_router,
    motivation_router
)
from app.db.connector import create_db_and_tables, drop_db_tables, add_first_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    # await populate_test_data()
    # await add_first_admin()
    yield
    # await drop_db_tables()


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="./static"), name="static")

app.middleware("http")(log_middleware)
app.middleware("http")(auth_middleware)
app.add_exception_handler(StarletteHTTPException, not_found_handler)


app.include_router(login_router, tags=["login"])
app.include_router(index_router, tags=["index"])
app.include_router(api_router, tags=["api"])
app.include_router(users_router, tags=["users"])
app.include_router(employees_router, tags=["employees"])
app.include_router(exercises_router, tags=["exercises"])
app.include_router(complexes_router, tags=["complexes"])
app.include_router(courses_router, tags=["courses"])
app.include_router(mailing_router, tags=["mailing"])
app.include_router(motivation_router, tags=["motivation"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
