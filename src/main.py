from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings
from typing import List
from .db import Base, engine, SessionLocal
from .models import Citizen, Application, Status, AppType, Branch
from .schemas import ApplicationCreate, ApplicationOut

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://stratou:secret@db:5432/stratologia"
    ALLOW_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:5174"]

settings = Settings()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables on startup (simple for assignment)
Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/applications", response_model=ApplicationOut)
def create_application(payload: ApplicationCreate):
    db = SessionLocal()
    try:
        citizen = db.query(Citizen).filter_by(national_id=payload.citizen_national_id).first()
        if not citizen:
            citizen = Citizen(first_name="Unknown", last_name="Citizen", national_id=payload.citizen_national_id)
            db.add(citizen)
            db.flush()
        app_row = Application(
            citizen_id=citizen.id,
            type=AppType(payload.type),
            desired_branch=Branch(payload.desired_branch),
            status=Status.pending,
        )
        db.add(app_row)
        db.commit()
        db.refresh(app_row)
        return {"id": app_row.id, "status": app_row.status.value}
    finally:
        db.close()
