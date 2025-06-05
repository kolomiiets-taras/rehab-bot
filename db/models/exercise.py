from sqlalchemy import Column, Integer, String
from db import Base


class Exercise(Base):
    __tablename__ = "exercise"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    text = Column(String(2000), nullable=True)
    media = Column(String(255), nullable=False, default='processing')
