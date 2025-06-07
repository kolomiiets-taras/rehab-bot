from datetime import datetime
from enum import IntEnum

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Boolean, Text, Time, BigInteger, ARRAY
from sqlalchemy.orm import relationship

from config import app_config
from db import Base


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=True, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    birthday = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.now, index=True)
    language = Column(String(10), nullable=True, default=app_config.DEFAULT_LANGUAGE)

    courses = relationship("UserCourse", back_populates="user", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="user", cascade="all, delete-orphan")


class UserCourse(Base):
    __tablename__ = "user_course"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    progress = Column(Text, nullable=True)
    current_position = Column(Integer, nullable=False, default=0)
    finished = Column(Boolean, nullable=True, default=False)
    mailing_time = Column(Time, nullable=True)
    mailing_days = Column(ARRAY(Integer), nullable=False, default=lambda: [])
    iterations = Column(Integer, nullable=False, default=1)
    current_iteration = Column(Integer, nullable=False, default=1)

    user = relationship("User", back_populates="courses")
    course = relationship("Course", back_populates="users")
    sessions = relationship("DailySession", order_by="DailySession.position", back_populates="user_course",
                            cascade="all, delete-orphan")

    @property
    def days_str(self) -> str:
        if not self.mailing_days:
            return ""
        mapping = {1: 'Пн', 2: 'Вт', 3: 'Ср', 4: 'Чт', 5: 'Пт', 6: 'Сб', 7: 'Нд'}
        return ', '.join([mapping[day] for day in self.mailing_days if day in mapping])

    @property
    def current_item_index(self) -> int:
        """Calculate the relative position in the current iteration."""
        return self.current_position % self.course.items_count


class DailySessionState(IntEnum):
    NOT_SENT = 0
    SENT = 1
    IN_PROGRESS = 2
    FINISHED = 3
    SKIPPED = 4


class DailySession(Base):
    __tablename__ = "daily_session"

    id = Column(Integer, primary_key=True, index=True)
    user_course_id = Column(Integer, ForeignKey("user_course.id", ondelete="CASCADE"), nullable=False)
    course_item_id = Column(Integer, ForeignKey("course_item.id", ondelete="CASCADE"), nullable=False)
    state = Column(Integer, nullable=False, default=DailySessionState.NOT_SENT)
    date = Column(Date, nullable=False)
    position = Column(Integer, nullable=False, default=0)
    pulse_before = Column(Integer, nullable=True)
    pulse_after = Column(Integer, nullable=True)
    # 1 - 5
    wellbeing_before = Column(Integer, nullable=True)
    wellbeing_after = Column(Integer, nullable=True)

    user_course = relationship("UserCourse", back_populates="sessions")
    course_item = relationship("CourseItem", back_populates="sessions")
