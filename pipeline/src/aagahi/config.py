"""City configuration loader (D-025: a city is a config file).

Fails loudly on anything that would silently break the leakage rules, e.g. an unpinned weather model.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = REPO_ROOT / "configs"
FORBIDDEN_WEATHER_MODELS = {"best_match"}  # D-027
EXCLUDED_FIRE_SENSORS = {"VIIRS_SNPP"}  # D-015b


@dataclass(frozen=True)
class Station:
    id: str
    name: str
    agency: str
    lat: float
    lon: float
    openaq_id: int | None
    cpcb_id: str | None


@dataclass(frozen=True)
class CityConfig:
    city: str
    timezone: str
    weather_model: str
    weather_variables: tuple[str, ...]
    horizon_hours: int
    quantiles: tuple[float, ...]
    fire_sensors: tuple[str, ...]
    delay_minutes: dict[str, int]
    stations: tuple[Station, ...]
    raw: dict


class ConfigError(ValueError):
    pass


def load_city(name_or_path: str | Path) -> CityConfig:
    path = Path(name_or_path)
    if not path.suffix:
        path = CONFIG_DIR / f"{name_or_path}.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))

    model = raw["weather"]["model"]
    if model in FORBIDDEN_WEATHER_MODELS:
        raise ConfigError(f"weather.model {model!r} is forbidden (D-027): pin a named model")
    sensors = tuple(raw["fires"]["sensors"])
    bad = EXCLUDED_FIRE_SENSORS.intersection(sensors)
    if bad:
        raise ConfigError(f"fire sensors {sorted(bad)} are excluded (D-015b)")

    stations = tuple(Station(**s) for s in raw["stations"])
    ids = [s.id for s in stations]
    if len(ids) != len(set(ids)):
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        raise ConfigError(f"duplicate station ids: {dupes}")
    for s in stations:
        if not (-90 <= s.lat <= 90 and -180 <= s.lon <= 180):
            raise ConfigError(f"station {s.id} has invalid coordinates")

    return CityConfig(
        city=raw["city"],
        timezone=raw["timezone"],
        weather_model=model,
        weather_variables=tuple(raw["weather"]["variables"]),
        horizon_hours=int(raw["forecast"]["horizon_hours"]),
        quantiles=tuple(raw["forecast"]["quantiles"]),
        fire_sensors=sensors,
        delay_minutes=dict(raw["observations"]["delay_minutes"]),
        stations=stations,
        raw=raw,
    )
