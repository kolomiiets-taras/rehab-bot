from sqlalchemy import Column, Integer, String

from db import Base


class MotivationMessage(Base):
    __tablename__ = "motivation_message"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(String(500), nullable=False, index=True)
