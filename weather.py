"""
Weather MCP Server - Root Deployment File

This file serves as the root entry point for FastMCP deployment.
It creates and exposes the MCP server object directly.
"""
import sys
import os
import traceback

try:
    sys.stderr.write("[ROOT] Initializing MCP server...\n")
    sys.stderr.write(f"[ROOT] Python version: {sys.version}\n")
    sys.stderr.write(f"[ROOT] Current directory: {os.getcwd()}\n")
    
    # Import FastMCP and create the server instance
    sys.stderr.write("[ROOT] Importing FastMCP...\n")
    from mcp.server.fastmcp import FastMCP
    
    # Create the server with the name "weather" - this is the expected variable name
    mcp = FastMCP("weather")
    
    # Import the necessary modules and register tools from the weather directory
    # Get the absolute path to the weather directory
    weather_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weather")
    sys.path.insert(0, weather_dir)
    
    # Import utility functions for tools
    from typing import Any
    import httpx
    
    # Constants
    NWS_API_BASE = "https://api.weather.gov"
    USER_AGENT = "weather-mcp/1.0"
    OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"
    AIR_QUALITY_BASE = "https://air-quality-api.open-meteo.com/v1/air-quality"
    
    # Utility function needed by tools
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

    # Define the tools directly in this file
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
Temperature: {current.get('temperature_2m', 'N/A')} C
Wind Speed: {current.get('wind_speed_10m', 'N/A')} m/s
Precipitation: {current.get('precipitation', 'N/A')} mm
"""

    @mcp.tool()
    async def get_alerts_by_type(state: str, event_type: str) -> str:
        """
        Get weather alerts of a specific type for a US state.

        Args:
            state: Two-letter US state code (e.g. CA, NY)
            event_type: Type of alert (e.g. Flood, Tornado, Snow)
        """
        url = f"{NWS_API_BASE}/alerts/active/area/{state}"
        data = await make_request(url)

        if not data or "features" not in data:
            return f"Unable to fetch alerts for {state}."

        # Filter alerts by type if specified
        features = data["features"]
        event_type_lower = event_type.lower()
        filtered = []

        for feature in features:
            props = feature["properties"]
            event = props.get("event", "")
            if event_type_lower in event.lower():
                alert = f"""
Event: {event}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')[:300]}...
"""
                filtered.append(alert)

        if not filtered:
            return f"No active {event_type} alerts for {state}."

        return "\n---\n".join(filtered)

    @mcp.tool()
    async def get_precipitation_chance(latitude: float, longitude: float) -> str:
        """
        Get precipitation forecast for a location.

        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
        """
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
        """
        Get current air quality data for a location.

        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
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
PM2.5: {aq.get('pm2_5', 'N/A')} μg/m³
PM10: {aq.get('pm10', 'N/A')} μg/m³
CO: {aq.get('carbon_monoxide', 'N/A')} μg/m³
NO₂: {aq.get('nitrogen_dioxide', 'N/A')} μg/m³
O₃: {aq.get('ozone', 'N/A')} μg/m³
"""
    
    # The mcp object is now available for the FastMCP deployment
    sys.stderr.write("[ROOT] MCP server initialized successfully with all tools registered.\n")
    
    # Define a custom run function to avoid the asyncio conflict
    def run_mcp_server():
        """Run the MCP server with special handling for asyncio conflicts"""
        import multiprocessing
        import time
        
        # Create a separate process to handle the MCP server
        def worker_process():
            try:
                sys.stderr.write("[WORKER] Starting MCP server in separate process\n")
                mcp.run(transport='stdio')
            except Exception as e:
                sys.stderr.write(f"[WORKER] Error: {str(e)}\n")
                sys.exit(1)
        
        # Start as a separate process to avoid asyncio conflicts
        p = multiprocessing.Process(target=worker_process)
        p.daemon = True  # Allow the process to be terminated when parent exits
        p.start()
        
        # Wait for the process to finish
        sys.stderr.write(f"[ROOT] MCP server process started with PID {p.pid}\n")
        p.join()
        
        if p.exitcode != 0:
            sys.stderr.write(f"[ROOT] MCP server process exited with code {p.exitcode}\n")
            sys.exit(p.exitcode)
    
    # This only runs when the file is executed directly
    if __name__ == "__main__":
        sys.stderr.write("[ROOT] Running MCP server directly...\n")
        run_mcp_server()
        
except Exception as e:
    sys.stderr.write(f"[ROOT] ERROR: {str(e)}\n")
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)