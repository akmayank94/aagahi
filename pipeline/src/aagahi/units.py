"""Unit conversions with range guards (DATASETS trap T-14: CAMS ADS gives kg m^-3, stations give µg/m³)."""

from __future__ import annotations

KG_TO_UG = 1e9

# Plausible hourly PM range in µg/m³ after conversion. Above-range is allowed but flagged by data contracts.
PLAUSIBLE_PM_UG_M3 = (0.0, 2000.0)


def kg_m3_to_ug_m3(value: float) -> float:
    """Convert a mass concentration from kg/m³ (CAMS ADS NetCDF) to µg/m³."""
    if value is None:
        raise ValueError("value is None")
    return float(value) * KG_TO_UG


def looks_like_kg_m3(value_ug_m3: float) -> bool:
    """True when a value that should be µg/m³ is suspiciously tiny, i.e. was probably never converted."""
    return 0 < value_ug_m3 < 1e-3
