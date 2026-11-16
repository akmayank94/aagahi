import pytest
import yaml

from aagahi.config import CONFIG_DIR, ConfigError, load_city
from aagahi.units import kg_m3_to_ug_m3, looks_like_kg_m3


def test_kg_to_ug():
    assert kg_m3_to_ug_m3(1.5e-7) == pytest.approx(150.0)  # a typical CAMS ADS winter value


def test_detects_unconverted_values():
    assert looks_like_kg_m3(1.5e-7)
    assert not looks_like_kg_m3(150.0)


def test_delhi_config_loads_and_follows_rules():
    cfg = load_city("delhi-ncr")
    assert cfg.weather_model == "gfs_seamless"
    assert "VIIRS_SNPP" not in cfg.fire_sensors
    assert len(cfg.stations) == 56
    assert cfg.delay_minutes["openaq_cpcb"] == 170
    assert cfg.horizon_hours == 72


def _write(tmp_path, mutate):
    raw = yaml.safe_load((CONFIG_DIR / "delhi-ncr.yaml").read_text(encoding="utf-8"))
    mutate(raw)
    p = tmp_path / "city.yaml"
    p.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return p


def test_best_match_is_rejected(tmp_path):
    p = _write(tmp_path, lambda r: r["weather"].update(model="best_match"))
    with pytest.raises(ConfigError, match="D-027"):
        load_city(p)


def test_snpp_is_rejected(tmp_path):
    p = _write(tmp_path, lambda r: r["fires"].update(sensors=["VIIRS_SNPP", "MODIS"]))
    with pytest.raises(ConfigError, match="D-015b"):
        load_city(p)


def test_duplicate_station_ids_rejected(tmp_path):
    p = _write(tmp_path, lambda r: r["stations"].append(dict(r["stations"][0])))
    with pytest.raises(ConfigError, match="duplicate"):
        load_city(p)
