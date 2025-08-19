from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .db import Base

class AppType(PyEnum):
    deferment = "deferment"
    enlistment = "enlistment"

class Branch(PyEnum):
    army = "army"
    navy = "navy"
    air = "air"

class Status(PyEnum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class Citizen(Base):
    __tablename__ = "citizens"
    id = Column(Integer, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name  = Column(String(100), nullable=False)
    national_id = Column(String(50), unique=True, nullable=False)

class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True)
    citizen_id = Column(Integer, ForeignKey("citizens.id"), nullable=False)
    type = Column(Enum(AppType), nullable=False)
    desired_branch = Column(Enum(Branch), nullable=False)
    status = Column(Enum(Status), nullable=False, default=Status.pending)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
