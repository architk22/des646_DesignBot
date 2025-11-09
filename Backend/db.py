# Backend/db.py
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "ddi.sqlite")
engine = create_engine(f"sqlite:///{DB_PATH}", future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

class Visit(Base):
    __tablename__ = "visits"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    patient_name = Column(String(128), nullable=True)
    age = Column(Integer, nullable=True)
    doctor_name = Column(String(128), nullable=True)

    new_drug = Column(String(256), nullable=False)
    current_csv = Column(Text, nullable=False)

    # useful summaries for quick reporting
    max_severity = Column(String(32), nullable=True)
    max_score = Column(Float, nullable=True)

    # full payloads
    alerts_json = Column(Text, nullable=False)
    not_found_json = Column(Text, nullable=False)

def init_db():
    Base.metadata.create_all(bind=engine)

def save_visit(req, result) -> int:
    """Persist one request + result, return visit_id."""
    from sqlalchemy import select
    with SessionLocal() as s:
        # compute max severity/score for quick overview
        sev_order = {"Contraindicated": 3, "Major": 2, "Moderate": 1, "Minor": 0}
        _max = None
        for a in result.get("alerts", []):
            key = (sev_order.get(a.get("severity",""), -1), float(a.get("severity_score", 0.0)))
            _max = key if _max is None or key > _max else _max
        max_sev = None if _max is None else ["Minor","Moderate","Major","Contraindicated"][_max[0]]
        max_score = None if _max is None else _max[1]

        v = Visit(
            patient_name=req.patient_name,
            age=req.age,
            doctor_name=req.doctor_name,
            new_drug=req.new_drug,
            current_csv=",".join(req.current),
            max_severity=max_sev,
            max_score=max_score,
            alerts_json=json.dumps(result.get("alerts", [])),
            not_found_json=json.dumps(result.get("not_found", [])),
        )
        s.add(v)
        s.commit()
        s.refresh(v)
        return v.id
