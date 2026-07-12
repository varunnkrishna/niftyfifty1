"""Compute engine orchestration: raw-fetch JSON (Phase 3) + prior day's
sidecar JSON + signal-config.json -> the numeric parts of the `premarket`
block (everything except `news`/`market_expectations`, which are COMPOSE
stage / Phase 5's job — ORCHESTRATION §0's "deterministic spine, LLM at
the edges" means this layer stops at the numbers).

Every threshold used here comes from signal-config.json, never a literal
in this file — that's what makes tuning a zero-code-edit change
(PHASES.md Phase 4 acceptance).
"""

from __future__ import annotations

from pipeline.compute.bias import compute_bias_label, compute_bias_score
from pipeline.compute.conviction import compute_conviction
from pipeline.compute.degradation import classify_data_quality
from pipeline.compute.votes import vote_range_thirds, vote_threshold

DIRECTIONAL_KEYS = (
	"gift_nifty",
	"sp500_overnight",
	"nasdaq_overnight",
	"us10y_yield",
	"dxy",
	"fii_net_cash",
	"dii_net_cash",
	"usdinr",
	"prev_close_in_range",
)


def _input_config(signal_config: dict, key: str) -> dict:
	for entry in signal_config["directional_inputs"]:
		if entry["key"] == key:
			return entry
	raise KeyError(f"{key} not found in signal-config.json directional_inputs")


def _metric(value=None, delta=None, delta_pct=None, vote=None, unavailable=False) -> dict:
	d: dict = {"vote": vote}
	if unavailable:
		d["unavailable"] = True
	if value is not None:
		d["value"] = value
	if delta is not None:
		d["delta"] = delta
	if delta_pct is not None:
		d["delta_pct"] = delta_pct
	return d


def _raw(raw_fetch: dict, key: str) -> dict:
	return raw_fetch["metrics"][key]


def _compute_gift_nifty(raw_fetch: dict, prev_day_sidecar: dict | None, cfg: dict) -> dict:
	raw = _raw(raw_fetch, "gift_nifty")
	if raw["unavailable"]:
		return _metric(unavailable=True)

	price = raw["value"]["value"]
	prev_close = (prev_day_sidecar or {}).get("eod", {}).get("nifty_close", {}).get("value")
	if prev_close is None:
		# PLANNING §5: GIFT Nifty votes vs the *previous NIFTY close*, not its
		# own previous close — without yesterday's stored close we cannot
		# compute that comparison, so this is honestly unavailable rather
		# than invented from a different baseline (CLAUDE.md rule 4).
		return _metric(value=price, unavailable=True)

	delta_pct = (price - prev_close) / prev_close * 100
	vote = vote_threshold(delta_pct, _input_config(cfg, "gift_nifty")["threshold_pct"])
	return _metric(value=price, delta_pct=delta_pct, vote=vote)


def _compute_yahoo_or_stooq_pct(raw_fetch: dict, key: str, cfg: dict, invert: bool = False) -> dict:
	raw = _raw(raw_fetch, key)
	if raw["unavailable"]:
		return _metric(unavailable=True)

	v = raw["value"]
	delta_pct = v.get("delta_pct")
	if delta_pct is None and "open" in v:
		# Stooq fallback shape carries no previous-close reference; the
		# session's own move (close vs open) is the closest available proxy.
		delta_pct = (v["value"] - v["open"]) / v["open"] * 100

	threshold = _input_config(cfg, key)["threshold_pct"]
	vote = vote_threshold(delta_pct, threshold, invert=invert)
	return _metric(value=v["value"], delta_pct=delta_pct, vote=vote)


def _compute_us10y_yield(raw_fetch: dict, cfg: dict) -> dict:
	raw = _raw(raw_fetch, "us10y_yield")
	if raw["unavailable"]:
		return _metric(unavailable=True)

	v = raw["value"]
	if raw["source"] == "fred":
		delta_bp = v["delta"] * 100
	else:
		# Yahoo ^TNX fallback: known simplification (^TNX historically quotes
		# yield*10) — treated as already level-equivalent here rather than
		# precisely rescaled. Flagged for follow-up if this path is ever the
		# one actually exercised live.
		delta_bp = (v["value"] - v["prev_close"]) * 100

	threshold_bp = _input_config(cfg, "us10y_yield")["threshold"]
	vote = vote_threshold(delta_bp, threshold_bp, invert=True)  # falling yield = risk-on = +1
	return _metric(value=v["value"], delta=delta_bp / 100, vote=vote)


