"""
Weather MCP Server - Root Deployment File

This file serves as the root entry point for FastMCP deployment.
It imports and runs the actual implementation from the weather directory.
"""
import sys
import os
import traceback

try:
    # Get the absolute path to the weather directory
    weather_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weather")
    sys.path.insert(0, weather_dir)
    
    # Import the main function from the weather implementation
    from weather import main
    
    # Run the server
    if __name__ == "__main__":
        main()
except Exception as e:
    sys.stderr.write(f"[ROOT] ERROR: {str(e)}\n")
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)