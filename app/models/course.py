from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from app.db import Base


class Course(Base):
    __tablename__ = "course"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)

    items = relationship("CourseItem", back_populates="course", order_by="CourseItem.position")
    users = relationship("UserCourse", back_populates="course", cascade="all, delete-orphan")


class CourseItem(Base):
    __tablename__ = "course_item"

    id = Column(Integer, primary_key=True)
    complex_id = Column(Integer, ForeignKey("complex.id", ondelete="CASCADE"), nullable=True)
    exercise_id = Column(Integer, ForeignKey("exercise.id", ondelete="CASCADE"), nullable=True)
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"))
    position = Column(Integer, nullable=False)

    course = relationship("Course", back_populates="items")
    complex = relationship("Complex")
    exercise = relationship("Exercise")
