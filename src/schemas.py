from pydantic import BaseModel, Field
from enum import Enum

class AppType(str, Enum):
    deferment = "deferment"
    enlistment = "enlistment"

class Branch(str, Enum):
    army = "army"
    navy = "navy"
    air = "air"

class ApplicationCreate(BaseModel):
    citizen_national_id: str = Field(min_length=3)
    type: AppType
    desired_branch: Branch

class ApplicationOut(BaseModel):
    id: int
    status: str
