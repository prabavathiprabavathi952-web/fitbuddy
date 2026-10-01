"""SQLite + SQLAlchemy persistence layer."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Column, DateTime, Float, ForeignKey, Integer, String, Text, create_engine, func,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from app import config

_connect_args = {"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(config.DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
Base = declarative_base()


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String(80), nullable=False)
    age = Column(Integer, nullable=False)
    weight = Column(Float, nullable=False)
    height = Column(Float, nullable=True)
    goal = Column(String(200), nullable=False)
    intensity = Column(String(10), nullable=False)
    experience = Column(String(20), default="beginner")
    equipment = Column(String(10), default="gym")
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=_now)

    plan = relationship("WorkoutPlan", back_populates="user", uselist=False,
                        cascade="all, delete-orphan")
    feedback = relationship("PlanFeedback", back_populates="user",
                            cascade="all, delete-orphan", order_by="PlanFeedback.id")


class WorkoutPlan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    original_plan = Column(Text, nullable=False)
    updated_plan = Column(Text, nullable=True)
    nutrition_tip = Column(Text, nullable=True)
    plan_source = Column(String(60), default="offline")
    updated_source = Column(String(60), nullable=True)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="plan")


class PlanFeedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=_now)

    user = relationship("User", back_populates="feedback")


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


# --------------------------------------------------------------------------- users
def next_user_id() -> int:
    with SessionLocal() as db:
        return (db.query(func.max(User.id)).scalar() or 0) + 1


def save_user(user_id: int, name: str, age: int, weight: float, goal: str, intensity: str,
              height: Optional[float] = None, experience: str = "beginner",
              equipment: str = "gym", notes: Optional[str] = None) -> int:
    """Create the user, or update them if this ID already exists."""
    with SessionLocal() as db:
        user = db.get(User, user_id)
        if user is None:
            user = User(id=user_id)
            db.add(user)
        user.name, user.age, user.weight, user.goal = name, age, weight, goal
        user.intensity, user.height, user.experience = intensity, height, experience
        user.equipment, user.notes = equipment, notes
        db.commit()
    return user_id


def get_user(user_id: int) -> Optional[User]:
    with SessionLocal() as db:
        return db.get(User, user_id)


def get_all_users() -> list[User]:
    with SessionLocal() as db:
        return db.query(User).order_by(User.id).all()


def delete_user(user_id: int) -> bool:
    with SessionLocal() as db:
        user = db.get(User, user_id)
        if not user:
            return False
        db.delete(user)
        db.commit()
        return True


# --------------------------------------------------------------------------- plans
def save_plan(user_id: int, plan: str, nutrition_tip: Optional[str] = None,
              source: str = "offline") -> None:
    """Store a freshly generated plan. Replaces any previous plan and feedback."""
    with SessionLocal() as db:
        row = db.query(WorkoutPlan).filter(WorkoutPlan.user_id == user_id).first()
        if row is None:
            row = WorkoutPlan(user_id=user_id, original_plan=plan)
            db.add(row)
        row.original_plan = plan
        row.updated_plan = None
        row.updated_source = None
        row.updated_at = None
        row.nutrition_tip = nutrition_tip
        row.plan_source = source
        row.created_at = _now()
        db.query(PlanFeedback).filter(PlanFeedback.user_id == user_id).delete()
        db.commit()


def update_plan(user_id: int, updated_text: str, feedback: Optional[str] = None,
                source: Optional[str] = None) -> bool:
    """Save the revised plan in its own column so the original is preserved."""
    with SessionLocal() as db:
        row = db.query(WorkoutPlan).filter(WorkoutPlan.user_id == user_id).first()
        if row is None:
            return False
        row.updated_plan = updated_text
        row.updated_source = source
        row.updated_at = _now()
        if feedback:
            db.add(PlanFeedback(user_id=user_id, text=feedback))
        db.commit()
        return True


def get_plan(user_id: int) -> Optional[WorkoutPlan]:
    with SessionLocal() as db:
        return db.query(WorkoutPlan).filter(WorkoutPlan.user_id == user_id).first()


def get_all_plans() -> list[WorkoutPlan]:
    with SessionLocal() as db:
        return db.query(WorkoutPlan).order_by(WorkoutPlan.user_id).all()


def get_original_plan(user_id: int) -> Optional[str]:
    plan = get_plan(user_id)
    return plan.original_plan if plan else None


def get_current_plan(user_id: int) -> Optional[str]:
    """Latest version of the plan: the updated one if it exists, else the original."""
    plan = get_plan(user_id)
    if not plan:
        return None
    return plan.updated_plan or plan.original_plan


def get_feedback_history(user_id: int) -> list[dict]:
    with SessionLocal() as db:
        rows = db.query(PlanFeedback).filter(PlanFeedback.user_id == user_id) \
                 .order_by(PlanFeedback.id).all()
        return [{"text": r.text, "created_at": r.created_at} for r in rows]


# --------------------------------------------------------------------------- admin
def get_admin_rows() -> list[dict]:
    """One dict per user, joined with plan and feedback count, for the dashboard."""
    with SessionLocal() as db:
        rows = []
        for u in db.query(User).order_by(User.id).all():
            p = u.plan
            rows.append({
                "id": u.id, "name": u.name, "age": u.age, "weight": u.weight,
                "height": u.height, "goal": u.goal, "intensity": u.intensity,
                "experience": u.experience, "equipment": u.equipment,
                "created_at": u.created_at,
                "original_plan": p.original_plan if p else None,
                "updated_plan": p.updated_plan if p else None,
                "plan_source": p.plan_source if p else None,
                "updated_at": p.updated_at if p else None,
                "feedback": [f.text for f in u.feedback],
            })
        return rows


def get_admin_stats(rows: list[dict]) -> dict:
    total = len(rows)
    updated = sum(1 for r in rows if r["updated_plan"])
    by_intensity = {"low": 0, "medium": 0, "high": 0}
    for r in rows:
        by_intensity[r["intensity"]] = by_intensity.get(r["intensity"], 0) + 1
    return {
        "total": total,
        "updated": updated,
        "feedback_total": sum(len(r["feedback"]) for r in rows),
        "avg_age": round(sum(r["age"] for r in rows) / total, 1) if total else 0,
        "by_intensity": by_intensity,
    }
