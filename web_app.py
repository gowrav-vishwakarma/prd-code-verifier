"""
FastAPI web application for PRD Code Verifier.
"""

import os
import json
import asyncio
from typing import List, Optional
from pathlib import Path
import aiofiles
from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from models import (
    ProjectConfig, VerificationSection, AIProviderConfig, 
    VerificationRequest, VerificationResponse, AIProvider
)
from verification_engine import VerificationEngine
from config import Config


app = FastAPI(title="PRD Code Verifier", version="0.1.0")

# Create templates directory
templates_dir = Path("templates")
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))

# Create static directory
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main application page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/providers")
async def get_ai_providers():
    """Get list of available AI providers."""
    return {"providers": [provider.value for provider in AIProvider]}


@app.get("/api/config/default-ai")
async def get_default_ai_config():
    """Get default AI configuration from environment."""
    default_config = Config.get_default_ai_config()
    return {
        "provider": default_config.provider.value,
        "model": default_config.model,
        "base_url": default_config.base_url,
        "api_key": default_config.api_key if default_config.api_key else ""
    }


@app.get("/api/config/streaming")
async def get_streaming_config():
    """Get streaming configuration."""
    return {
        "enabled": Config.ENABLE_STREAMING
    }


@app.post("/api/projects/save")
async def save_project(
    project_name: str = Form(...),
    output_folder: str = Form(...),
    documentation_root_path: str = Form(""),
    frontend_project_path: str = Form(""),
    backend_project_path: str = Form(""),
    global_system_prompt: str = Form(""),
    global_instructions: str = Form(""),
    verification_data: str = Form(...),  # JSON string of verification sections
    ai_config_data: str = Form("")  # JSON string of AI configuration
):
    """Save project configuration."""
    try:
        # Parse verification sections
        verification_sections_data = json.loads(verification_data)
        verification_sections = [
            VerificationSection(**section_data) 
            for section_data in verification_sections_data
        ]
        
        # Parse AI configuration if provided
        ai_config = None
        if ai_config_data and ai_config_data.strip():
            try:
                ai_config_data_parsed = json.loads(ai_config_data)
                ai_config = AIProviderConfig(**ai_config_data_parsed)
            except (json.JSONDecodeError, ValidationError) as e:
                # If AI config is invalid, continue without it
                print(f"Warning: Invalid AI configuration provided: {e}")
        
        # Create project config
        project_config = ProjectConfig(
            project_name=project_name,
            output_folder=output_folder,
            documentation_root_path=documentation_root_path,
            frontend_project_path=frontend_project_path,
            backend_project_path=backend_project_path,
            global_system_prompt=global_system_prompt,
            global_instructions=global_instructions,
            verification_sections=verification_sections,
            ai_config=ai_config
        )
        
        # Save to file
        filename = f"{project_name.replace(' ', '_')}.json"
        filepath = Path("projects") / filename
        filepath.parent.mkdir(exist_ok=True)
        
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(project_config.model_dump_json(indent=2))
        
        return {"message": "Project saved successfully", "filename": filename}
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving project: {str(e)}")


@app.get("/api/projects")
async def list_projects():
    """List all saved projects."""
    projects_dir = Path("projects")
    if not projects_dir.exists():
        return {"projects": []}
    
    projects = []
    for file_path in projects_dir.glob("*.json"):
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                project_data = json.loads(content)
                projects.append({
                    "filename": file_path.name,
                    "project_name": project_data.get("project_name", "Unknown"),
                    "created": file_path.stat().st_mtime
                })
        except Exception:
            continue
    
    return {"projects": projects}


@app.post("/api/projects/load")
async def load_project(file: UploadFile = File(...)):
    """Load project configuration from file."""
    try:
        content = await file.read()
        project_data = json.loads(content.decode('utf-8'))
        project_config = ProjectConfig(**project_data)
        return project_config.model_dump()
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid project file: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading project: {str(e)}")


@app.post("/api/verification/run")
async def run_verification(request: VerificationRequest):
    """Run verification process."""
    try:
        # Create verification engine
        engine = VerificationEngine(request.project_config, request.ai_config)
        
        # Run verifications
        results = await engine.run_all_verifications(request.verification_names)
        
        # Calculate summary
        total = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total - successful
        
        response = VerificationResponse(
            results=results,
            total_verifications=total,
            successful_verifications=successful,
            failed_verifications=failed
        )
        
        return response.model_dump()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running verification: {str(e)}")


