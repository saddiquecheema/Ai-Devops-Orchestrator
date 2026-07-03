# from fastapi import APIRouter, Depends, HTTPException
# from fastapi.security import OAuth2PasswordRequestForm
# from sqlalchemy.orm import Session
# from passlib.context import CryptContext
# from pydantic import BaseModel, EmailStr
# from jose import jwt
# from datetime import datetime, timedelta
# from backend.models.user import User
# from backend.core.database import get_db
# from backend.core.auth import get_current_user  # ✅ Uncomment kiya

# router = APIRouter(prefix="/auth", tags=["Authentication"])
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# SECRET_KEY = "your_secret_key_change_this"
# ALGORITHM = "HS256"


# class RegisterSchema(BaseModel):
#     name: str
#     email: EmailStr
#     password: str


# class UserResponse(BaseModel):
#     email: str
#     full_name: str

#     class Config:
#         from_attributes = True


# import re

# def _validate_password(password: str):
#     """Strong password check: 8+ chars, upper, lower, digit, special."""
#     if len(password) < 8:
#         raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
#     if not re.search(r'[A-Z]', password):
#         raise HTTPException(status_code=400, detail="Password must contain an uppercase letter")
#     if not re.search(r'[a-z]', password):
#         raise HTTPException(status_code=400, detail="Password must contain a lowercase letter")
#     if not re.search(r'[0-9]', password):
#         raise HTTPException(status_code=400, detail="Password must contain a number")
#     if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-]', password):
#         raise HTTPException(status_code=400, detail="Password must contain a special character")


# @router.post("/register", status_code=201)
# def register(data: RegisterSchema, db: Session = Depends(get_db)):
#     _validate_password(data.password)
#     if db.query(User).filter(User.email == data.email).first():
#         raise HTTPException(status_code=400, detail="Email already registered")

#     new_user = User(
#         full_name=data.name,
#         email=data.email,
#         password_hash=pwd_context.hash(data.password)
#     )
#     db.add(new_user)
#     db.commit()
#     return {"message": "Account created successfully"}


# @router.post("/login")
# def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.email == form_data.username).first()
#     if not user or not pwd_context.verify(form_data.password, user.password_hash):
#         raise HTTPException(status_code=401, detail="Invalid credentials")

#     expire = datetime.utcnow() + timedelta(hours=24)
#     token = jwt.encode(
#         {"sub": user.email, "exp": expire},
#         SECRET_KEY,
#         algorithm=ALGORITHM
#     )
#     return {"access_token": token, "token_type": "bearer"}


# @router.get("/me", response_model=UserResponse)
# def get_me(
#     current_user_email: str = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     user = db.query(User).filter(User.email == current_user_email).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     return user


# @router.post("/logout")
# def logout(current_user_email: str = Depends(get_current_user)):
#     return {"message": "Logged out successfully"}

