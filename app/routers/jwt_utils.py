from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.config import app_config


def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=60)):
    to_encode = data.copy()
    expire = datetime.now() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, app_config.SECRET_KEY, algorithm=app_config.ALGORITHM)


def verify_token(token: str):
    try:
        payload = jwt.decode(token, app_config.SECRET_KEY, algorithms=[app_config.ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
