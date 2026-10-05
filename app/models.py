from sqlalchemy import Column, Integer, String, Text

from app.database import Base


class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(255), nullable=False)

    description = Column(Text)

    format = Column(String(20), nullable=False)

    file_path = Column(String(500), nullable=True)