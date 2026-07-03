# """
# =============================================================================
# backend/agent/tools/github_tool.py — GITHUB MCP TOOL
# =============================================================================
# GitHub REST API v3 wrapper.
# AI Agent in methods ko call karta hai — direct HTTP nahi karta.

# METHODS:
#   get_pr_diff()           — PR diff + metadata + file stats
#   get_pr_commit_history() — PR commits history
#   add_pr_comment()        — AI review comment post karo
#   add_pr_review()         — Formal GitHub Review (APPROVE/REQUEST_CHANGES)
#   set_pr_label()          — Risk label lagao
#   merge_pr()              — Auto-merge (sirf low risk)
#   close_pr()              — Critical PR close karo
#   list_pr_files()         — Changed files list
#   assign_pr_reviewer()    — Reviewers assign karo
#   get_repo_contributors() — Contributors fetch karo
# =============================================================================
# """

# import httpx
# from backend.core.config import settings
# from backend.core.logger import get_logger

# logger = get_logger(__name__)

# SENSITIVE_FILE_PATTERNS = (
#     ".env", "secret", "password", "credential", "token",
#     "settings.py", "config.py", "config.yml", "config.json",
#     "migration", "schema.sql", "models.py",
#     "requirements.txt", "package.json", "Pipfile",
#     "dockerfile", "docker-compose", ".github/workflows",
#     "nginx.conf", "apache", ".htaccess",
#     "id_rsa", "id_ed25519", ".pem", ".key", ".cert",
# )


# def _detect_sensitive_files(files: list[dict]) -> list[str]:
#     """Changed files mein sensitive patterns dhoondhao."""
#     found = []
#     for f in files:
#         filename = f.get("filename", "").lower()
#         for pattern in SENSITIVE_FILE_PATTERNS:
#             if pattern in filename:
#                 found.append(f["filename"])
#                 break
#     return found


# class GitHubTool:
#     """GitHub REST API v3 wrapper."""

#     def __init__(self):
#         self.base_url = settings.github_api_url
#         self.headers  = {
#             "Authorization":        f"token {settings.github_token}",
#             "Accept":               "application/vnd.github.v3+json",
#             "X-GitHub-Api-Version": "2022-11-28",
#         }

#     async def get_pr_diff(self, repo: str, pr_number: int) -> dict:
#         """
#         PR ka complete data fetch karo — metadata, diff, file stats.
#         3 API calls karta hai internally.
#         Diff 8000 chars pe truncate — LLM context window ke liye.
#         """
#         pr_url       = f"{self.base_url}/repos/{repo}/pulls/{pr_number}"
#         diff_headers = {**self.headers, "Accept": "application/vnd.github.v3.diff"}
#         files_url    = f"{pr_url}/files"

#         async with httpx.AsyncClient(timeout=30.0) as client:
#             meta_resp  = await client.get(pr_url, headers=self.headers)
#             meta_resp.raise_for_status()
#             meta = meta_resp.json()

#             diff_resp  = await client.get(pr_url, headers=diff_headers)
#             diff_resp.raise_for_status()

#             files_resp = await client.get(files_url, headers=self.headers)
#             files_resp.raise_for_status()
#             files_data = files_resp.json()

#         changed_files = [
#             {
#                 "filename": f["filename"],
#                 "status":   f["status"],
#                 "changes":  f["changes"],
#                 "additions":f["additions"],
#                 "deletions":f["deletions"],
#             }
#             for f in files_data
#         ]

#         sensitive_files = _detect_sensitive_files(changed_files)
#         full_diff       = diff_resp.text

#         logger.info(
#             f"[GitHub] PR #{pr_number} | "
#             f"files={len(changed_files)} | sensitive={len(sensitive_files)}"
#         )

#         return {
#             "title":          meta.get("title", ""),
#             "body":           meta.get("body", "") or "No description.",
#             "author":         meta.get("user", {}).get("login", "unknown"),
#             "pr_url":         meta.get("html_url", ""),
#             "state":          meta.get("state", "open"),
#             "base_branch":    meta["base"]["ref"],
#             "head_branch":    meta["head"]["ref"],
#             "files_changed":  meta.get("changed_files", 0),
#             "additions":      meta.get("additions", 0),
#             "deletions":      meta.get("deletions", 0),
#             "commits":        meta.get("commits", 0),
#             "changed_files":  changed_files,
#             "sensitive_files":sensitive_files,
#             "diff":           full_diff[:8000],
#             "diff_truncated": len(full_diff) > 8000,
#         }

