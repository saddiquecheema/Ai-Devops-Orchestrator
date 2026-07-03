from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.sql import func
from backend.core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    name        = Column(String(100), nullable=False)
    description = Column(String(300), nullable=True)
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())


class ProjectCredentials(Base):
    __tablename__ = "project_credentials"

    id                    = Column(Integer, primary_key=True, index=True)
    project_id            = Column(Integer, ForeignKey("projects.id"), unique=True, nullable=False)

    # GitHub
    github_token          = Column(String(500), nullable=True)
    github_webhook_secret = Column(String(200), nullable=True)

    # Slack
    slack_bot_token       = Column(String(500), nullable=True)
    slack_signing_secret  = Column(String(200), nullable=True)
    slack_channel         = Column(String(100), nullable=True)

    # Jira
    jira_base_url         = Column(String(200), nullable=True)
    jira_email            = Column(String(200), nullable=True)
    jira_api_token        = Column(String(500), nullable=True)
    jira_project_key      = Column(String(50),  nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())