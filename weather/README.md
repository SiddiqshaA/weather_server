Weather CLI and MCP Server
==========================

This project provides:

- A simple CLI to fetch National Weather Service (NWS) alerts and forecasts
- An MCP server exposing the same tools for MCP-compatible hosts

Requirements
------------
- Python 3.13+
- uv (recommended) to run/build

Install (editable) and Run
--------------------------

Using uv:

```powershell
# From the repository root
uv sync

# Show CLI help
uv run weather --help

# Alerts for a state
uv run weather alerts CA

# Forecast for a location
uv run weather forecast 37.7749 -122.4194

# Start MCP server over stdio (for MCP hosts)
uv run weather serve
```

Alternatively, run directly without installing:

```powershell
uv run python -m weather.weather --help
uv run python -m weather.weather alerts CA
uv run python -m weather.weather forecast 37.7749 -122.4194
```

Notes
-----
- The NWS API requires a User-Agent. This project sets a default one.
- Forecasts show the next 5 periods from the NWS gridpoint forecast.
