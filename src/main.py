# src/main.py
import json
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings

from .db import Base, engine, SessionLocal
from .models import Citizen, Application, Status, AppType, Branch
from .schemas import ApplicationCreate, ApplicationOut
from .mailer import send_mail


def parse_origins(raw: Optional[str]) -> List[str]:
    """
    Accept JSON list (preferred) or comma-separated string.
    """
    if not raw:
        return []
    try:
        v = json.loads(raw)
        if isinstance(v, list):
            return v
    except Exception:
        pass
    return [s.strip() for s in raw.split(",") if s.strip()]


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://stratou:secret@db:5432/stratologia"
    ALLOW_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:5174"]
    ALLOW_ORIGINS_RAW: Optional[str] = None


settings = Settings()
origins = parse_origins(settings.ALLOW_ORIGINS_RAW) or settings.ALLOW_ORIGINS

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables on startup (simple for assignment)
Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/_debug/cors")
def debug_cors():
    return {"allow_origins": origins}


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


@app.get("/applications")
def list_applications(status: Status | None = Query(None)):
    db = SessionLocal()
    try:
        q = db.query(Application)
        if status:
            q = q.filter(Application.status == status)
        rows = q.order_by(Application.submitted_at.desc()).limit(100).all()
        return [
            {
                "id": r.id,
                "status": r.status.value,
                "type": r.type.value,
                "desired_branch": r.desired_branch.value,
                "citizen_id": r.citizen_id,
            }
            for r in rows
        ]
    finally:
        db.close()


@app.post("/applications/{app_id}/approve")
def approve_application(app_id: int):
    db = SessionLocal()
    try:
        app_row = db.get(Application, app_id)  # modern SQLAlchemy
        if not app_row:
            raise HTTPException(404, "Not found")
        app_row.status = Status.approved
        db.commit()

        to = f"{app_row.citizen_id}@example.test"
        send_mail(
            to=to,
            subject=f"Application #{app_row.id} approved",
            body=f"Your application {app_row.id} has been approved. Branch: {app_row.desired_branch.value}",
        )
        return {"id": app_row.id, "status": app_row.status.value}
    finally:
        db.close()


@app.post("/applications/{app_id}/reject")
def reject_application(app_id: int):
    db = SessionLocal()
    try:
        app_row = db.get(Application, app_id)  # modern SQLAlchemy
        if not app_row:
            raise HTTPException(404, "Not found")
        app_row.status = Status.rejected
        db.commit()
        return {"id": app_row.id, "status": app_row.status.value}
    finally:
        db.close()
