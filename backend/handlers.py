from fastapi import Request
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from config import app_config

templates = app_config.TEMPLATES


async def not_found_handler(request: Request, exc: Exception):
    if isinstance(exc, StarletteHTTPException):
        if exc.status_code == 404:
            return templates.TemplateResponse("errors/404.html", {"request": request}, status_code=404)
        if exc.status_code == 403:
            return templates.TemplateResponse("errors/403.html", {"request": request}, status_code=403)
    return JSONResponse({"detail": str(exc)}, status_code=500)
