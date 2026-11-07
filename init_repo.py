import os
import sys
from dotenv import load_dotenv

load_dotenv()

try:
    from github import Github, Auth, GithubException
except ImportError:
    print("[ERROR] PyGithub is not installed. Run: pip install PyGithub")
    sys.exit(1)


def prime_repository():
    github_pat = os.getenv("GITHUB_PAT")
    repo_name = os.getenv("GITHUB_REPO", "praesync/praesync-core")

    if not github_pat:
        print("[ERROR] GITHUB_PAT is missing from environment or .env file.")
        sys.exit(1)

    print(f"[*] Authenticating with GitHub for repository: {repo_name}...")

    try:
        if hasattr(Auth, "Token"):
            auth = Auth.Token(github_pat)
            gh = Github(auth=auth)
        else:
            gh = Github(github_pat)

        repo = gh.get_repo(repo_name)
    except Exception as e:
        print(f"[FATAL] Failed to access repository '{repo_name}': {e}")
        sys.exit(1)

    readme_content = (
        "# Praesync Core\n\n"
        "Autonomous incident response engine and stateless cluster telemetry mesh.\n\n"
        "## Architecture\n"
        "- Coordinator: `swarm-investigator`\n"
        "- Automated Remediation: `swarm-patcher`\n"
        "- Canary & Rollout: `swarm-ops`\n"
    )

    buggy_db_connection_code = '''"""
Database Connection Pool Manager
Simulates an unmanaged connection pool with socket exhaustion bug.
"""
import time
import socket
from typing import Optional, Dict, Any

_MAX_CONNECTIONS = 5
_ACTIVE_POOL: Dict[str, Any] = {}

class DatabasePoolError(Exception):
    """Raised when connection pool capacity is exceeded."""
    pass

def acquire_connection(timeout: float = 2.0):
    """
    Acquires an active socket from the auth-db-primary connection pool.
    BUG: Fails to reap stale sockets on transient timeout, causing pool exhaustion.
    """
    connection_id = f"conn-{len(_ACTIVE_POOL) + 1}"
    
    # Buggy condition: artificial pool exhaustion threshold
    if len(_ACTIVE_POOL) >= _MAX_CONNECTIONS:
        raise DatabasePoolError(
            "Sev-1: auth-db-primary connection pool exhausted. Socket timeout waiting for release."
        )

    # Simulate connection leak: connection added but never returned to pool
    _ACTIVE_POOL[connection_id] = {
        "host": "auth-db-primary.internal",
        "port": 5432,
        "acquired_at": time.time(),
        "status": "ALLOCATED"
    }
    return _ACTIVE_POOL[connection_id]

def release_connection(connection_id: str):
    """Release socket back to pool."""
    _ACTIVE_POOL.pop(connection_id, None)
'''

    target_file = os.getenv("HOTFIX_TARGET_FILE", "app/database/connection.py")
    branch = "main"

    print(f"[*] Priming branch '{branch}' in {repo.full_name}...")

    # 1. Initialize README.md (creates initial commit on empty repo)
    try:
        existing_readme = repo.get_contents("README.md", ref=branch)
        repo.update_file(
            path="README.md",
            message="chore: update README.md initialization",
            content=readme_content,
            sha=existing_readme.sha,
            branch=branch,
        )
        print("  [+] README.md updated on main branch.")
    except Exception:
        try:
            repo.create_file(
                path="README.md",
                message="chore: initialize repository with README.md",
                content=readme_content,
                branch=branch,
            )
            print("  [+] README.md created on main branch (Initial Commit).")
        except Exception as e:
            print(f"  [!] Failed to commit README.md: {e}")

    # 2. Commit buggy DB connection file
    try:
        existing_code = repo.get_contents(target_file, ref=branch)
        repo.update_file(
            path=target_file,
            message="feat(database): initialize connection pool manager with baseline logic",
            content=buggy_db_connection_code,
            sha=existing_code.sha,
            branch=branch,
        )
        print(f"  [+] {target_file} updated on main branch.")
    except Exception:
        try:
            repo.create_file(
                path=target_file,
                message="feat(database): initialize connection pool manager with baseline logic",
                content=buggy_db_connection_code,
                branch=branch,
            )
            print(f"  [+] {target_file} created on main branch.")
        except Exception as e:
            print(f"  [!] Failed to commit {target_file}: {e}")

    print("\n========================================================")
    print(f" SUCCESS: Repository '{repo.full_name}' is primed and ready!")
    print(f" Default branch: {branch}")
    print(f" Hotfix target primed: {target_file}")
    print(" ReAct loop is now ready to fork, commit, and create PRs.")
    print("========================================================\n")


if __name__ == "__main__":
    prime_repository()