#     async def get_pr_commit_history(self, repo: str, pr_number: int) -> list[dict]:
#         """PR ke commits ki list — intent samajhne ke liye."""
#         url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}/commits"
#         async with httpx.AsyncClient(timeout=30.0) as client:
#             resp = await client.get(url, headers=self.headers)
#             resp.raise_for_status()
#         return [
#             {
#                 "sha":     c["sha"][:8],
#                 "message": c["commit"]["message"].split("\n")[0],
#                 "author":  c["commit"]["author"]["name"],
#             }
#             for c in resp.json()[:20]
#         ]

#     async def list_pr_files(self, repo: str, pr_number: int) -> list[dict]:
#         """PR mein changed files."""
#         url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}/files"
#         async with httpx.AsyncClient(timeout=30.0) as client:
#             resp = await client.get(url, headers=self.headers)
#             resp.raise_for_status()
#         files = resp.json()
#         changed = [{"filename": f["filename"], "status": f["status"], "changes": f["changes"]} for f in files]
#         sensitive = _detect_sensitive_files(changed)
#         if sensitive:
#             logger.warning(f"[GitHub] Sensitive files: {sensitive}")
#         return changed

#     async def get_repo_contributors(self, repo: str) -> list[str]:
#         """Top contributors — reviewer suggestion ke liye."""
#         url = f"{self.base_url}/repos/{repo}/contributors"
#         async with httpx.AsyncClient(timeout=30.0) as client:
#             resp = await client.get(url, headers=self.headers)
#             if resp.status_code == 403:
#                 return []
#             resp.raise_for_status()
#         return [c["login"] for c in resp.json()[:5]]

#     async def add_pr_comment(self, repo: str, pr_number: int, body: str) -> dict:
#         """PR pe AI review comment post karo."""
#         url = f"{self.base_url}/repos/{repo}/issues/{pr_number}/comments"
#         async with httpx.AsyncClient(timeout=30.0) as client:
#             resp = await client.post(url, headers=self.headers, json={"body": body})
#             resp.raise_for_status()
#         data = resp.json()
#         logger.info(f"[GitHub] Comment posted on PR #{pr_number}")
#         return {"comment_id": data["id"], "url": data["html_url"]}

#     async def add_pr_review(
#         self,
#         repo:      str,
#         pr_number: int,
#         body:      str,
#         event:     str = "COMMENT",  # APPROVE | REQUEST_CHANGES | COMMENT
#     ) -> dict:
#         """
#         Formal GitHub Review submit karo.
#         APPROVE         → PR approve (low risk)
#         REQUEST_CHANGES → Changes maango (high/critical)
#         COMMENT         → Sirf comment (medium)
#         """
#         url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}/reviews"
#         async with httpx.AsyncClient(timeout=30.0) as client:
#             resp = await client.post(url, headers=self.headers, json={"body": body, "event": event})
#             resp.raise_for_status()
#         logger.info(f"[GitHub] Review submitted: {event} on PR #{pr_number}")
#         return {"review_id": resp.json()["id"], "event": event}

#     async def set_pr_label(self, repo: str, pr_number: int, labels: list[str]) -> dict:
#         """Risk label PR pe lagao — visually dikhta hai PR list mein."""
#         url = f"{self.base_url}/repos/{repo}/issues/{pr_number}/labels"
#         async with httpx.AsyncClient(timeout=30.0) as client:
#             resp = await client.post(url, headers=self.headers, json={"labels": labels})
#             resp.raise_for_status()
#         logger.info(f"[GitHub] Labels set on PR #{pr_number}: {labels}")
#         return {"labels": labels}

#     async def merge_pr(self, repo: str, pr_number: int, commit_message: str) -> dict:
#         """
#         PR auto-merge karo.
#         SIRF tab call hota hai: risk=low + auto_merge=True + no concerns.
#         Squash merge = clean git history.
#         """
#         url     = f"{self.base_url}/repos/{repo}/pulls/{pr_number}/merge"
#         payload = {
#             "commit_title":   commit_message,
#             "commit_message": "Auto-merged by AI DevOps Orchestrator.",
#             "merge_method":   "squash",
#         }
#         async with httpx.AsyncClient(timeout=30.0) as client:
#             resp = await client.put(url, headers=self.headers, json=payload)
#             resp.raise_for_status()
#         logger.info(f"[GitHub] Auto-merged PR #{pr_number}")
#         return {"merged": True, "sha": resp.json().get("sha", "")}

