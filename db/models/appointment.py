from datetime import datetime
from enum import IntEnum

from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from db import Base


class AppointmentStatus(IntEnum):
    PENDING = 0
    CONFIRMED = 1


class Appointment(Base):
    __tablename__ = "appointment"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    status = Column(Integer, nullable=False, default=AppointmentStatus.PENDING)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="appointments")
