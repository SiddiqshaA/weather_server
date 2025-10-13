"""
MCP Runner - A standalone script to run the Weather MCP server

This script directly imports and runs the weather tools from the weather.py file,
but in a separate process to avoid asyncio conflicts.
"""
import sys
import os
import importlib.util
import subprocess

def main():
    """Start the MCP server in a completely separate process"""
    print("[Weather MCP] Starting server in a separate process...")
    
    # Get the path to the original weather.py file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create a simple script that will launch a clean MCP server
    runner_content = """
import sys
import os
import importlib

try:
    # Import the FastMCP library
    from mcp.server.fastmcp import FastMCP
    
    # Create a fresh FastMCP instance
    mcp = FastMCP("weather")
    
    # Import the weather module from the workspace
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Import all tools from the weather module
    from weather import get_weather_by_city, get_alerts_by_type, get_precipitation_chance, get_air_quality
    
    # Register all tools with this MCP instance
    mcp.add_tool(get_weather_by_city)
    mcp.add_tool(get_alerts_by_type)
    mcp.add_tool(get_precipitation_chance)
    mcp.add_tool(get_air_quality)
    
    # Run the MCP server
    print("[Weather MCP] Server started successfully", file=sys.stderr)
    mcp.run(transport='stdio')
    
except Exception as e:
    print(f"[ERROR] Failed to start MCP server: {e}", file=sys.stderr)
    sys.exit(1)
"""
    
    # Create a temporary runner script
    temp_script = os.path.join(script_dir, "_temp_runner.py")
    
    try:
        # Write the runner script
        with open(temp_script, "w") as f:
            f.write(runner_content)
        
        # Start the runner in a separate process
        python_exec = sys.executable
        
        print(f"[Runner] Starting MCP server with Python: {python_exec}")
        result = subprocess.run([python_exec, temp_script], check=True)
        
        return result.returncode
        
    except Exception as e:
        print(f"[Runner ERROR] {e}", file=sys.stderr)
        return 1
        
    finally:
        # Clean up
        try:
            if os.path.exists(temp_script):
                os.remove(temp_script)
        except:
            pass

if __name__ == "__main__":
    sys.exit(main())