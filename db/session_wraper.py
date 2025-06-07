import functools

from .database import async_session


def with_session(handler):
    @functools.wraps(handler)
    async def wrapper(*args, **kwargs):
        async with async_session() as session:
            kwargs['session'] = session
            return await handler(*args, **kwargs)

    return wrapper