@app.post("/api/verification/run-stream")
async def run_verification_stream(request: VerificationRequest):
    """Run verification process with streaming progress updates."""
    async def generate_progress():
        progress_queue = asyncio.Queue()
        
        async def progress_callback(event):
            await progress_queue.put(event)
        
        try:
            # Create verification engine with progress callback
            engine = VerificationEngine(request.project_config, request.ai_config, progress_callback)
            
            # Start verification process in background
            verification_task = asyncio.create_task(
                engine.run_all_verifications_with_progress(request.verification_names)
            )
            
            # Send initial progress
            yield f"data: {json.dumps({'type': 'start', 'message': 'Starting verification process...'})}\n\n"
            
            # Process progress events and verification
            while True:
                try:
                    # Wait for either progress event or verification completion
                    done, pending = await asyncio.wait(
                        [asyncio.create_task(progress_queue.get()), verification_task],
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # Check if verification is complete
                    if verification_task in done:
                        results = await verification_task
                        
                        # Calculate summary
                        total = len(results)
                        successful = sum(1 for r in results if r.success)
                        failed = total - successful
                        
                        # Send final results
                        final_response = VerificationResponse(
                            results=results,
                            total_verifications=total,
                            successful_verifications=successful,
                            failed_verifications=failed
                        )
                        
                        yield f"data: {json.dumps({'type': 'complete', 'results': final_response.model_dump()})}\n\n"
                        break
                    
                    # Process progress events
                    for task in done:
                        if task != verification_task:
                            event = await task
                            yield f"data: {json.dumps(event)}\n\n"
                
                except asyncio.TimeoutError:
                    continue
                    
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_progress(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@app.post("/api/ai/test-connection")
async def test_ai_connection(ai_config: AIProviderConfig):
    """Test AI provider connection and streaming capability."""
    try:
        # Use the provided AI config instead of default
        engine = VerificationEngine(ProjectConfig(project_name="test", output_folder="test"), ai_config)
        
        # Test with a simple prompt
        test_prompt = "Hello, please respond with 'Connection successful' if you can read this."
        
        try:
            response = await engine.ai_provider.generate_response(test_prompt)
            return {
                "status": "success",
                "provider": ai_config.provider.value,
                "model": ai_config.model,
                "base_url": ai_config.base_url,
                "response": response[:100] + "..." if len(response) > 100 else response,
                "streaming_supported": True  # Will be updated based on actual test
            }
        except Exception as e:
            return {
                "status": "error",
                "provider": ai_config.provider.value,
                "model": ai_config.model,
                "base_url": ai_config.base_url,
                "error": str(e),
                "streaming_supported": False
            }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Configuration error: {str(e)}"
        }


@app.get("/api/reports/{project_name}/{verification_name}/{filename}")
async def get_report(project_name: str, verification_name: str, filename: str):
    """Download a verification report from the new path structure."""
    # Security: only allow .md files
    if not filename.endswith('.md'):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    # Try to find the file in the new structure
    # Look in common output directories first
    common_output_dirs = ["./output", "/tmp/reports", "./reports"]
    
    for output_dir in common_output_dirs:
        if os.path.exists(output_dir):
            # Build the new path: output_dir/project_name/verification_name/filename
            new_path = os.path.join(output_dir, project_name, verification_name, filename)
            if os.path.exists(new_path):
                return FileResponse(new_path, media_type='text/markdown')
    
    # Fallback: search for the file in any subdirectory (for backward compatibility)
    for root, dirs, files in os.walk("."):
        if filename in files:
            # Check if this is in a project folder with the new structure
            path_parts = root.split(os.sep)
            if (len(path_parts) >= 3 and 
                path_parts[-2] == project_name and 
                path_parts[-1] == verification_name):
                file_path = os.path.join(root, filename)
                if os.path.exists(file_path):
                    return FileResponse(file_path, media_type='text/markdown')
    
    raise HTTPException(status_code=404, detail=f"Report not found: {project_name}/{verification_name}/{filename}")




@app.get("/api/reports/{project_name}/{filename}")
async def get_report_legacy(project_name: str, filename: str):
    """Legacy download endpoint for backward compatibility."""
    # Security: only allow .md files
    if not filename.endswith('.md'):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    # Try to find the file in any output folder (legacy search)
    for root, dirs, files in os.walk("."):
        if filename in files:
            # Check if this is in a project folder
            path_parts = root.split(os.sep)
            if len(path_parts) >= 2 and path_parts[-1] == project_name:
                file_path = os.path.join(root, filename)
                if os.path.exists(file_path):
                    return FileResponse(file_path, media_type='text/markdown')
    
    # Also check common output directories
    common_output_dirs = ["/tmp/reports", "./reports", "./output"]
    for output_dir in common_output_dirs:
        if os.path.exists(output_dir):
            project_dir = os.path.join(output_dir, project_name)
            if os.path.exists(project_dir):
                file_path = os.path.join(project_dir, filename)
                if os.path.exists(file_path):
                    return FileResponse(file_path, media_type='text/markdown')
    
    raise HTTPException(status_code=404, detail="Report not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