import re
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from jose import jwt
from backend.models.user import User
from backend.models.otp import OTPCode
from backend.core.database import get_db
from backend.core.auth import get_current_user
from backend.services.email_service import (
    generate_otp, send_verification_email, send_password_reset_email
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your_secret_key_change_this"
ALGORITHM  = "HS256"


# ── Schemas ───────────────────────────────────────────────────────────────────
class RegisterSchema(BaseModel):
    name: str
    email: EmailStr
    password: str

class VerifySchema(BaseModel):
    email: EmailStr
    code: str

class ForgotSchema(BaseModel):
    email: EmailStr

class ResetSchema(BaseModel):
    email: EmailStr
    code: str
    new_password: str

class UserResponse(BaseModel):
    email: str
    full_name: str
    class Config:
        from_attributes = True


# ── Password validation ───────────────────────────────────────────────────────
def _validate_password(password: str):
    if len(password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")
    if not re.search(r'[A-Z]', password):
        raise HTTPException(400, "Password must contain an uppercase letter")
    if not re.search(r'[a-z]', password):
        raise HTTPException(400, "Password must contain a lowercase letter")
    if not re.search(r'[0-9]', password):
        raise HTTPException(400, "Password must contain a number")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=~`]', password):
        raise HTTPException(400, "Password must contain a special character")


def _create_otp(email: str, purpose: str, db: Session) -> str:
    """Old OTPs expire karo aur naya banao."""
    db.query(OTPCode).filter(
        OTPCode.email == email,
        OTPCode.purpose == purpose,
        OTPCode.is_used == False
    ).delete()

    code = generate_otp()
    otp  = OTPCode(
        email      = email,
        code       = code,
        purpose    = purpose,
        expires_at = datetime.utcnow() + timedelta(minutes=10)
    )
    db.add(otp)
    db.commit()
    return code


# ── Register ──────────────────────────────────────────────────────────────────
@router.post("/register", status_code=201)
def register(data: RegisterSchema, db: Session = Depends(get_db)):
    _validate_password(data.password)

    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, "This email is already registered")

    # Save user as inactive (email not verified yet)
    new_user = User(
        full_name     = data.name,
        email         = data.email,
        password_hash = pwd_context.hash(data.password),
        is_active     = False   # inactive until verified
    )
    db.add(new_user)
    db.commit()

    # Send verification email
    code = _create_otp(data.email, "verify", db)
    sent = send_verification_email(data.email, data.name, code)

    if not sent:
        raise HTTPException(500, "Failed to send verification email. Please try again.")

    return {"message": "Verification code sent to your email"}


# ── Verify Email ──────────────────────────────────────────────────────────────
@router.post("/verify-email")
def verify_email(data: VerifySchema, db: Session = Depends(get_db)):
    otp = db.query(OTPCode).filter(
        OTPCode.email   == data.email,
        OTPCode.code    == data.code,
        OTPCode.purpose == "verify",
        OTPCode.is_used == False
    ).first()

    if not otp:
        raise HTTPException(400, "Invalid verification code")
    if datetime.utcnow() > otp.expires_at.replace(tzinfo=None):
        raise HTTPException(400, "Verification code has expired. Please register again.")

    # Activate user
    user = db.query(User).filter(User.email == data.email).first()
    if user:
        user.is_active = True

    otp.is_used = True
    db.commit()
    return {"message": "Email verified successfully. You can now log in."}


# ── Resend Verification ───────────────────────────────────────────────────────
@router.post("/resend-verification")
def resend_verification(data: ForgotSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(404, "No account found with this email")
    if user.is_active:
        raise HTTPException(400, "This account is already verified")

    code = _create_otp(data.email, "verify", db)
    send_verification_email(data.email, user.full_name, code)
    return {"message": "Verification code resent"}


# ── Login ─────────────────────────────────────────────────────────────────────
@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not pwd_context.verify(form_data.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")

    if not user.is_active:
        raise HTTPException(403, "Please verify your email before logging in")

    expire = datetime.utcnow() + timedelta(hours=24)
    token  = jwt.encode({"sub": user.email, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}


# ── Forgot Password ───────────────────────────────────────────────────────────
@router.post("/forgot-password")
def forgot_password(data: ForgotSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    # Always return success (don't reveal if email exists)
    if not user or not user.is_active:
        return {"message": "If this email is registered, a reset code has been sent"}

    code = _create_otp(data.email, "reset", db)
    send_password_reset_email(data.email, user.full_name, code)
    return {"message": "If this email is registered, a reset code has been sent"}


# ── Reset Password ────────────────────────────────────────────────────────────
@router.post("/reset-password")
def reset_password(data: ResetSchema, db: Session = Depends(get_db)):
    _validate_password(data.new_password)

    otp = db.query(OTPCode).filter(
        OTPCode.email   == data.email,
        OTPCode.code    == data.code,
        OTPCode.purpose == "reset",
        OTPCode.is_used == False
    ).first()

    if not otp:
        raise HTTPException(400, "Invalid or expired reset code")
    if datetime.utcnow() > otp.expires_at.replace(tzinfo=None):
        raise HTTPException(400, "Reset code has expired. Please request a new one.")

    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(404, "User not found")

    user.password_hash = pwd_context.hash(data.new_password)
    otp.is_used = True
    db.commit()
    return {"message": "Password reset successfully. You can now log in."}


# ── Me / Logout ───────────────────────────────────────────────────────────────
@router.get("/me", response_model=UserResponse)
def get_me(current_email: str = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == current_email).first()
    if not user:
        raise HTTPException(404, "User not found")
    return user

@router.post("/logout")
def logout(current_email: str = Depends(get_current_user)):
    return {"message": "Logged out successfully"}