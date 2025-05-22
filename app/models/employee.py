from datetime import datetime
from enum import IntEnum

from app.db import Base
from sqlalchemy import Column, String, Integer, DateTime


class Role(IntEnum):
    OWNER = 0
    ADMIN = 1
    DOCTOR = 2


class Employee(Base):
    __tablename__ = "employee"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(20), unique=True, index=True)
    password = Column(String(128))
    first_name = Column(String(128))
    last_name = Column(String(128))
    phone = Column(String(20), unique=True, nullable=True, index=True)
    role = Column(Integer, nullable=False)  # 0 - owner, 1 - admin, 2 - doctor
    created_at = Column(DateTime, default=datetime.now)