#     async def close_pr(self, repo: str, pr_number: int) -> dict:
#         """Critical risk PR close karo (merge nahi)."""
#         url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}"
#         async with httpx.AsyncClient(timeout=30.0) as client:
#             resp = await client.patch(url, headers=self.headers, json={"state": "closed"})
#             resp.raise_for_status()
#         logger.warning(f"[GitHub] Closed PR #{pr_number} — critical risk")
#         return {"closed": True, "pr_number": pr_number}

#     async def assign_pr_reviewer(self, repo: str, pr_number: int, reviewers: list[str]) -> dict:
#         """PR pe reviewers assign karo."""
#         url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}/requested_reviewers"
#         async with httpx.AsyncClient(timeout=30.0) as client:
#             resp = await client.post(url, headers=self.headers, json={"reviewers": reviewers})
#             resp.raise_for_status()
#         logger.info(f"[GitHub] Reviewers assigned: {reviewers}")
#         return {"assigned": reviewers}


"""
=============================================================================
app/agent/tools/github_tool.py — GITHUB MCP TOOL
=============================================================================
PURPOSE:
  GitHub REST API v3 ke saath communication ka complete wrapper.
  AI Agent directly HTTP calls nahi karta — ye tool call karta hai.

  MCP (Model Context Protocol) concept:
  AI agent ke paas defined "tools" hote hain jinhe woh call kar sakta hai.
  Har tool sirf ek kaam karta hai — single responsibility.

METHODS:
  get_pr_diff()           — PR diff + metadata + file-level stats fetch karo
  get_pr_commit_history() — PR ke commits ka history fetch karo
  add_pr_comment()        — AI review comment PR pe post karo
  add_pr_review()         — Formal GitHub Review submit karo (APPROVE/REQUEST_CHANGES)
  set_pr_label()          — Risk level ka label PR pe lagao
  merge_pr()              — PR automatically merge karo (sirf low risk pe)
  close_pr()              — Critical risk PR ko close karo
  list_pr_files()         — Changed files ki list + sensitive file detection
  assign_pr_reviewer()    — Reviewers assign karo
  get_repo_contributors() — Repo ke contributors fetch karo (reviewer suggestion ke liye)
=============================================================================
"""

import httpx

from backend.core.config import settings
from backend.core.logger import get_logger

logger = get_logger(__name__)

# ── Sensitive file patterns — in files mein changes high/critical risk hoti hai
SENSITIVE_FILE_PATTERNS = (
    ".env", "secret", "password", "credential", "token",  # Secrets
    "settings.py", "config.py", "config.yml", "config.json",  # Config
    "migration", "schema.sql", "models.py",  # Database
    "requirements.txt", "package.json", "Pipfile",  # Dependencies
    "dockerfile", "docker-compose", ".github/workflows",  # Infrastructure
    "nginx.conf", "apache", ".htaccess",  # Server config
    "id_rsa", "id_ed25519", ".pem", ".key", ".cert",  # Certificates
)


def _detect_sensitive_files(files: list[dict]) -> list[str]:
    """
    Changed files mein sensitive patterns dhoondhao.
    Ye list LLM ko extra context deti hai risk assessment ke liye.
    """
    found = []
    for f in files:
        filename = f.get("filename", "").lower()
        for pattern in SENSITIVE_FILE_PATTERNS:
            if pattern in filename:
                found.append(f["filename"])
                break
    return found


