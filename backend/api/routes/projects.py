from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from backend.core.database import get_db
from backend.core.auth import get_current_user
from backend.models.project import Project, ProjectCredentials
from backend.models.user import User

router = APIRouter(prefix="/api/projects", tags=["Projects"])


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectCredentialsSchema(BaseModel):
    github_token:          Optional[str] = None
    github_webhook_secret: Optional[str] = None
    slack_bot_token:       Optional[str] = None
    slack_signing_secret:  Optional[str] = None
    slack_channel:         Optional[str] = None
    jira_base_url:         Optional[str] = None
    jira_email:            Optional[str] = None
    jira_api_token:        Optional[str] = None
    jira_project_key:      Optional[str] = None


def _get_user_project(project_id: int, email: str, db: Session) -> Project:
    user = db.query(User).filter(User.email == email).first()
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user.id,
        Project.is_active == True
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("")
def get_projects(current_email: str = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == current_email).first()
    projects = db.query(Project).filter(
        Project.user_id == user.id, Project.is_active == True
    ).order_by(Project.created_at.desc()).all()

    result = []
    for p in projects:
        creds = db.query(ProjectCredentials).filter(ProjectCredentials.project_id == p.id).first()
        result.append({
            "id":              p.id,
            "name":            p.name,
            "description":     p.description or "",
            "has_credentials": bool(creds and creds.github_token),
            "created_at":      p.created_at.strftime("%b %d, %Y") if p.created_at else ""
        })
    return result


@router.post("", status_code=201)
def create_project(data: ProjectCreate, current_email: str = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == current_email).first()

    # Duplicate name check
    existing = db.query(Project).filter(
        Project.user_id == user.id,
        Project.name == data.name,
        Project.is_active == True
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f'A project named "{data.name}" already exists.')

    project = Project(user_id=user.id, name=data.name, description=data.description)
    db.add(project)
    db.commit()
    db.refresh(project)
    return {"id": project.id, "name": project.name}


@router.patch("/{project_id}")
def update_project(
    project_id: int, data: ProjectUpdate,
    current_email: str = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Project name/description update karo."""
    project = _get_user_project(project_id, current_email, db)
    if data.name is not None:
        project.name = data.name
    if data.description is not None:
        project.description = data.description
    db.commit()
    return {"message": "Project updated", "name": project.name}


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    current_email: str = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Project permanently delete karo."""
    project = _get_user_project(project_id, current_email, db)
    # Delete credentials too
    db.query(ProjectCredentials).filter(ProjectCredentials.project_id == project_id).delete()
    project.is_active = False
    db.commit()
    return {"message": "Project deleted"}


@router.post("/{project_id}/credentials")
def save_project_credentials(
    project_id: int, data: ProjectCredentialsSchema,
    current_email: str = Depends(get_current_user), db: Session = Depends(get_db)
):
    _get_user_project(project_id, current_email, db)
    creds = db.query(ProjectCredentials).filter(ProjectCredentials.project_id == project_id).first()

    if creds:
        for field, value in data.dict(exclude_none=True).items():
            if value:
                setattr(creds, field, value)
    else:
        creds = ProjectCredentials(project_id=project_id, **{k: v for k, v in data.dict().items() if v})
        db.add(creds)

    db.commit()
    return {"message": "Credentials saved"}


@router.get("/{project_id}/credentials")
def get_project_credentials(
    project_id: int,
    current_email: str = Depends(get_current_user), db: Session = Depends(get_db)
):
    _get_user_project(project_id, current_email, db)
    creds = db.query(ProjectCredentials).filter(ProjectCredentials.project_id == project_id).first()
    if not creds:
        return {}

    def mask(val):
        if not val: return ""
        return "••••••••" + val[-4:]

    return {
        "github_token":          mask(creds.github_token),
        "github_webhook_secret": mask(creds.github_webhook_secret),
        "slack_bot_token":       mask(creds.slack_bot_token),
        "slack_signing_secret":  mask(creds.slack_signing_secret),
        "slack_channel":         creds.slack_channel or "",
        "jira_base_url":         creds.jira_base_url or "",
        "jira_email":            creds.jira_email or "",
        "jira_api_token":        mask(creds.jira_api_token),
        "jira_project_key":      creds.jira_project_key or "",
    }