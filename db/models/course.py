from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from db import Base


class Course(Base):
    __tablename__ = "course"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)

    items = relationship("CourseItem", back_populates="course", order_by="CourseItem.position")
    users = relationship("UserCourse", back_populates="course", cascade="all, delete-orphan")

    @property
    def items_count(self) -> int:
        return len(self.items)


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
    sessions = relationship("DailySession", back_populates="course_item", cascade="all, delete-orphan")

    @property
    def is_exercise(self) -> bool:
        return self.exercise_id is not None

    @property
    def is_complex(self) -> bool:
        return self.complex_id is not None
