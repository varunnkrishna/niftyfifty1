"""CI check (ORCHESTRATION §6b): on any `eod *` commit, the `premarket`
object inside that day's sidecar JSON must be byte-identical to the
previous commit's version — the mechanical enforcement of CLAUDE.md rule 2
("the EOD write never modifies pre-market data").
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EOD_COMMIT_RE = re.compile(r"^eod (\d{4}-\d{2}-\d{2})$")


def _git_show(ref: str, path: str) -> str | None:
	result = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=REPO_ROOT, capture_output=True, text=True)
	return result.stdout if result.returncode == 0 else None


def check_commit(commit_sha: str = "HEAD") -> int:
	message = subprocess.run(
		["git", "log", "-1", "--format=%s", commit_sha], cwd=REPO_ROOT, capture_output=True, text=True
	).stdout.strip()

	match = EOD_COMMIT_RE.match(message)
	if not match:
		print(f"Commit message {message!r} doesn't match 'eod YYYY-MM-DD' — immutability check doesn't apply here.")
		return 0

	iso_date = match.group(1)
	rel_path = f"data/days/{iso_date}.json"

	before_text = _git_show(f"{commit_sha}~1", rel_path)
	after_text = _git_show(commit_sha, rel_path)

	if before_text is None:
		print(f"No prior version of {rel_path} at {commit_sha}~1 — can't verify immutability. Failing safe.")
		return 1
	if after_text is None:
		print(f"{rel_path} doesn't exist at {commit_sha} — unexpected for an eod commit.")
		return 1

	before_premarket = json.loads(before_text).get("premarket")
	after_premarket = json.loads(after_text).get("premarket")

	if before_premarket != after_premarket:
		print(f"IMMUTABILITY VIOLATION: `premarket` in {rel_path} changed between {commit_sha}~1 and {commit_sha}.")
		return 1

	print(f"OK: `premarket` in {rel_path} is unchanged by this eod commit.")
	return 0


if __name__ == "__main__":
	raise SystemExit(check_commit(sys.argv[1] if len(sys.argv) > 1 else "HEAD"))
