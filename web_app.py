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
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from models import (
    ProjectConfig, VerificationSection, AIProviderConfig, 
    VerificationRequest, VerificationResponse, AIProvider
)
from verification_engine import VerificationEngine


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


@app.post("/api/projects/save")
async def save_project(
    project_name: str = Form(...),
    output_folder: str = Form(...),
    global_system_prompt: str = Form(""),
    global_instructions: str = Form(""),
    verification_data: str = Form(...)  # JSON string of verification sections
):
    """Save project configuration."""
    try:
        # Parse verification sections
        verification_sections_data = json.loads(verification_data)
        verification_sections = [
            VerificationSection(**section_data) 
            for section_data in verification_sections_data
        ]
        
        # Create project config
        project_config = ProjectConfig(
            project_name=project_name,
            output_folder=output_folder,
            global_system_prompt=global_system_prompt,
            global_instructions=global_instructions,
            verification_sections=verification_sections
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


@app.get("/api/reports/{filename}")
async def get_report(filename: str):
    """Download a verification report."""
    # Security: only allow .md files
    if not filename.endswith('.md'):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    # Find the report file
    for root, dirs, files in os.walk("."):
        if filename in files:
            file_path = os.path.join(root, filename)
            return FileResponse(file_path, media_type='text/markdown')
    
    raise HTTPException(status_code=404, detail="Report not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
