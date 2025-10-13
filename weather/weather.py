from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("weather")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-mcp/1.0"
OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_BASE = "https://air-quality-api.open-meteo.com/v1/air-quality"


# -------------------- Utility Functions --------------------

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
            print(f"[ERROR] {url} -> {e}")
            return None


# -------------------- Tools --------------------

@mcp.tool()
async def get_weather_by_city(city: str) -> str:
    """
    Get current weather for a given city using Open-Meteo API.

    Args:
        city: City name (e.g. "Chennai", "New York")
    """
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
Temperature: {current.get('temperature_2m', 'N/A')}°C
Wind Speed: {current.get('wind_speed_10m', 'N/A')} m/s
Precipitation: {current.get('precipitation', 'N/A')} mm
"""


@mcp.tool()
async def get_alerts_by_type(state: str, event_type: str) -> str:
    """
    Get weather alerts of a specific type for a US state.

    Args:
        state: Two-letter US state code (e.g. 'CA', 'TX')
        event_type: Type of event (e.g. 'Flood', 'Storm', 'Heat')
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state.upper()}"
    data = await make_request(url)

    if not data or "features" not in data:
        return f"Unable to fetch alerts for {state}."

    filtered = [
        f"""
Event: {f['properties'].get('event', 'Unknown')}
Area: {f['properties'].get('areaDesc', 'Unknown')}
Severity: {f['properties'].get('severity', 'Unknown')}
Description: {f['properties'].get('description', 'No description available')}
Instructions: {f['properties'].get('instruction', 'No specific instructions provided')}
"""
        for f in data["features"]
        if event_type.lower() in f["properties"].get("event", "").lower()
    ]

    if not filtered:
        return f"No active {event_type} alerts for {state.upper()}."

    return "\n---\n".join(filtered)


@mcp.tool()
async def get_precipitation_chance(latitude: float, longitude: float) -> str:
    """
    Get precipitation probability for the next 3 days.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "precipitation_probability_max",
        "forecast_days": 3,
        "timezone": "auto",
    }
    data = await make_request(OPEN_METEO_BASE, params)

    if not data or "daily" not in data:
        return "Unable to fetch precipitation data."

    days = data["daily"]
    response = []
    for i, date in enumerate(days["time"]):
        chance = days["precipitation_probability_max"][i]
        response.append(f"{date}: {chance}% chance of precipitation")

    return "\n".join(response)


@mcp.tool()
async def get_air_quality(latitude: float, longitude: float) -> str:
    """
    Get current air quality data for a given location.

    Args:
        latitude: Latitude
        longitude: Longitude
    """
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
PM2.5: {aq.get('pm2_5', 'N/A')} µg/m³
PM10: {aq.get('pm10', 'N/A')} µg/m³
CO: {aq.get('carbon_monoxide', 'N/A')} µg/m³
NO₂: {aq.get('nitrogen_dioxide', 'N/A')} µg/m³
O₃: {aq.get('ozone', 'N/A')} µg/m³
"""


# -------------------- Server Entry --------------------

def main():
    import sys
    print("[MCP Weather] Server starting... Listening on stdio", file=sys.stderr)
    mcp.run(transport='stdio')


if __name__ == "__main__":
    main()
