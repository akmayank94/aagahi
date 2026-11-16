import pytest

from aagahi.aqi import aqi_from, sub_index


@pytest.mark.parametrize(
    ("conc", "aqi", "category"),
    [
        (0, 0, "Good"),
        (30, 50, "Good"),
        (31, 51, "Satisfactory"),
        (60, 100, "Satisfactory"),
        (61, 101, "Moderate"),
        (90, 200, "Moderate"),
        (91, 201, "Poor"),
        (120, 300, "Poor"),
        (121, 301, "Very Poor"),
        (250, 400, "Very Poor"),
    ],
)
def test_pm25_band_edges(conc, aqi, category):
    s = sub_index("pm25", conc)
    assert (s.aqi, s.category, s.provisional) == (aqi, category, False)


@pytest.mark.parametrize(("conc", "aqi"), [(50, 50), (100, 100), (250, 200), (350, 300), (430, 400)])
def test_pm10_band_edges(conc, aqi):
    assert sub_index("pm10", conc).aqi == aqi


def test_severe_is_flagged_provisional_and_capped():
    s = sub_index("pm25", 300)
    assert s.category == "Severe" and s.provisional and 401 <= s.aqi <= 500
    assert sub_index("pm25", 999).aqi == 500


def test_overall_aqi_is_max_subindex():
    s = aqi_from(pm25=100, pm10=120)  # pm25 -> Poor (~233), pm10 -> Moderate (~113)
    assert s.pollutant == "pm25" and s.category == "Poor"


def test_rejects_bad_input():
    with pytest.raises(ValueError):
        sub_index("pm25", -1)
    with pytest.raises(ValueError):
        sub_index("no2", 10)
    with pytest.raises(ValueError):
        aqi_from()
