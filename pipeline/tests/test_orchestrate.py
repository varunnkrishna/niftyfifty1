"""Phase 7 acceptance tests (PHASES.md): immutability-violation detection,
a killed-mid-FETCH run alerting and committing nothing, idempotent reruns
being a no-op, the day-type resolver, and IndexNow's URL construction —
all without touching the network or a real git remote.
"""

from __future__ import annotations

import json
import subprocess
from datetime import date
from unittest.mock import patch

import pytest

from pipeline.orchestrate import check_immutability, postdeploy, run_premarket
from pipeline.orchestrate.resolve import resolve


def _init_scratch_repo(tmp_path):
	subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
	subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, check=True)
	subprocess.run(["git", "config", "user.name", "test"], cwd=tmp_path, check=True)
	(tmp_path / "data" / "days").mkdir(parents=True)
	return tmp_path


def _commit_sidecar(tmp_path, sidecar: dict, message: str):
	path = tmp_path / "data" / "days" / f"{sidecar['date']}.json"
	path.write_text(json.dumps(sidecar))
	subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
	subprocess.run(["git", "commit", "-q", "-m", message], cwd=tmp_path, check=True)


class TestImmutabilityCheck:
	def test_eod_commit_that_mutates_premarket_fails(self, tmp_path, monkeypatch):
		_init_scratch_repo(tmp_path)
		_commit_sidecar(tmp_path, {"date": "2026-07-20", "premarket": {"gift_nifty": {"vote": 1}}, "eod_written": False}, "premarket 2026-07-20")
		_commit_sidecar(tmp_path, {"date": "2026-07-20", "premarket": {"gift_nifty": {"vote": -1}}, "eod_written": True, "eod": {}}, "eod 2026-07-20")

		monkeypatch.setattr(check_immutability, "REPO_ROOT", tmp_path)
		assert check_immutability.check_commit("HEAD") == 1

	def test_legitimate_eod_commit_passes(self, tmp_path, monkeypatch):
		_init_scratch_repo(tmp_path)
		_commit_sidecar(tmp_path, {"date": "2026-07-20", "premarket": {"gift_nifty": {"vote": 1}}, "eod_written": False}, "premarket 2026-07-20")
		_commit_sidecar(tmp_path, {"date": "2026-07-20", "premarket": {"gift_nifty": {"vote": 1}}, "eod_written": True, "eod": {"conclusion": "x"}}, "eod 2026-07-20")

		monkeypatch.setattr(check_immutability, "REPO_ROOT", tmp_path)
		assert check_immutability.check_commit("HEAD") == 0

	def test_non_eod_commit_is_skipped(self, tmp_path, monkeypatch):
		_init_scratch_repo(tmp_path)
		_commit_sidecar(tmp_path, {"date": "2026-07-20", "premarket": {}}, "premarket 2026-07-20")

		monkeypatch.setattr(check_immutability, "REPO_ROOT", tmp_path)
		assert check_immutability.check_commit("HEAD") == 0


class TestKilledMidFetch:
	def test_fetch_failure_alerts_high_and_commits_nothing(self):
		with (
			patch("pipeline.orchestrate.run_premarket.git_pull"),
			patch("pipeline.orchestrate.run_premarket.check_holiday_calendar_expiry", return_value=None),
			patch("pipeline.orchestrate.run_premarket.missed_day_check"),
			patch("pipeline.orchestrate.run_premarket.resolve", return_value=("trading", None)),
			patch("pipeline.orchestrate.run_premarket.load_day_sidecar", return_value=None),
			patch("pipeline.orchestrate.run_premarket.load_prev_day_sidecar", return_value=None),
			patch("pipeline.orchestrate.run_premarket.load_signal_config", return_value={}),
			patch("pipeline.orchestrate.run_premarket.build_raw_fetch", side_effect=RuntimeError("network unreachable mid-fetch")),
			patch("pipeline.orchestrate.run_premarket.commit_and_push") as mock_commit,
			patch("pipeline.orchestrate.run_premarket.send_alert") as mock_alert,
		):
			exit_code = run_premarket.run("2026-07-20")

		assert exit_code == 1
		mock_commit.assert_not_called()
		mock_alert.assert_called_once()
		severity, message = mock_alert.call_args[0]
		assert severity == "high"
		assert "2026-07-20" in message


class TestIdempotentRerun:
	def test_already_published_phase_is_a_noop(self):
		already_published = {"date": "2026-07-20", "premarket": {"gift_nifty": {"vote": 1}}, "eod_written": False}
		with (
			patch("pipeline.orchestrate.run_premarket.git_pull"),
			patch("pipeline.orchestrate.run_premarket.check_holiday_calendar_expiry", return_value=None),
			patch("pipeline.orchestrate.run_premarket.missed_day_check"),
			patch("pipeline.orchestrate.run_premarket.resolve", return_value=("trading", None)),
			patch("pipeline.orchestrate.run_premarket.load_day_sidecar", return_value=already_published),
			patch("pipeline.orchestrate.run_premarket.build_raw_fetch") as mock_fetch,
			patch("pipeline.orchestrate.run_premarket.commit_and_push") as mock_commit,
		):
			exit_code = run_premarket.run("2026-07-20")

		assert exit_code == 0
		mock_fetch.assert_not_called()  # no re-fetch, no re-compose -> nothing to diff
		mock_commit.assert_not_called()


class TestResolver:
	def test_2026_holiday_routes_to_holiday(self):
		day_type, reason = resolve(date(2026, 1, 26))
		assert day_type == "holiday"
		assert reason == "Republic Day"

	def test_saturday_routes_to_weekend(self):
		day_type, reason = resolve(date(2026, 7, 11))
		assert day_type == "weekend"
		assert reason is None

	def test_trading_day_has_no_reason(self):
		day_type, reason = resolve(date(2026, 7, 9))
		assert day_type == "trading"
		assert reason is None


class TestIndexNow:
	def test_ping_sends_correct_day_url(self):
		captured = {}

		def fake_post(url, json, timeout):
			captured["url"] = url
			captured["payload"] = json

			class Resp:
				def raise_for_status(self):
					pass

			return Resp()

		with (
			patch("pipeline.orchestrate.postdeploy.os.environ.get", return_value="fake-indexnow-key"),
			patch("pipeline.orchestrate.postdeploy.requests.post", side_effect=fake_post),
		):
			result = postdeploy.ping_indexnow("2026-07-09")

		assert result is True
		assert captured["url"] == "https://api.indexnow.org/indexnow"
		assert captured["payload"]["key"] == "fake-indexnow-key"
		assert captured["payload"]["urlList"] == ["https://niftyfiftyone.com/2026/07/09/"]
		assert captured["payload"]["host"] == "niftyfiftyone.com"

	def test_missing_key_skips_ping(self):
		with patch("pipeline.orchestrate.postdeploy.os.environ.get", return_value=None):
			assert postdeploy.ping_indexnow("2026-07-09") is False
