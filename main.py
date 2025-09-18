"""
Main entry point for the PRD Code Verifier application.
"""

import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Run the FastAPI application."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    print(f"Starting PRD Code Verifier on {host}:{port}")
    print(f"Debug mode: {debug}")
    print(f"Open your browser to: http://{host}:{port}")
    
    uvicorn.run(
        "web_app:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )


if __name__ == "__main__":
    main()