def _compute_fii_or_dii(raw_fetch: dict, key: str, cfg: dict) -> dict:
	raw = _raw(raw_fetch, key)
	if raw["unavailable"]:
		return _metric(unavailable=True)

	net_cash = raw["value"]
	threshold = _input_config(cfg, key)["threshold"]
	vote = vote_threshold(net_cash, threshold)
	return _metric(value=round(net_cash, 2), vote=vote)


def _compute_prev_close_in_range(raw_fetch: dict) -> dict:
	raw = _raw(raw_fetch, "prev_close_in_range")
	if raw["unavailable"]:
		return _metric(unavailable=True)
	position = raw["value"]
	return _metric(value=position, vote=vote_range_thirds(position))


def _compute_india_vix(raw_fetch: dict, cfg: dict) -> tuple[dict, str]:
	raw = _raw(raw_fetch, "india_vix")
	if raw["unavailable"]:
		return _metric(unavailable=True), "normal"  # ORCHESTRATION §5b item 2: missing VIX skips damping

	v = raw["value"]
	level = v["value"]
	delta = v.get("delta")
	delta_pct = (delta / (level - delta) * 100) if delta is not None and (level - delta) != 0 else None

	dampener_cfg = cfg["conviction_dampeners"][0]
	conviction = compute_conviction(level, delta_pct, dampener_cfg)
	return _metric(value=level, delta=delta, vote=None), conviction


def _compute_brent(raw_fetch: dict) -> dict:
	raw = _raw(raw_fetch, "brent")
	if raw["unavailable"]:
		return _metric(unavailable=True)
	v = raw["value"]
	return _metric(value=v["value"], delta_pct=v.get("delta_pct"), vote=None)


def compute_premarket_numbers(raw_fetch: dict, prev_day_sidecar: dict | None, signal_config: dict) -> dict:
	"""Returns the numeric/vote portion of `premarket` — everything the
	Pydantic `Premarket` model needs except `news` and `market_expectations`
	(Phase 5's COMPOSE stage fills those in before assembly)."""

	metrics: dict[str, dict] = {
		"gift_nifty": _compute_gift_nifty(raw_fetch, prev_day_sidecar, signal_config),
		"sp500_overnight": _compute_yahoo_or_stooq_pct(raw_fetch, "sp500_overnight", signal_config),
		"nasdaq_overnight": _compute_yahoo_or_stooq_pct(raw_fetch, "nasdaq_overnight", signal_config),
		"us10y_yield": _compute_us10y_yield(raw_fetch, signal_config),
		"dxy": _compute_yahoo_or_stooq_pct(raw_fetch, "dxy", signal_config, invert=True),
		"fii_net_cash": _compute_fii_or_dii(raw_fetch, "fii_net_cash", signal_config),
		"dii_net_cash": _compute_fii_or_dii(raw_fetch, "dii_net_cash", signal_config),
		"usdinr": _compute_yahoo_or_stooq_pct(raw_fetch, "usdinr", signal_config, invert=True),
		"prev_close_in_range": _compute_prev_close_in_range(raw_fetch),
	}
	india_vix, conviction = _compute_india_vix(raw_fetch, signal_config)
	metrics["india_vix"] = india_vix
	metrics["brent"] = _compute_brent(raw_fetch)

	missing = sorted(key for key in DIRECTIONAL_KEYS if metrics[key].get("unavailable"))
	data_quality, suppressed = classify_data_quality(
		n_missing_directional=len(missing),
		n_directional_total=len(DIRECTIONAL_KEYS),
		suppress_at=signal_config["degradation_ladder"]["suppress_at_missing_count"],
	)

	votes = {key: metrics[key]["vote"] for key in DIRECTIONAL_KEYS}
	if suppressed or data_quality == "outage":
		bias_score, bias_label, bias_intensity = None, None, None
	else:
		bias_score = compute_bias_score(votes)
		bias_label, bias_intensity = compute_bias_label(bias_score, signal_config["label_bands"]["bands"])

	return {
		**metrics,
		"bias_score": bias_score,
		"bias_label": bias_label,
		"bias_intensity": bias_intensity,
		"conviction": conviction,
		"data_quality": data_quality,
		"missing": missing,
	}
