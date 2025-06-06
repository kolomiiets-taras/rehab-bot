from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

router = APIRouter()


@router.get("/")
async def redirect_to_users(request: Request):
    return RedirectResponse(url="/users", status_code=303)


@router.get("/healthcheck")
async def healthcheck():
    return {"status": "healthy", "service": "spina-rehab-api"}
