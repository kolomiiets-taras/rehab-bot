from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from config import app_config
from backend.handlers import not_found_handler
from backend.middlewares.auth_middleware import auth_middleware
from backend.middlewares.log_middleware import log_middleware
from backend.routers import (
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
from db.connector import create_db_and_tables


class ProxyHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware для правильної обробки HTTPS через nginx proxy"""

    async def dispatch(self, request: Request, call_next):
        # Встановлюємо HTTPS якщо запит прийшов через nginx
        if request.headers.get("x-forwarded-proto") == "https":
            # Змінюємо схему на HTTPS
            request.scope["scheme"] = "https"
            # Встановлюємо правильний порт
            request.scope["server"] = (request.scope["server"][0], 443)

        response = await call_next(request)
        return response


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

# Додаємо middleware для обробки proxy заголовків ПЕРШИМ
app.add_middleware(ProxyHeadersMiddleware)

# Довіряємо лише певним хостам
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["spina.in.ua", "www.spina.in.ua", "localhost", "127.0.0.1"]
)

# Монтуємо статичні файли
app.mount("/static", StaticFiles(directory=app_config.STATIC_PATH), name="static")

# Додаємо власні middleware
app.middleware("http")(log_middleware)
app.middleware("http")(auth_middleware)

# Обробник виключень
app.add_exception_handler(StarletteHTTPException, not_found_handler)

# Підключаємо маршрути
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
    import asyncio
    from db.connector import add_first_admin
    asyncio.run(add_first_admin())

    uvicorn.run(app, host="0.0.0.0", port=8000, proxy_headers=True)