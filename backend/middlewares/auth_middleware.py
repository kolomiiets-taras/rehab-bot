from starlette.requests import Request
from starlette.responses import Response, RedirectResponse
from backend.routers.jwt_utils import verify_token
from db import async_session
from db.models import Employee
from sqlalchemy import select


async def auth_middleware(request: Request, call_next) -> Response:
    token = request.cookies.get("access_token")
    request.state.user = None
    public_paths = {"/login", "/signup", "/static", "/favicon.ico"}

    if any(request.url.path.startswith(path) for path in public_paths):
        return await call_next(request)

    if token:
        email = verify_token(token)
        if email:
            async with async_session() as session:
                result = await session.execute(select(Employee).where(Employee.email == email))
                user = result.scalar_one_or_none()
                if user:
                    request.state.user = user
        else:
            return RedirectResponse(url="/login", status_code=303)
    else:
        return RedirectResponse(url="/login", status_code=303)

    response = await call_next(request)
    return response
