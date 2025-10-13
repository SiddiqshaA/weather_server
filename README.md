# Weather MCP Server

This repository contains a Model Context Protocol (MCP) server that provides weather information tools.

## Repository Structure

- `weather.py`: Root entry point for FastMCP deployment
- `weather/`: Directory containing the implementation:
  - `weather.py`: Main implementation of the MCP server
  - `app.py`: Alternative implementation in a single file
  - `run_mcp.py`: Local development helper for running the MCP server

## Tools

The MCP server provides the following tools:

1. `get_weather_by_city`: Get current weather for a city
2. `get_alerts_by_type`: Get weather alerts for a US state filtered by type
3. `get_precipitation_chance`: Get precipitation forecast for a location
4. `get_air_quality`: Get air quality data for a location

## Deployment

This server is deployed at: https://back-aqua-basilisk.fastmcp.app/mcp