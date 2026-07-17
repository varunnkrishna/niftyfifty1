"""Sidecar JSON schema (PLANNING.md §4) — the pipeline's own pre-commit
validation gate (ORCHESTRATION §6a). Mirrors, and is intentionally
redundant with, the Astro content-collection Zod schema in
src/content.config.ts (ORCHESTRATION §6's "three layers" of validation).

A malformed sidecar JSON must fail here, loudly, before anything is
assembled or committed (CLAUDE.md: "validation is a feature").
"""

from __future__ import annotations

import re
from datetime import date as date_type
from typing import Annotated, Literal

from pydantic import BaseModel, Field, HttpUrl, TypeAdapter, field_validator, model_validator

Vote = Literal[-1, 0, 1]
BiasLabel = Literal["Long", "Short", "Neutral", "Cautious"]
BiasIntensity = Literal["Mildly", "Strongly"]
Conviction = Literal["normal", "reduced"]
DataQuality = Literal["full", "partial", "outage"]

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class VotedMetric(BaseModel):
	model_config = {"extra": "forbid"}

	value: str | float | int | None = None
	delta_pct: float | None = None
	delta: float | None = None
	vote: Vote | None = None
	unavailable: bool = False

	@model_validator(mode="after")
	def _unavailable_implies_no_vote(self) -> "VotedMetric":
		if self.unavailable and self.vote is not None:
			raise ValueError("unavailable metric must not carry a vote")
		return self


class NewsItem(BaseModel):
	model_config = {"extra": "forbid"}

	headline_reworded: str = Field(min_length=1)
	why_it_matters: str = Field(min_length=1)
	source_name: str = Field(min_length=1)
	# CLAUDE.md rule 5: "A news item without a real URL is invalid."
	source_url: HttpUrl
	timestamp: str

	@field_validator("timestamp")
	@classmethod
	def _timestamp_looks_like_iso(cls, v: str) -> str:
		if "T" not in v:
			raise ValueError("timestamp must be ISO 8601 (e.g. 2026-07-09T08:12:00+05:30)")
		return v


class CloseMetric(BaseModel):
	model_config = {"extra": "forbid"}

	value: float
	delta_pct: float


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


class Premarket(BaseModel):
	model_config = {"extra": "forbid"}

	gift_nifty: VotedMetric
	sp500_overnight: VotedMetric
	nasdaq_overnight: VotedMetric
	us10y_yield: VotedMetric
	dxy: VotedMetric
	fii_net_cash: VotedMetric
	dii_net_cash: VotedMetric
	usdinr: VotedMetric
	prev_close_in_range: VotedMetric
	india_vix: VotedMetric  # conviction dampener, vote always null
	brent: VotedMetric  # context note only, vote always null

	bias_score: int | None = None
	bias_label: BiasLabel | None = None
	bias_intensity: BiasIntensity | None = None
	conviction: Conviction = "normal"
	market_expectations: str = Field(min_length=1)
	# min-1 news is enforced at the sidecar level, where data_quality is
	# visible — an outage day legitimately has nothing to list.
	news: list[NewsItem] = Field(default_factory=list, max_length=10)

	@model_validator(mode="after")
	def _bias_label_and_score_agree(self) -> "Premarket":
		if (self.bias_label is None) != (self.bias_score is None):
			raise ValueError("bias_label and bias_score must both be null (suppressed) or both set")
		return self

	@model_validator(mode="after")
	def _context_only_metrics_never_vote(self) -> "Premarket":
		if self.india_vix.vote is not None:
			raise ValueError("india_vix is a conviction dampener and must never carry a vote")
		if self.brent.vote is not None:
			raise ValueError("brent is context-only and must never carry a vote")
		return self


class Eod(BaseModel):
	model_config = {"extra": "forbid"}

	nifty_close: CloseMetric
	sensex_close: CloseMetric
	banknifty_close: CloseMetric
	advance_decline: str | None = None
	sector_leaders: list[str] = Field(default_factory=list)
	sector_laggards: list[str] = Field(default_factory=list)
	news: list[NewsItem] = Field(min_length=1, max_length=10)
	conclusion: str = Field(min_length=1)


