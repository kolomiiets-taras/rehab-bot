from datetime import datetime

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Boolean, Text, Time, BigInteger
from sqlalchemy.orm import relationship

from app.config import app_config
from app.db import Base


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
    mailing_days = Column(String(100), nullable=True, default="")

    user = relationship("User", back_populates="courses")
    course = relationship("Course", back_populates="users")
    sessions = relationship("DailySession", order_by="DailySession.position", back_populates="user_course", cascade="all, delete-orphan")

    @property
    def cron_expression(self) -> str:
        if not self.mailing_time or not self.mailing_days:
            return ""
        hour = self.mailing_time.hour
        minute = self.mailing_time.minute
        return f"{minute:02d} {hour:02d} * * {self.mailing_days}"

    @property
    def days_str(self) -> str:
        if not self.mailing_days:
            return ""
        mapping = {'1': 'Пн', '2': 'Вт', '3': 'Ср', '4': 'Чт', '5': 'Пт', '6': 'Сб', '7': 'Нд'}
        return ', '.join([mapping[day] for day in self.mailing_days.split(',') if day in mapping])


class DailySession(Base):
    __tablename__ = "daily_session"

    id = Column(Integer, primary_key=True, index=True)
    user_course_id = Column(Integer, ForeignKey("user_course.id", ondelete="CASCADE"), nullable=False)
    course_item_id = Column(Integer, ForeignKey("course_item.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    position = Column(Integer, nullable=False, default=0)
    pulse_before = Column(Integer, nullable=True)
    pulse_after = Column(Integer, nullable=True)
    # 1 - 5
    wellbeing_before = Column(Integer, nullable=True)
    wellbeing_after = Column(Integer, nullable=True)

    user_course = relationship("UserCourse", back_populates="sessions")
    course_item = relationship("CourseItem", back_populates="sessions")
