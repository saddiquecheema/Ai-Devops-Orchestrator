# """
# =============================================================================
# backend/core/application.py — FASTAPI APPLICATION FACTORY
# =============================================================================
# FastAPI app banata hai — routes register karta hai.
# main.py is function ko call karta hai.
# =============================================================================
# """

# import os
# from contextlib import asynccontextmanager

# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware

# from backend.api.routes import github, jira, report, slack, system
# from backend.core.config import settings
# from backend.core.logger import get_logger, setup_logging

# logger = get_logger(__name__)


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """Startup aur shutdown logic."""
#     setup_logging()
#     os.makedirs("logs", exist_ok=True)

#     logger.info("=" * 50)
#     logger.info("  AI DevOps Orchestrator — STARTED")
#     logger.info(f"  Port    : {settings.app_port}")
#     logger.info(f"  Model   : {settings.groq_model}")
#     logger.info(f"  Jira    : {settings.jira_project_key}")
#     logger.info(f"  Slack   : {settings.default_slack_channel}")
#     logger.info("=" * 50)

#     yield

#     logger.info("AI DevOps Orchestrator — Shutting down")


# def create_app() -> FastAPI:
#     """FastAPI app banao aur return karo."""
#     app = FastAPI(
#         title    = "AI-Driven DevOps Orchestrator",
#         version  = "1.0.0",
#         docs_url = "/docs",
#         lifespan = lifespan,
#     )

#     app.add_middleware(
#         CORSMiddleware,
#         allow_origins     = ["*"],
#         allow_credentials = True,
#         allow_methods     = ["*"],
#         allow_headers     = ["*"],
#     )

#     # Routes register karo
#     app.include_router(system.router)
#     app.include_router(report.router)
#     app.include_router(github.router)
#     app.include_router(slack.router,  prefix="/webhooks")
#     app.include_router(jira.router,   prefix="/webhooks")

#     return app


"""
=============================================================================
app/core/application.py — FASTAPI APPLICATION FACTORY
=============================================================================
PURPOSE:
  FastAPI app banata hai — middleware attach karta hai, routes register
  karta hai, aur startup/shutdown logic handle karta hai.

  Factory pattern use kiya hai (create_app function) taake testing mein
  alag app instance banana aasaan ho.

STARTUP FLOW:
  main.py → create_app() → lifespan() → routes registered → server ready
=============================================================================
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import github, jira, report, slack, system
from backend.core.config import settings
from backend.core.logger import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application ke shuru aur band hone par kya karna hai.
    'yield' se pehle = startup code
    'yield' ke baad = shutdown code

    Yahan: logging setup karo aur startup message print karo.
    Production mein: DB connection pool bhi yahan kholte hain.
    """
    # ----- STARTUP -----
    setup_logging()

    # Logs folder banao agar exist nahi karta
    os.makedirs("logs", exist_ok=True)

    logger.info("=" * 60)
    logger.info("  AI-Driven DevOps Orchestrator — STARTING")
    logger.info("=" * 60)
    logger.info(f"  Environment : {settings.app_env}")
    logger.info(f"  LLM Model   : {settings.groq_model}")
    logger.info(f"  Jira Project: {settings.jira_project_key}")
    logger.info(f"  Slack Chan  : {settings.default_slack_channel}")
    logger.info(f"  Port        : {settings.app_port}")
    logger.info("=" * 60)

    yield  # <-- Application yahan run hoti hai

    # ----- SHUTDOWN -----
    logger.info("AI-Driven DevOps Orchestrator — SHUTTING DOWN")


def create_app() -> FastAPI:
    """
    FastAPI application banao aur return karo.
    main.py is function ko call karta hai.
    Tests bhi is function ko call kar ke fresh app lete hain.
    """
    app = FastAPI(
        title       = "AI-Driven DevOps Orchestrator",
        description = "GitHub + Slack + Jira ko AI agent se automate karta hai",
        version     = "1.0.0",
        docs_url    = "/docs",    # Swagger UI — browser mein kholne ke liye
        redoc_url   = "/redoc",   # ReDoc — alternate API docs
        lifespan    = lifespan,
    )

    # -------------------------------------------------------------------------
    # CORS Middleware
    # Development mein sab allow, production mein restrict karo
    # -------------------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins     = ["*"] if settings.app_env == "development" else [],
        allow_credentials = True,
        allow_methods     = ["*"],
        allow_headers     = ["*"],
    )

    # -------------------------------------------------------------------------
    # ROUTES — Har platform ka alag router file
    # -------------------------------------------------------------------------
    app.include_router(system.router)
    app.include_router(report.router)                       # /report/daily
    app.include_router(github.router,)
    app.include_router(slack.router,  prefix="/webhooks")
    app.include_router(jira.router,   prefix="/webhooks")

    return app