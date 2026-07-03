from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.auth import get_current_user
from backend.models.stats import Stats, ActivityLog
from backend.models.project import Project
from backend.models.user import User

router = APIRouter(prefix="/api", tags=["Stats"])


def _verify_project(project_id: int, current_email: str, db: Session) -> Project:
    """Project exist karta hai aur user ka hai — verify karo."""
    user = db.query(User).filter(User.email == current_email).first()
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user.id,
        Project.is_active == True
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def get_or_create_stat(db: Session, project_id: int, key: str) -> Stats:
    stat = db.query(Stats).filter(
        Stats.project_id == project_id,
        Stats.key == key
    ).first()
    if not stat:
        stat = Stats(project_id=project_id, key=key, count=0)
        db.add(stat)
        db.commit()
        db.refresh(stat)
    return stat


@router.get("/stats")
def get_stats(
    project_id: int = None,
    current_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Project ke stats return karo."""
    if not project_id:
        return {"git_events": 0, "jira_tickets": 0, "slack_alerts": 0, "activities": []}

    _verify_project(project_id, current_email, db)

    git   = get_or_create_stat(db, project_id, "git_events")
    jira  = get_or_create_stat(db, project_id, "jira_tickets")
    slack = get_or_create_stat(db, project_id, "slack_alerts")

    activities = (
        db.query(ActivityLog)
        .filter(ActivityLog.project_id == project_id)
        .order_by(ActivityLog.created_at.desc())
        .limit(20)
        .all()
    )

    return {
        "git_events":   git.count,
        "jira_tickets": jira.count,
        "slack_alerts": slack.count,
        "activities": [
            {
                "type":     a.event_type,
                "message":  a.message,
                "priority": a.priority,
                "time":     a.created_at.strftime("%H:%M:%S") if a.created_at else ""
            }
            for a in reversed(activities)
        ]
    }


@router.post("/stats/reset")
def reset_stats(
    project_id: int,
    current_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _verify_project(project_id, current_email, db)
    db.query(Stats).filter(Stats.project_id == project_id).delete()
    db.query(ActivityLog).filter(ActivityLog.project_id == project_id).delete()
    db.commit()
    return {"message": "Stats reset"}