class GitHubTool:
    """
    GitHub REST API v3 wrapper.
    Har method ek specific GitHub operation perform karta hai.
    Sab methods async hain — FastAPI event loop ke saath compatible.
    """

    def __init__(self):
        self.base_url = settings.github_api_url
        self.headers = {
            "Authorization":        f"token {settings.github_token}",
            "Accept":               "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    # ==========================================================================
    # DATA FETCHING METHODS
    # ==========================================================================

    async def get_pr_diff(self, repo: str, pr_number: int) -> dict:
        """
        PR ka complete data fetch karo — metadata, diff, aur file stats.

        3 API calls karta hai:
          1. PR metadata  — title, author, branches, stats
          2. PR diff      — actual code changes (git diff format)
          3. Changed files — file-level breakdown with sensitive file detection

        Diff ko 8,000 characters pe truncate kiya hai:
          - Groq LLM ka context window limited hota hai
          - 8000 chars mein usually enough context hota hai review ke liye
          - Isse AI cost bhi control mein rehti hai

        Returns:
            dict with all PR data needed for LLM analysis
        """
        pr_url   = f"{self.base_url}/repos/{repo}/pulls/{pr_number}"
        diff_headers = {**self.headers, "Accept": "application/vnd.github.v3.diff"}
        files_url = f"{pr_url}/files"

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Call 1: PR metadata
            meta_resp = await client.get(pr_url, headers=self.headers)
            meta_resp.raise_for_status()
            meta = meta_resp.json()

            # Call 2: Raw git diff
            diff_resp = await client.get(pr_url, headers=diff_headers)
            diff_resp.raise_for_status()

            # Call 3: File-level details
            files_resp = await client.get(files_url, headers=self.headers)
            files_resp.raise_for_status()
            files_data = files_resp.json()

        # Changed files parse karo
        changed_files = [
            {
                "filename": f["filename"],
                "status":   f["status"],    # added | modified | removed | renamed
                "changes":  f["changes"],   # total line changes
                "additions":f["additions"],
                "deletions":f["deletions"],
            }
            for f in files_data
        ]

        # Sensitive files detect karo — LLM ko extra context milega
        sensitive_files = _detect_sensitive_files(changed_files)

        full_diff = diff_resp.text

        logger.info(
            f"[GitHub] Fetched PR #{pr_number} | "
            f"files={len(changed_files)} | "
            f"sensitive={len(sensitive_files)} | "
            f"diff_chars={len(full_diff)}"
        )

        return {
            # PR Basic Info
            "title":           meta.get("title", ""),
            "body":            meta.get("body", "") or "No description provided.",
            "author":          meta.get("user", {}).get("login", "unknown"),
            "pr_url":          meta.get("html_url", ""),
            "state":           meta.get("state", "open"),

            # Branch Info
            "base_branch":     meta["base"]["ref"],
            "head_branch":     meta["head"]["ref"],

            # Change Stats
            "files_changed":   meta.get("changed_files", 0),
            "additions":       meta.get("additions", 0),
            "deletions":       meta.get("deletions", 0),
            "commits":         meta.get("commits", 0),

            # File Details
            "changed_files":   changed_files,
            "sensitive_files": sensitive_files,  # ← Extra context for LLM

            # Code Diff (truncated for LLM context window)
            "diff":            full_diff[:8000],
            "diff_truncated":  len(full_diff) > 8000,  # LLM ko batao agar truncated hai
        }

    async def get_pr_commit_history(self, repo: str, pr_number: int) -> list[dict]:
        """
        PR ke commits ki list fetch karo.

        Commit messages se PR ka intent samajhna aasaan hota hai.
        Example: "fix: SQL injection vulnerability" → automatically high risk.
        """
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}/commits"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=self.headers)
            resp.raise_for_status()

        commits = resp.json()
        return [
            {
                "sha":     c["sha"][:8],  # Short SHA (first 8 chars)
                "message": c["commit"]["message"].split("\n")[0],  # First line only
                "author":  c["commit"]["author"]["name"],
            }
            for c in commits[:20]  # Max 20 commits
        ]

    async def list_pr_files(self, repo: str, pr_number: int) -> list[dict]:
        """
        PR mein changed files ki list fetch karo.
        Sensitive file detection ke saath.
        """
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}/files"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=self.headers)
            resp.raise_for_status()

        files = resp.json()
        changed = [
            {
                "filename": f["filename"],
                "status":   f["status"],
                "changes":  f["changes"],
            }
            for f in files
        ]

        sensitive = _detect_sensitive_files(changed)
        if sensitive:
            logger.warning(f"[GitHub] Sensitive files detected in PR: {sensitive}")

        return changed

    async def get_repo_contributors(self, repo: str) -> list[str]:
        """
        Repo ke top contributors fetch karo.
        PR reviewer suggestion ke liye use hota hai.
        """
        url = f"{self.base_url}/repos/{repo}/contributors"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=self.headers)
            if resp.status_code == 403:
                return []  # Private repo — gracefully handle
            resp.raise_for_status()

        contributors = resp.json()
        # Top 5 contributors return karo (PR author ko exclude karo)
        return [c["login"] for c in contributors[:5]]

    # ==========================================================================
    # ACTION METHODS
    # ==========================================================================

    async def add_pr_comment(self, repo: str, pr_number: int, body: str) -> dict:
        """
        PR pe plain comment post karo.
        AI review summary is comment mein hogi — markdown format mein.
        """
        url = f"{self.base_url}/repos/{repo}/issues/{pr_number}/comments"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                url, headers=self.headers, json={"body": body}
            )
            resp.raise_for_status()

        data = resp.json()
        logger.info(f"[GitHub] AI comment posted on PR #{pr_number} — {data['html_url']}")
        return {"comment_id": data["id"], "url": data["html_url"]}

    async def add_pr_review(
        self,
        repo:       str,
        pr_number:  int,
        body:       str,
        event:      str = "COMMENT",  # APPROVE | REQUEST_CHANGES | COMMENT
    ) -> dict:
        """
        GitHub ka formal Review submit karo — sirf comment se zyada powerful.

        event values:
          APPROVE          → PR approve karo (low risk)
          REQUEST_CHANGES  → Changes maango (high/critical risk)
          COMMENT          → Sirf comment, koi decision nahi (medium risk)

        Formal review se PR merge conditions bhi affect hoti hain
        agar branch protection rules enabled hon.
        """
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}/reviews"
        payload = {"body": body, "event": event}

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=self.headers, json=payload)
            resp.raise_for_status()

        logger.info(f"[GitHub] Formal review submitted: {event} on PR #{pr_number}")
        return {"review_id": resp.json()["id"], "event": event}

    async def set_pr_label(self, repo: str, pr_number: int, labels: list[str]) -> dict:
        """
        PR pe labels lagao — visual risk indicator ke tor pe.

        Labels automatically create ho jaate hain agar exist nahi karte.
        Examples:
          ["ai-reviewed", "risk:low"]    → Low risk PR
          ["ai-reviewed", "risk:high"]   → High risk — manual review needed
          ["ai-reviewed", "risk:critical", "do-not-merge"] → Block karo
        """
        url = f"{self.base_url}/repos/{repo}/issues/{pr_number}/labels"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                url, headers=self.headers, json={"labels": labels}
            )
            resp.raise_for_status()

        logger.info(f"[GitHub] Labels set on PR #{pr_number}: {labels}")
        return {"labels": labels}

    async def merge_pr(self, repo: str, pr_number: int, commit_message: str) -> dict:
        """
        PR automatically merge karo.

        IMPORTANT SAFETY RULES:
          - Ye function SIRF tab call hota hai jab:
            1. risk_level == "low"
            2. auto_merge == True (LLM ne explicitly approve kiya)
            3. concerns list empty hai
          - Squash merge use karta hai → poori PR ke commits ek
            clean commit mein compress hote hain → git history clean rehti hai

        Squash vs Merge vs Rebase:
          squash  → sab commits ek mein → cleaner history ✅ (hum ye use karte hain)
          merge   → merge commit banta hai → history mein extra node
          rebase  → commits replay hote hain → complex history
        """
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}/merge"
        payload = {
            "commit_title":   commit_message,
            "commit_message": "Auto-merged by AI DevOps Orchestrator after risk assessment.",
            "merge_method":   "squash",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.put(url, headers=self.headers, json=payload)
            resp.raise_for_status()

        logger.info(f"[GitHub] ✅ Auto-merged PR #{pr_number} in {repo}")
        return {"merged": True, "sha": resp.json().get("sha", "")}

    async def close_pr(self, repo: str, pr_number: int) -> dict:
        """
        PR close karo (merge nahi, sirf close).
        Critical risk PR pe call hota hai jab auto_merge=False ho.
        Comment posting ke baad call karo taake team ko pata chale.
        """
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.patch(
                url, headers=self.headers, json={"state": "closed"}
            )
            resp.raise_for_status()

        logger.warning(f"[GitHub] ⛔ Closed PR #{pr_number} — Critical risk detected")
        return {"closed": True, "pr_number": pr_number}

    async def assign_pr_reviewer(
        self, repo: str, pr_number: int, reviewers: list[str]
    ) -> dict:
        """
        PR pe GitHub users ko reviewer assign karo.

        Note: reviewers mein GitHub usernames chahiye (not email, not display name).
        LLM roles suggest karta hai (e.g. "security engineer") — in roles ko
        actual GitHub usernames se map karna manually configure karna hoga.
        """
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}/requested_reviewers"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                url,
                headers=self.headers,
                json={"reviewers": reviewers},
            )
            resp.raise_for_status()

        logger.info(f"[GitHub] Reviewers assigned to PR #{pr_number}: {reviewers}")
        return {"assigned": reviewers}