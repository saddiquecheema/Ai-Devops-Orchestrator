from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from backend.core.database import Base


class Stats(Base):
    __tablename__ = "stats"

    id         = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    key        = Column(String(50), nullable=False)   # git_events, jira_tickets, slack_alerts
    count      = Column(Integer, default=0, nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class ActivityLog(Base):
    __tablename__ = "activity_log"

    id         = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    event_type = Column(String(20), nullable=False)
    message    = Column(String(500), nullable=False)
    priority   = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())