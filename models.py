"""
Pydantic models for the PRD Code Verifier application.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class AIProvider(str, Enum):
    """Supported AI providers."""
    OPENAI = "openai"
    GEMINI = "gemini"
    OLLAMA = "ollama"
    LM_STUDIO = "lm_studio"


class OverrideMode(str, Enum):
    """Override mode for prompts and instructions."""
    USE_GLOBAL = "use_global"
    OVERRIDE = "override"
    APPEND = "append"


class VerificationSection(BaseModel):
    """Individual verification section configuration."""
    name: str = Field(..., description="Name of the verification")
    documentation_files: List[str] = Field(default_factory=list, description="List of documentation file paths")
    frontend_code_files: List[str] = Field(default_factory=list, description="List of frontend code file paths")
    backend_code_files: List[str] = Field(default_factory=list, description="List of backend code file paths")
    system_prompt_mode: OverrideMode = Field(default=OverrideMode.USE_GLOBAL, description="How to handle system prompt (use_global, override, append)")
    instructions_mode: OverrideMode = Field(default=OverrideMode.USE_GLOBAL, description="How to handle instructions (use_global, override, append)")
    verification_system_prompt: Optional[str] = Field(None, description="Local system prompt for this verification")
    verification_instructions: Optional[str] = Field(None, description="Local instructions for this verification")
    
    # Legacy fields for backward compatibility
    override_global_system_prompt: Optional[bool] = Field(None, description="Legacy: Override global system prompt (deprecated)")
    override_global_instructions: Optional[bool] = Field(None, description="Legacy: Override global instructions (deprecated)")


class ProjectConfig(BaseModel):
    """Project configuration model."""
    project_name: str = Field(..., description="Name of the project")
    output_folder: str = Field(..., description="Output folder path for reports")
    documentation_root_path: str = Field(default="", description="Root path for documentation files")
    frontend_project_path: str = Field(default="", description="Root path for frontend code files")
    backend_project_path: str = Field(default="", description="Root path for backend code files")
    global_system_prompt: str = Field(default="", description="Global system prompt for all verifications")
    global_instructions: str = Field(default="", description="Global instructions for all verifications")
    verification_sections: List[VerificationSection] = Field(default_factory=list, description="List of verification sections")
    ai_config: Optional["AIProviderConfig"] = Field(None, description="AI provider configuration for this project")


class AIProviderConfig(BaseModel):
    """AI provider configuration."""
    provider: AIProvider = Field(..., description="AI provider to use")
    api_key: Optional[str] = Field(None, description="API key for the provider")
    base_url: Optional[str] = Field(None, description="Base URL for the provider (for custom endpoints)")
    model: str = Field(default="gpt-3.5-turbo", description="Model to use")
    tag: Optional[str] = Field(None, description="Tag for folder organization (optional)")
    temperature: float = Field(default=0.7, description="Temperature for generation")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")


class VerificationRequest(BaseModel):
    """Request model for running verification."""
    project_config: ProjectConfig
    ai_config: AIProviderConfig
    verification_names: Optional[List[str]] = Field(None, description="Specific verifications to run (None = all)")


class VerificationResult(BaseModel):
    """Result of a verification run."""
    verification_name: str
    success: bool
    report_content: Optional[str] = None
    error_message: Optional[str] = None
    report_file_path: Optional[str] = None
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    ai_tag: Optional[str] = None


class VerificationResponse(BaseModel):
    """Response model for verification results."""
    results: List[VerificationResult]
    total_verifications: int
    successful_verifications: int
    failed_verifications: int
