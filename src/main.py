# src/main.py
import json, os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Query
from typing import List
from pydantic_settings import BaseSettings

from .db import Base, engine, SessionLocal
from .models import Citizen, Application, Status, AppType, Branch
from .schemas import ApplicationCreate, ApplicationOut


def parse_origins(raw: str) -> List[str]:
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
    # fallback: comma-separated
    return [s.strip() for s in raw.split(",") if s.strip()]


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://stratou:secret@db:5432/stratologia"
    # Read raw string; we’ll parse it ourselves
    ALLOW_ORIGINS_RAW: str = '["http://localhost:5173","http://localhost:5174"]'

    @property
    def ALLOW_ORIGINS(self) -> List[str]:
        return parse_origins(self.ALLOW_ORIGINS_RAW)


settings = Settings()

app = FastAPI()

# CORS
allowlist = settings.ALLOW_ORIGINS
print("CORS allow_origins =", allowlist)  # shows up in `docker compose logs api`

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowlist,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB schema
Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}


# Optional: quick debug endpoint to inspect CORS at runtime
@app.get("/_debug/cors")
def debug_cors():
    return {"allow_origins": allowlist}


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
        app_row = db.query(Application).get(app_id)
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
        app_row = db.query(Application).get(app_id)
        if not app_row:
            raise HTTPException(404, "Not found")
        app_row.status = Status.rejected
        db.commit()
        return {"id": app_row.id, "status": app_row.status.value}
    finally:
        db.close()
