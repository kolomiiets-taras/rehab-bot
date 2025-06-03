from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from db import Base


class Complex(Base):
    __tablename__ = "complex"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)

    exercises = relationship("ComplexExercise", back_populates="complex", order_by="ComplexExercise.position")


class ComplexExercise(Base):
    __tablename__ = "complex_exercise"

    id = Column(Integer, primary_key=True)
    complex_id = Column(Integer, ForeignKey("complex.id", ondelete="CASCADE"))
    exercise_id = Column(Integer, ForeignKey("exercise.id", ondelete="CASCADE"))
    position = Column(Integer, nullable=False)

    complex = relationship("Complex", back_populates="exercises")
    exercise = relationship("Exercise")
