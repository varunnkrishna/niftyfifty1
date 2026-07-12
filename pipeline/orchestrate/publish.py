"""git commit + push (CLAUDE.md commit conventions: "premarket YYYY-MM-DD" ·
"eod YYYY-MM-DD" · "news YYYY-MM-DD"). A no-op when there's nothing staged
— the mechanical form of idempotency: a rerun of an already-published
phase touches no files, so there's nothing to commit (PHASES.md Phase 7
acceptance: "workflow_dispatch rerun of an already-successful phase
results in an empty diff").
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


class PublishError(Exception):
	pass


def _run(args: list[str]) -> subprocess.CompletedProcess:
	return subprocess.run(args, cwd=REPO_ROOT, capture_output=True, text=True)


def commit_and_push(files: list[Path], message: str, push: bool = True) -> bool:
	"""Returns True if a commit was made, False if there was nothing to
	commit (already up to date)."""
	add = _run(["git", "add", *[str(f) for f in files]])
	if add.returncode != 0:
		raise PublishError(f"git add failed: {add.stderr}")

	# Nothing staged relative to HEAD -> idempotent no-op, not an error.
	diff = _run(["git", "diff", "--cached", "--quiet"])
	if diff.returncode == 0:
		return False

	commit = _run(["git", "commit", "-m", message])
	if commit.returncode != 0:
		raise PublishError(f"git commit failed: {commit.stderr}")

	if push:
		pushed = _run(["git", "push"])
		if pushed.returncode != 0:
			raise PublishError(f"git push failed: {pushed.stderr}")

	return True
