"""
backend/services/email_service.py
Gmail SMTP se verification/reset emails bhejo
"""
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.core.config import settings
from backend.core.logger import get_logger

logger = get_logger(__name__)


def generate_otp(length: int = 6) -> str:
    """6-digit numeric OTP generate karo."""
    return ''.join(random.choices(string.digits, k=length))


def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Gmail SMTP se email bhejo."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"DevOps Orchestrator <{settings.gmail_user}>"
        msg["To"]      = to_email

        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(settings.gmail_user, settings.gmail_app_password)
            server.sendmail(settings.gmail_user, to_email, msg.as_string())

        logger.info(f"[Email] Sent to {to_email}: {subject}")
        return True

    except Exception as e:
        logger.error(f"[Email] Failed to send to {to_email}: {e}")
        return False


def send_verification_email(to_email: str, name: str, otp: str) -> bool:
    """Account verification email bhejo."""
    subject = "Verify your DevOps Orchestrator account"
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0;padding:0;background:#080c14;font-family:'Segoe UI',sans-serif;">
        <div style="max-width:480px;margin:40px auto;background:#0d1320;border:1px solid #1c2a3a;border-radius:16px;overflow:hidden;">

            <!-- Header -->
            <div style="background:linear-gradient(135deg,#3b82f6,#6366f1);padding:28px 32px;text-align:center;">
                <div style="font-size:28px;margin-bottom:8px;">⚡</div>
                <div style="color:white;font-size:18px;font-weight:700;">DevOps Orchestrator</div>
            </div>

            <!-- Body -->
            <div style="padding:32px;">
                <h2 style="color:#e2eaf4;font-size:20px;margin:0 0 8px;">Hi {name},</h2>
                <p style="color:#5a7090;font-size:14px;margin:0 0 24px;line-height:1.6;">
                    Thanks for registering. Use the verification code below to activate your account.
                    This code expires in <b style="color:#e2eaf4;">10 minutes</b>.
                </p>

                <!-- OTP Box -->
                <div style="background:#111927;border:1px solid #1c2a3a;border-radius:12px;padding:24px;text-align:center;margin-bottom:24px;">
                    <div style="color:#5a7090;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:2px;margin-bottom:12px;">Verification Code</div>
                    <div style="font-size:38px;font-weight:700;letter-spacing:12px;color:#3b82f6;font-family:'Courier New',monospace;">{otp}</div>
                </div>

                <p style="color:#3a5070;font-size:12px;margin:0;line-height:1.6;">
                    If you did not create an account, you can safely ignore this email.
                </p>
            </div>

            <!-- Footer -->
            <div style="padding:16px 32px;border-top:1px solid #1c2a3a;text-align:center;">
                <p style="color:#3a5070;font-size:11px;margin:0;">© 2026 DevOps Orchestrator · Automated with AI</p>
            </div>
        </div>
    </body>
    </html>
    """
    return send_email(to_email, subject, html)


def send_password_reset_email(to_email: str, name: str, otp: str) -> bool:
    """Password reset email bhejo."""
    subject = "Reset your DevOps Orchestrator password"
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0;padding:0;background:#080c14;font-family:'Segoe UI',sans-serif;">
        <div style="max-width:480px;margin:40px auto;background:#0d1320;border:1px solid #1c2a3a;border-radius:16px;overflow:hidden;">

            <!-- Header -->
            <div style="background:linear-gradient(135deg,#ef4444,#f97316);padding:28px 32px;text-align:center;">
                <div style="font-size:28px;margin-bottom:8px;">🔐</div>
                <div style="color:white;font-size:18px;font-weight:700;">Password Reset</div>
            </div>

            <!-- Body -->
            <div style="padding:32px;">
                <h2 style="color:#e2eaf4;font-size:20px;margin:0 0 8px;">Hi {name},</h2>
                <p style="color:#5a7090;font-size:14px;margin:0 0 24px;line-height:1.6;">
                    We received a request to reset your password. Use the code below.
                    This code expires in <b style="color:#e2eaf4;">10 minutes</b>.
                </p>

                <!-- OTP Box -->
                <div style="background:#111927;border:1px solid #2a1a1a;border-radius:12px;padding:24px;text-align:center;margin-bottom:24px;">
                    <div style="color:#5a7090;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:2px;margin-bottom:12px;">Reset Code</div>
                    <div style="font-size:38px;font-weight:700;letter-spacing:12px;color:#f97316;font-family:'Courier New',monospace;">{otp}</div>
                </div>

                <p style="color:#3a5070;font-size:12px;margin:0;line-height:1.6;">
                    If you did not request a password reset, please ignore this email. Your password will remain unchanged.
                </p>
            </div>

            <!-- Footer -->
            <div style="padding:16px 32px;border-top:1px solid #1c2a3a;text-align:center;">
                <p style="color:#3a5070;font-size:11px;margin:0;">© 2026 DevOps Orchestrator · Automated with AI</p>
            </div>
        </div>
    </body>
    </html>
    """
    return send_email(to_email, subject, html)