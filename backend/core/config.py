# """
# =============================================================================
# backend/core/config.py — CENTRAL CONFIGURATION
# =============================================================================
# Tamam settings ek jagah.
# .env file se automatically load hoti hain.
# =============================================================================
# """

# import os
# from pydantic import Field
# from pydantic_settings import BaseSettings, SettingsConfigDict

# # Current directory se .env file ka absolute path
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# ENV_FILE = os.path.join(BASE_DIR, ".env")

# class Settings(BaseSettings):
#     model_config = SettingsConfigDict(
#         env_file          = ENV_FILE,           # ← Absolute path
#         env_file_encoding = "utf-8",
#         case_sensitive    = False,
#         extra             = 'ignore',
#     )

#     # App
#     app_env:   str = Field(default="development")
#     app_port:  int = Field(default=8000)
#     log_level: str = Field(default="INFO")

#     # Groq LLM
#     groq_api_key:    str   = Field(default="placeholder")
#     groq_model:      str   = Field(default="llama3-groq-70b-8192-tool-use-preview")
#     llm_temperature: float = Field(default=0.1)
#     llm_max_tokens:  int   = Field(default=2048)

#     # GitHub
#     github_token:          str = Field(default="placeholder")
#     github_webhook_secret: str = Field(default="placeholder")
#     github_api_url:        str = Field(default="https://api.github.com")

#     # Slack
#     slack_bot_token:       str = Field(default="placeholder")
#     slack_signing_secret:  str = Field(default="placeholder")
#     slack_api_url:         str = Field(default="https://slack.com/api")
#     default_slack_channel: str = Field(default="#devops-alerts")

#     # Jira
#     jira_base_url:    str = Field(default="https://placeholder.atlassian.net")
#     jira_email:       str = Field(default="placeholder@email.com")
#     jira_api_token:   str = Field(default="placeholder")
#     jira_project_key: str = Field(default="SCRUM")


# # Singleton
# settings = Settings()

# # Debug print (startup pe dikhega)
# print(f"✅ Config Loaded from: {ENV_FILE}")
# print(f"🔑 GitHub Webhook Secret Length: {len(settings.github_webhook_secret)}")


"""
=============================================================================
backend/core/config.py — CENTRAL CONFIGURATION
=============================================================================
"""

import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(BASE_DIR, ".env")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file          = ENV_FILE,
        env_file_encoding = "utf-8",
        case_sensitive    = False,
        extra             = 'ignore',
    )

    # App
    app_env:   str = Field(default="development")
    app_port:  int = Field(default=8000)
    log_level: str = Field(default="INFO")

    # Groq LLM
    groq_api_key:    str   = Field(default="placeholder")
    groq_model:      str   = Field(default="llama3-groq-70b-8192-tool-use-preview")
    llm_temperature: float = Field(default=0.1)
    llm_max_tokens:  int   = Field(default=2048)

    # GitHub
    github_token:          str = Field(default="placeholder")
    github_webhook_secret: str = Field(default="placeholder")
    github_api_url:        str = Field(default="https://api.github.com")

    # Slack
    slack_bot_token:       str = Field(default="placeholder")
    slack_signing_secret:  str = Field(default="placeholder")
    slack_api_url:         str = Field(default="https://slack.com/api")
    default_slack_channel: str = Field(default="#devops-alerts")

    # Jira
    jira_base_url:    str = Field(default="https://placeholder.atlassian.net")
    jira_email:       str = Field(default="placeholder@email.com")
    jira_api_token:   str = Field(default="placeholder")
    jira_project_key: str = Field(default="SCRUM")

    # ✅ Gmail (OTP emails ke liye)
    gmail_user:         str = Field(default="")
    gmail_app_password: str = Field(default="")


# Singleton
settings = Settings()

print(f"✅ Config Loaded from: {ENV_FILE}")
print(f"🔑 GitHub Webhook Secret Length: {len(settings.github_webhook_secret)}")