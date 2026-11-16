"""Aagahi command-line interface. Every pipeline step is a plain CLI command (D-020: orchestrator-agnostic).

Steps not yet built print which build phase adds them (ROADMAP.md).
"""

from __future__ import annotations

import typer

from aagahi import __version__
from aagahi.aqi import aqi_from
from aagahi.config import load_city

app = typer.Typer(help="Aagahi: explainable air-quality forecasting for Delhi-NCR.", no_args_is_help=True)


@app.command()
def version() -> None:
    """Print the package version."""
    typer.echo(__version__)


@app.command("check-config")
def check_config(city: str = "delhi-ncr") -> None:
    """Load and validate a city config (pinned model, sensors, unique stations)."""
    cfg = load_city(city)
    agencies: dict[str, int] = {}
    for s in cfg.stations:
        agencies[s.agency] = agencies.get(s.agency, 0) + 1
    typer.echo(
        f"{cfg.city}: {len(cfg.stations)} stations {agencies}; weather={cfg.weather_model}; "
        f"horizon={cfg.horizon_hours} h; delays={cfg.delay_minutes}"
    )


@app.command()
def aqi(pm25: float = typer.Option(None), pm10: float = typer.Option(None)) -> None:
    """PM-based Indian AQI from 24-h average concentrations (µg/m³)."""
    s = aqi_from(pm25=pm25, pm10=pm10)
    note = "  (Severe band upper breakpoint provisional: verify in B1)" if s.provisional else ""
    typer.echo(f"AQI {s.aqi} · {s.category} · driven by {s.pollutant}{note}")


def _planned(step: str, phase: str) -> None:
    typer.echo(f"`{step}` arrives in build phase {phase} (see docs/ROADMAP.md).")
    raise typer.Exit(code=2)


@app.command()
def ingest() -> None:
    """Fetch observations, weather, CAMS and fires (B2)."""
    _planned("ingest", "B2")


@app.command()
def forecast() -> None:
    """Run the champion model for all stations (B2 baseline, B3 model)."""
    _planned("forecast", "B2/B3")


@app.command()
def publish() -> None:
    """Write latest/*.json + status.json to the live repo (B2)."""
    _planned("publish", "B2")


if __name__ == "__main__":
    app()
