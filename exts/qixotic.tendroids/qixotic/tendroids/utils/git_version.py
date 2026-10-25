"""
Display version derived from git history.

Format is MAJOR.MINOR.PATCH (short hash): MINOR is the number of PRs merged
into origin/main (offset so main read 3 when this scheme began), PATCH is the
number of commits on the current branch that are not yet on origin/main. Local
main is used only when there is no origin/main.
"""

import subprocess
from pathlib import Path
from typing import Optional

MAJOR = 2
# 22 first-parent merges existed on main when the scheme began; that state is minor 3.
MINOR_OFFSET = 19

_REPO_DIR = Path(__file__).resolve().parent


def _git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=_REPO_DIR, text=True, stderr=subprocess.DEVNULL, timeout=5
    ).strip()


def get_git_version() -> Optional[str]:
    """Return e.g. '2.3.2 (f80ad00-dirty)', or None when not running from a git checkout."""
    try:
        # A shallow clone has too little history for the merge count to mean anything.
        if _git("rev-parse", "--is-shallow-repository") == "true":
            return None
        # origin/main advances on any fetch, so it does not go stale just because
        # local main was not pulled after a merge.
        for base in ("origin/main", "main"):
            try:
                # First-parent only: merges of main into a feature branch would
                # otherwise count as extra PRs.
                merges = int(_git("rev-list", "--count", "--merges", "--first-parent", base))
                break
            except subprocess.CalledProcessError:
                continue
        else:
            return None
        patch = int(_git("rev-list", "--count", f"{base}..HEAD"))
        short_hash = _git("rev-parse", "--short", "HEAD")
        # Untracked files count too: a new module is code Kit may be running.
        dirty = "-dirty" if _git("status", "--porcelain") else ""
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    return f"{MAJOR}.{merges - MINOR_OFFSET}.{patch} ({short_hash}{dirty})"
