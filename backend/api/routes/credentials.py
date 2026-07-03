# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from pydantic import BaseModel
# from typing import Optional
# from backend.core.database import get_db
# from backend.core.auth import get_current_user
# from backend.models.user_credentials import UserCredentials
# from backend.models.user import User

# router = APIRouter(prefix="/api/credentials", tags=["Credentials"])


# class CredentialsSchema(BaseModel):
#     github_token:          Optional[str] = None
#     github_webhook_secret: Optional[str] = None
#     slack_bot_token:       Optional[str] = None
#     slack_signing_secret:  Optional[str] = None
#     slack_channel:         Optional[str] = None
#     jira_base_url:         Optional[str] = None
#     jira_email:            Optional[str] = None
#     jira_api_token:        Optional[str] = None
#     jira_project_key:      Optional[str] = None
#     groq_api_key:          Optional[str] = None


# @router.get("/check")
# def check_credentials(
#     current_email: str = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Check karo ke user ki credentials saved hain ya nahi."""
#     user = db.query(User).filter(User.email == current_email).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     creds = db.query(UserCredentials).filter(
#         UserCredentials.user_id == user.id
#     ).first()

#     # Credentials hain aur GitHub token filled hai?
#     has_credentials = bool(creds and creds.github_token)
#     return {"has_credentials": has_credentials}


# @router.post("/save")
# def save_credentials(
#     data: CredentialsSchema,
#     current_email: str = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """User ki API credentials save ya update karo."""
#     user = db.query(User).filter(User.email == current_email).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     creds = db.query(UserCredentials).filter(
#         UserCredentials.user_id == user.id
#     ).first()

#     if creds:
#         # Update karo
#         for field, value in data.dict(exclude_none=True).items():
#             setattr(creds, field, value)
#     else:
#         # Naya record banao
#         creds = UserCredentials(user_id=user.id, **data.dict())
#         db.add(creds)

#     db.commit()
#     return {"message": "Credentials saved successfully"}


# @router.get("/get")
# def get_credentials(
#     current_email: str = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """User ki saved credentials return karo (masked)."""
#     user = db.query(User).filter(User.email == current_email).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     creds = db.query(UserCredentials).filter(
#         UserCredentials.user_id == user.id
#     ).first()

#     if not creds:
#         return {}

#     def mask(val):
#         """Token ka sirf aakhri 4 characters dikha."""
#         if not val:
#             return ""
#         return "••••••••" + val[-4:]

#     return {
#         "github_token":          mask(creds.github_token),
#         "github_webhook_secret": mask(creds.github_webhook_secret),
#         "slack_bot_token":       mask(creds.slack_bot_token),
#         "slack_signing_secret":  mask(creds.slack_signing_secret),
#         "slack_channel":         creds.slack_channel or "",
#         "jira_base_url":         creds.jira_base_url or "",
#         "jira_email":            creds.jira_email or "",
#         "jira_api_token":        mask(creds.jira_api_token),
#         "jira_project_key":      creds.jira_project_key or "",
#         "groq_api_key":          mask(creds.groq_api_key),
#     }


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from backend.core.database import get_db
from backend.core.auth import get_current_user
from backend.models.user_credentials import UserCredentials
from backend.models.user import User

router = APIRouter(prefix="/api/credentials", tags=["Credentials"])


class CredentialsSchema(BaseModel):
    github_token:          Optional[str] = None
    github_webhook_secret: Optional[str] = None
    slack_bot_token:       Optional[str] = None
    slack_signing_secret:  Optional[str] = None
    slack_channel:         Optional[str] = None
    jira_base_url:         Optional[str] = None
    jira_email:            Optional[str] = None
    jira_api_token:        Optional[str] = None
    jira_project_key:      Optional[str] = None


@router.get("/check")
def check_credentials(
    current_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check karo ke user ki credentials saved hain ya nahi."""
    user = db.query(User).filter(User.email == current_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    creds = db.query(UserCredentials).filter(
        UserCredentials.user_id == user.id
    ).first()

    # Credentials hain aur GitHub token filled hai?
    has_credentials = bool(creds and creds.github_token)
    return {"has_credentials": has_credentials}


@router.post("/save")
def save_credentials(
    data: CredentialsSchema,
    current_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """User ki API credentials save ya update karo."""
    user = db.query(User).filter(User.email == current_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    creds = db.query(UserCredentials).filter(
        UserCredentials.user_id == user.id
    ).first()

    if creds:
        # Update karo
        for field, value in data.dict(exclude_none=True).items():
            setattr(creds, field, value)
    else:
        # Naya record banao
        creds = UserCredentials(user_id=user.id, **data.dict())
        db.add(creds)

    db.commit()
    return {"message": "Credentials saved successfully"}


@router.get("/get")
def get_credentials(
    current_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """User ki saved credentials return karo (masked)."""
    user = db.query(User).filter(User.email == current_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    creds = db.query(UserCredentials).filter(
        UserCredentials.user_id == user.id
    ).first()

    if not creds:
        return {}

    def mask(val):
        """Token ka sirf aakhri 4 characters dikha."""
        if not val:
            return ""
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