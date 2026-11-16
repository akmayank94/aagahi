"""Indian National AQI (NAQI) sub-indices for PM2.5 and PM10 (DECISIONS D-005).

Models forecast concentrations; AQI is derived here with CPCB breakpoints, never predicted directly.
Breakpoints are 24-hour average concentrations in µg/m³ (CPCB National AQI, 2014/2015).

VERIFY IN B1: the upper concentration of the Severe band (used only to scale 401-500) must be
checked against CPCB's official NAQI document before any AQI number is published. Until then
SEVERE_UPPER is marked provisional and every value inside the Severe band is flagged.
"""

from __future__ import annotations

from dataclasses import dataclass

CATEGORIES = ("Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe")
AQI_BANDS = ((0, 50), (51, 100), (101, 200), (201, 300), (301, 400), (401, 500))

# (low, high) concentration per category; the last band's high is provisional (see module doc).
BREAKPOINTS: dict[str, tuple[tuple[float, float], ...]] = {
    "pm25": ((0, 30), (31, 60), (61, 90), (91, 120), (121, 250), (251, 380)),
    "pm10": ((0, 50), (51, 100), (101, 250), (251, 350), (351, 430), (431, 510)),
}
SEVERE_UPPER_IS_PROVISIONAL = True


@dataclass(frozen=True)
class SubIndex:
    pollutant: str
    concentration: float
    aqi: int
    category: str
    provisional: bool  # True when the value falls in the Severe band (upper breakpoint unverified)


def sub_index(pollutant: str, concentration: float) -> SubIndex:
    """AQI sub-index for one pollutant from its 24-h average concentration (µg/m³).

    Concentrations are rounded to whole µg/m³ first (CPCB tables use integer breakpoints),
    then linearly interpolated inside their band. Values above the table cap at 500.
    """
    if pollutant not in BREAKPOINTS:
        raise ValueError(f"unknown pollutant {pollutant!r}; expected one of {sorted(BREAKPOINTS)}")
    if concentration is None or concentration < 0:
        raise ValueError(f"concentration must be >= 0, got {concentration!r}")

    c = round(concentration)
    bands = BREAKPOINTS[pollutant]
    for i, ((b_lo, b_hi), (i_lo, i_hi)) in enumerate(zip(bands, AQI_BANDS, strict=True)):
        if c <= b_hi:
            aqi = (i_hi - i_lo) / (b_hi - b_lo) * (c - b_lo) + i_lo
            return SubIndex(pollutant, concentration, round(aqi), CATEGORIES[i], i == len(bands) - 1)
    return SubIndex(pollutant, concentration, 500, "Severe", True)


def aqi_from(pm25: float | None = None, pm10: float | None = None) -> SubIndex:
    """Overall AQI = the highest available sub-index (CPCB uses the maximum).

    CPCB requires at least three pollutants (one of them PM2.5 or PM10) for an official AQI;
    Aagahi forecasts only PM, so its AQI is labelled "PM-based AQI" in the product (D-005).
    """
    subs = [sub_index(p, v) for p, v in (("pm25", pm25), ("pm10", pm10)) if v is not None]
    if not subs:
        raise ValueError("need at least one of pm25, pm10")
    return max(subs, key=lambda s: s.aqi)
