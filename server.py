"""
Simple Weather MCP Server - Root Entry Point

This file provides a clean and simple implementation for deployment.
"""
from mcp.server.fastmcp import FastMCP
import httpx
from typing import Any
import sys

# Create the MCP server
mcp = FastMCP("weather")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-mcp/1.0"
OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_BASE = "https://air-quality-api.open-meteo.com/v1/air-quality"

# Print diagnostic info
print("Weather MCP Server initializing...", file=sys.stderr)

# Utility function
async def make_request(url: str, params: dict | None = None) -> dict[str, Any] | None:
    """Generic async HTTP GET request with error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[ERROR] {url} -> {e}", file=sys.stderr)
            return None

# Tool definitions
@mcp.tool()
async def get_weather_by_city(city: str) -> str:
    """Get current weather for a given city using Open-Meteo API."""
    geocode_url = f"https://geocoding-api.open-meteo.com/v1/search"
    geo_data = await make_request(geocode_url, {"name": city, "count": 1})

    if not geo_data or "results" not in geo_data or not geo_data["results"]:
        return f"Unable to find location for '{city}'."

    lat = geo_data["results"][0]["latitude"]
    lon = geo_data["results"][0]["longitude"]

    weather_data = await make_request(
        OPEN_METEO_BASE,
        {"latitude": lat, "longitude": lon, "current": ["temperature_2m", "wind_speed_10m", "precipitation"]}
    )

    if not weather_data or "current" not in weather_data:
        return f"Unable to fetch current weather for {city}."

    current = weather_data["current"]
    return f"""
Current Weather in {city.title()}:
Temperature: {current.get('temperature_2m', 'N/A')} C
Wind Speed: {current.get('wind_speed_10m', 'N/A')} m/s
Precipitation: {current.get('precipitation', 'N/A')} mm
"""

@mcp.tool()
async def get_precipitation_chance(latitude: float, longitude: float) -> str:
    """Get precipitation forecast for a location."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": ["precipitation_probability_max"],
        "forecast_days": 7
    }
    data = await make_request(OPEN_METEO_BASE, params)

    if not data or "daily" not in data:
        return "Unable to fetch precipitation forecast."

    daily = data["daily"]
    response = ["Precipitation Forecast:"]

    for i, day in enumerate(daily.get("time", [])):
        prob = daily.get("precipitation_probability_max", [])[i]
        response.append(f"{day}: {prob}% chance of precipitation")

    return "\n".join(response)

@mcp.tool()
async def get_air_quality(latitude: float, longitude: float) -> str:
    """Get current air quality data for a location."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ["pm10", "pm2_5", "carbon_monoxide", "nitrogen_dioxide", "ozone"],
    }
    data = await make_request(AIR_QUALITY_BASE, params)

    if not data or "current" not in data:
        return "Unable to fetch air quality data."

    aq = data["current"]
    return f"""
Air Quality Data:
PM2.5: {aq.get('pm2_5', 'N/A')} μg/m³
PM10: {aq.get('pm10', 'N/A')} μg/m³
CO: {aq.get('carbon_monoxide', 'N/A')} μg/m³
NO₂: {aq.get('nitrogen_dioxide', 'N/A')} μg/m³
O₃: {aq.get('ozone', 'N/A')} μg/m³
"""

# Print ready message
print("Weather MCP Server ready with tools:", file=sys.stderr)
for tool in mcp._tools:
    print(f"- {tool.name}", file=sys.stderr)

# When executed directly, run the server
if __name__ == "__main__":
    print("Starting Weather MCP Server...", file=sys.stderr)
    mcp.run(transport='stdio')