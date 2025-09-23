"""
Main entry point for the PRD Code Verifier application.
Supports both local web mode and CR (Continuous Review) mode.
"""

import uvicorn
import os
import sys
import asyncio
import argparse
from dotenv import load_dotenv
from cr_config import CRConfig, CRMode
from cr_runner import CRRunner

# Load environment variables
load_dotenv()

def main():
    """Main entry point with support for both web and CR modes."""
    parser = argparse.ArgumentParser(description="PRD Code Verifier")
    parser.add_argument("--mode", choices=["web", "cr"], default="web", 
                       help="Run mode: 'web' for local web interface, 'cr' for Continuous Review")
    parser.add_argument("--cr-config", help="Path to CR configuration file")
    parser.add_argument("--project-file", help="Path to project JSON file")
    parser.add_argument("--output-folder", help="Output folder for results")
    parser.add_argument("--run-all", action="store_true", help="Run all verifications (CR mode)")
    parser.add_argument("--verifications", help="Comma-separated list of verification names to run (CR mode)")
    
    args = parser.parse_args()
    
    if args.mode == "web":
        run_web_mode()
    elif args.mode == "cr":
        run_cr_mode(args)

def run_web_mode():
    """Run the web application mode."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    print(f"🌐 Starting PRD Code Verifier Web Mode on {host}:{port}")
    print(f"Debug mode: {debug}")
    print(f"Open your browser to: http://{host}:{port}")
    
    uvicorn.run(
        "web_app:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )

def run_cr_mode(args):
    """Run the Continuous Review mode."""
    print("🚀 Starting PRD Code Verifier CR Mode")
    
    # Create CR configuration
    config = CRConfig.from_env()
    
    # Override with command line arguments
    if args.project_file:
        config.project_file = args.project_file
    if args.output_folder:
        config.output_folder = args.output_folder
    if args.run_all:
        config.run_all_verifications = True
    if args.verifications:
        config.specific_verifications = args.verifications.split(',')
    
    # Substitute environment variables
    config = config.substitute_env_vars()
    
    # Run CR process
    async def run_cr():
        runner = CRRunner(config)
        result = await runner.run()
        
        if result["status"] == "success":
            print(f"\n🎉 CR Summary:")
            print(f"  - Affected verifications: {len(result['affected_verifications'])}")
            print(f"  - Results: {len(result['results'])}")
            sys.exit(0)
        else:
            print(f"\n💥 CR Failed: {result['error']}")
            sys.exit(1)
    
    asyncio.run(run_cr())


if __name__ == "__main__":
    main()
