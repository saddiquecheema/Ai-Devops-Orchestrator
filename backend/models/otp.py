"""
backend/models/otp.py — OTP table
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from backend.core.database import Base


class OTPCode(Base):
    __tablename__ = "otp_codes"

    id         = Column(Integer, primary_key=True, index=True)
    email      = Column(String(255), nullable=False, index=True)
    code       = Column(String(10), nullable=False)
    purpose    = Column(String(20), nullable=False)  # "verify" or "reset"
    is_used    = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())