class TradingDaySidecar(BaseModel):
	model_config = {"extra": "forbid"}

	date: str
	type: Literal["trading-day"]
	premarket: Premarket
	data_quality: DataQuality
	missing: list[str] = Field(default_factory=list)
	eod_written: bool
	eod: Eod | None = None
	# True when the EOD write is known to have been permanently missed
	# (pipeline outage) — flips the page from "awaiting EOD" to an honest
	# "EOD not captured" note instead of waiting forever.
	eod_missed: bool = False

	@field_validator("date")
	@classmethod
	def _date_format(cls, v: str) -> str:
		if not DATE_RE.match(v):
			raise ValueError("date must be YYYY-MM-DD")
		date_type.fromisoformat(v)  # raises if not a real calendar date
		return v

	@model_validator(mode="after")
	def _eod_matches_eod_written(self) -> "TradingDaySidecar":
		# CLAUDE.md rule 2: the EOD write never modifies pre-market data — the
		# mechanical form of that rule is that `eod` simply does not exist
		# until `eod_written` flips true.
		if self.eod_written and self.eod is None:
			raise ValueError("eod is required once eod_written is true")
		if not self.eod_written and self.eod is not None:
			raise ValueError("eod must be absent until eod_written is true")
		if self.eod_missed and self.eod_written:
			raise ValueError("eod_missed cannot be true once eod_written is true")
		return self

	@model_validator(mode="after")
	def _news_required_unless_outage(self) -> "TradingDaySidecar":
		# The one sanctioned empty-news case: an outage page honestly has
		# nothing to list (ORCHESTRATION §4 recovery decision, 2026-07-17).
		if self.data_quality != "outage" and not self.premarket.news:
			raise ValueError("premarket.news requires at least one item except on outage days")
		return self

	@model_validator(mode="after")
	def _missing_matches_data_quality_and_votes(self) -> "TradingDaySidecar":
		declared_missing = set(self.missing)
		actual_missing = {k for k in DIRECTIONAL_KEYS if getattr(self.premarket, k).unavailable}
		if declared_missing != actual_missing:
			raise ValueError(f"missing[] {sorted(declared_missing)} does not match unavailable directional inputs {sorted(actual_missing)}")

		n_missing = len(actual_missing)
		if self.data_quality == "full" and n_missing != 0:
			raise ValueError("data_quality is 'full' but directional inputs are marked unavailable")
		if self.data_quality == "partial" and n_missing == 0:
			raise ValueError("data_quality is 'partial' but no directional inputs are marked unavailable")

		# ORCHESTRATION §5b: >=4 missing directional inputs -> signal suppressed.
		if n_missing >= 4 and self.premarket.bias_label is not None:
			raise ValueError("bias_label must be null (suppressed) when >=4 directional inputs are missing")
		return self


class WeekendHolidaySidecar(BaseModel):
	model_config = {"extra": "forbid"}

	date: str
	type: Literal["weekend", "holiday"]
	reason: str | None = None
	# True only on a backfilled outage page — the pipeline never ran, so
	# there is honestly nothing to list (the only empty-news case).
	outage: bool = False
	news: list[NewsItem] = Field(default_factory=list)

	@field_validator("date")
	@classmethod
	def _date_format(cls, v: str) -> str:
		if not DATE_RE.match(v):
			raise ValueError("date must be YYYY-MM-DD")
		date_type.fromisoformat(v)
		return v

	@model_validator(mode="after")
	def _holiday_requires_reason(self) -> "WeekendHolidaySidecar":
		if self.type == "holiday" and not self.reason:
			raise ValueError("reason is required for holiday pages (e.g. 'Republic Day')")
		return self

	@model_validator(mode="after")
	def _news_required_unless_outage(self) -> "WeekendHolidaySidecar":
		if not self.outage and not self.news:
			raise ValueError("news requires at least one item except on outage pages")
		return self


DaySidecar = Annotated[
	TradingDaySidecar | WeekendHolidaySidecar,
	Field(discriminator="type"),
]


_day_sidecar_adapter: TypeAdapter[TradingDaySidecar | WeekendHolidaySidecar] = TypeAdapter(DaySidecar)


def parse_sidecar(data: dict) -> TradingDaySidecar | WeekendHolidaySidecar:
	"""Validate a raw sidecar JSON dict, raising pydantic.ValidationError with
	a clear message on any malformed input."""
	return _day_sidecar_adapter.validate_python(data)
