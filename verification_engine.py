"""
Verification engine that combines documentation and code for AI analysis.
"""

import os
import asyncio
from typing import List, Optional
from pathlib import Path
import aiofiles
from datetime import datetime
from models import ProjectConfig, VerificationSection, AIProviderConfig, VerificationResult
from ai_providers import AIProviderFactory
from config import Config


class VerificationEngine:
    """Engine for running code verification against documentation."""
    
    def __init__(self, project_config: ProjectConfig, ai_config: AIProviderConfig):
        self.project_config = project_config
        self.ai_config = ai_config
        self.ai_provider = AIProviderFactory.create_provider(ai_config)
    
    def build_full_path(self, relative_path: str, file_type: str) -> str:
        """Build full path by combining root path with relative path."""
        if not relative_path.strip():
            return ""
        
        # Determine which root path to use based on file type
        if file_type == "documentation" and self.project_config.documentation_root_path:
            root_path = self.project_config.documentation_root_path
        elif file_type == "frontend" and self.project_config.frontend_project_path:
            root_path = self.project_config.frontend_project_path
        elif file_type == "backend" and self.project_config.backend_project_path:
            root_path = self.project_config.backend_project_path
        else:
            # If no root path is set, treat as absolute path
            return relative_path
        
        # Combine root path with relative path
        return os.path.join(root_path, relative_path)
    
    async def read_file_content(self, file_path: str) -> str:
        """Read file content asynchronously."""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
        except Exception as e:
            return f"[Error reading file {file_path}: {str(e)}]"
    
    def build_verification_prompt(self, section: VerificationSection) -> str:
        """Build the complete prompt for a verification section."""
        prompt_parts = []
        
        # Add system prompt (global or local)
        if section.override_global_system_prompt and section.verification_system_prompt:
            prompt_parts.append(f"SYSTEM PROMPT:\n{section.verification_system_prompt}\n")
        elif self.project_config.global_system_prompt:
            prompt_parts.append(f"SYSTEM PROMPT:\n{self.project_config.global_system_prompt}\n")
        
        # Add documentation content
        if section.documentation_files:
            prompt_parts.append("DOCUMENTATION FILES:")
            for doc_file in section.documentation_files:
                full_path = self.build_full_path(doc_file, "documentation")
                if full_path and os.path.exists(full_path):
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        prompt_parts.append(f"\n--- {doc_file} ---\n{content}\n")
                    except Exception as e:
                        prompt_parts.append(f"\n--- {doc_file} ---\n[Error reading file: {str(e)}]\n")
                else:
                    prompt_parts.append(f"\n--- {doc_file} ---\n[File not found: {full_path}]\n")
        
        # Add frontend code
        if section.frontend_code_files:
            prompt_parts.append("\nFRONTEND CODE FILES:")
            for frontend_file in section.frontend_code_files:
                full_path = self.build_full_path(frontend_file, "frontend")
                if full_path and os.path.exists(full_path):
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        prompt_parts.append(f"\n--- {frontend_file} ---\n{content}\n")
                    except Exception as e:
                        prompt_parts.append(f"\n--- {frontend_file} ---\n[Error reading file: {str(e)}]\n")
                else:
                    prompt_parts.append(f"\n--- {frontend_file} ---\n[File not found: {full_path}]\n")
        
        # Add backend code
        if section.backend_code_files:
            prompt_parts.append("\nBACKEND CODE FILES:")
            for backend_file in section.backend_code_files:
                full_path = self.build_full_path(backend_file, "backend")
                if full_path and os.path.exists(full_path):
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        prompt_parts.append(f"\n--- {backend_file} ---\n{content}\n")
                    except Exception as e:
                        prompt_parts.append(f"\n--- {backend_file} ---\n[Error reading file: {str(e)}]\n")
                else:
                    prompt_parts.append(f"\n--- {backend_file} ---\n[File not found: {full_path}]\n")
        
        # Add instructions (global or local)
        if section.override_global_instructions and section.verification_instructions:
            prompt_parts.append(f"\nINSTRUCTIONS:\n{section.verification_instructions}")
        elif self.project_config.global_instructions:
            prompt_parts.append(f"\nINSTRUCTIONS:\n{self.project_config.global_instructions}")
        
        return "\n".join(prompt_parts)
    
    async def run_verification(self, section: VerificationSection) -> VerificationResult:
        """Run verification for a single section."""
        # Create hierarchical output directory: ProjectName/AIProvider/Model
        provider_name = self.ai_config.provider.value
        model_name = self.ai_config.model.replace("/", "_").replace(":", "_")  # Sanitize model name for filesystem
        
        project_output_dir = os.path.join(
            self.project_config.output_folder, 
            self.project_config.project_name,
            provider_name,
            model_name
        )
        os.makedirs(project_output_dir, exist_ok=True)
        
        try:
            # Build the prompt
            prompt = self.build_verification_prompt(section)
            
            # Get AI response
            response = await self.ai_provider.generate_response(prompt)
            
            # Save the report
            report_filename = f"{section.name}_report.md"
            report_path = os.path.join(project_output_dir, report_filename)
            
            # Write the report with enhanced metadata
            async with aiofiles.open(report_path, 'w', encoding='utf-8') as f:
                await f.write(f"# Verification Report: {section.name}\n\n")
                await f.write(f"**Project:** {self.project_config.project_name}\n")
                await f.write(f"**AI Provider:** {provider_name}\n")
                await f.write(f"**Model:** {self.ai_config.model}\n")
                await f.write(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}\n\n")
                await f.write("## AI Analysis\n\n")
                await f.write(response)
            
            # Save the prompt if DEBUG is enabled
            prompt_path = None
            if Config.DEBUG:
                prompt_filename = f"{section.name}_prompt.md"
                prompt_path = os.path.join(project_output_dir, prompt_filename)
                
                async with aiofiles.open(prompt_path, 'w', encoding='utf-8') as f:
                    await f.write(f"# Verification Prompt: {section.name}\n\n")
                    await f.write(f"**Project:** {self.project_config.project_name}\n")
                    await f.write(f"**AI Provider:** {provider_name}\n")
                    await f.write(f"**Model:** {self.ai_config.model}\n")
                    await f.write(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}\n\n")
                    await f.write("## Complete Prompt Sent to AI\n\n")
                    await f.write("```\n")
                    await f.write(prompt)
                    await f.write("\n```\n")
            
            return VerificationResult(
                verification_name=section.name,
                success=True,
                report_content=response,
                report_file_path=report_path,
                ai_provider=provider_name,
                ai_model=self.ai_config.model
            )
            
        except Exception as e:
            return VerificationResult(
                verification_name=section.name,
                success=False,
                error_message=str(e),
                ai_provider=self.ai_config.provider.value,
                ai_model=self.ai_config.model
            )
    
    async def run_all_verifications(self, verification_names: Optional[List[str]] = None) -> List[VerificationResult]:
        """Run verifications for specified sections or all sections."""
        sections_to_run = []
        
        if verification_names:
            # Run specific verifications
            for section in self.project_config.verification_sections:
                if section.name in verification_names:
                    sections_to_run.append(section)
        else:
            # Run all verifications
            sections_to_run = self.project_config.verification_sections
        
        # Run verifications concurrently
        tasks = [self.run_verification(section) for section in sections_to_run]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(VerificationResult(
                    verification_name=sections_to_run[i].name,
                    success=False,
                    error_message=str(result),
                    ai_provider=self.ai_config.provider.value,
                    ai_model=self.ai_config.model
                ))
            else:
                processed_results.append(result)
        
        return processed_results
