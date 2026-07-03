# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker

# SQLALCHEMY_DATABASE_URL = "sqlite:///./devops.db"
# engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
# SessionLocal = sessionmaker(bind=engine)
# Base = declarative_base()


# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


# def init_db():
#     """Saare tables create karo agar exist nahi karte"""
#     from backend.models.user import User                          # noqa: F401
#     from backend.models.stats import Stats, ActivityLog          # noqa: F401
#     from backend.models.user_credentials import UserCredentials  # noqa: F401
#     from backend.models.project import Project, ProjectCredentials  # noqa: F401
#     Base.metadata.create_all(bind=engine)
#     print("✅ Database tables created!")

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./devops.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Saare tables create karo agar exist nahi karte"""
    from backend.models.user import User                          # noqa: F401
    from backend.models.stats import Stats, ActivityLog          # noqa: F401
    from backend.models.user_credentials import UserCredentials  # noqa: F401
    from backend.models.project import Project, ProjectCredentials  # noqa: F401
    from backend.models.otp import OTPCode                            # noqa: F401
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created!")