"""
Verification engine that combines documentation and code for AI analysis.
"""

import os
import asyncio
from typing import List, Optional, Callable, Dict, Any
from pathlib import Path
import aiofiles
from datetime import datetime
from models import ProjectConfig, VerificationSection, AIProviderConfig, VerificationResult, OverrideMode
from ai_providers import AIProviderFactory
from config import Config
from utils.env_substitution import EnvSubstitution


class VerificationEngine:
    """Engine for running code verification against documentation."""
    
    def __init__(self, project_config: ProjectConfig, ai_config: AIProviderConfig, progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None, cr_mode: bool = False):
        # Apply environment substitution to project config before using it
        self.project_config = self._substitute_project_config(project_config)
        
        # Apply environment substitution to AI config before using it
        self.ai_config = self._substitute_ai_config(ai_config)
        self.ai_provider = AIProviderFactory.create_provider(self.ai_config)
        self.progress_callback = progress_callback
        self.cr_mode = cr_mode
        
        # Pass progress callback to AI provider
        self.ai_provider.progress_callback = progress_callback
    
    def _substitute_project_config(self, project_config: ProjectConfig) -> ProjectConfig:
        """Apply environment variable substitution to project config."""
        # Convert to dict, substitute, then recreate the object
        config_dict = project_config.model_dump()
        substituted_dict = EnvSubstitution.substitute(config_dict)
        
        # Create new ProjectConfig with substituted values
        return ProjectConfig(**substituted_dict)
    
    def _substitute_ai_config(self, ai_config: AIProviderConfig) -> AIProviderConfig:
        """Apply environment variable substitution to AI config."""
        # Convert to dict, substitute, then recreate the object
        config_dict = ai_config.model_dump()
        substituted_dict = EnvSubstitution.substitute(config_dict)
        
        # Create new AIProviderConfig with substituted values
        return AIProviderConfig(**substituted_dict)
    
    async def _emit_progress(self, event_type: str, message: str, data: Optional[Dict[str, Any]] = None):
        """Emit progress event if callback is available."""
        if self.progress_callback:
            event = {
                "type": event_type,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
            if data:
                event.update(data)
            await self.progress_callback(event)
    
    def build_full_path(self, relative_path: str, file_type: str) -> str:
        """Build full path by combining root path with relative path."""
        if not relative_path.strip():
            return ""
        
        # Always substitute environment variables in paths
        relative_path = EnvSubstitution.substitute(relative_path)
        
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
        
        # Always substitute environment variables in root path too
        root_path = EnvSubstitution.substitute(root_path)
        
        # Combine root path with relative path
        return os.path.join(root_path, relative_path)
    
    async def read_file_content(self, file_path: str) -> str:
        """Read file content asynchronously."""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
        except Exception as e:
            return f"[Error reading file {file_path}: {str(e)}]"
    
    def get_files_in_path(self, path: str) -> List[str]:
        """Get all files in a path, handling both files and directories."""
        if not path or not os.path.exists(path):
            return []
        
        if os.path.isfile(path):
            return [path]
        elif os.path.isdir(path):
            files = []
            for root, dirs, filenames in os.walk(path):
                for filename in filenames:
                    # Skip hidden files and common non-code files
                    if not filename.startswith('.') and not filename.endswith(('.pyc', '.pyo', '__pycache__')):
                        files.append(os.path.join(root, filename))
            return files
        else:
            return []
    
    def build_verification_prompt(self, section: VerificationSection) -> str:
        """Build the complete prompt for a verification section."""
        prompt_parts = []
        
        # Handle system prompt based on mode
        system_prompt = self._build_system_prompt(section)
        if system_prompt:
            prompt_parts.append(f"SYSTEM PROMPT:\n{system_prompt}\n")
        
        # Add documentation content
        if section.documentation_files:
            prompt_parts.append("DOCUMENTATION FILES:")
            for doc_file in section.documentation_files:
                full_path = self.build_full_path(doc_file, "documentation")
                if full_path:
                    files_to_read = self.get_files_in_path(full_path)
                    if files_to_read:
                        for file_path in files_to_read:
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                # Get relative path for display
                                rel_path = os.path.relpath(file_path, self.project_config.documentation_root_path or "")
                                prompt_parts.append(f"\n--- {rel_path} ---\n{content}\n")
                            except Exception as e:
                                prompt_parts.append(f"\n--- {file_path} ---\n[Error reading file: {str(e)}]\n")
                    else:
                        prompt_parts.append(f"\n--- {doc_file} ---\n[No files found in: {full_path}]\n")
                else:
                    prompt_parts.append(f"\n--- {doc_file} ---\n[Path not found: {doc_file}]\n")
        
        # Add frontend code
        if section.frontend_code_files:
            prompt_parts.append("\nFRONTEND CODE FILES:")
            for frontend_file in section.frontend_code_files:
                full_path = self.build_full_path(frontend_file, "frontend")
                if full_path:
                    files_to_read = self.get_files_in_path(full_path)
                    if files_to_read:
                        for file_path in files_to_read:
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                # Get relative path for display
                                rel_path = os.path.relpath(file_path, self.project_config.frontend_project_path or "")
                                prompt_parts.append(f"\n--- {rel_path} ---\n{content}\n")
                            except Exception as e:
                                prompt_parts.append(f"\n--- {file_path} ---\n[Error reading file: {str(e)}]\n")
                    else:
                        prompt_parts.append(f"\n--- {frontend_file} ---\n[No files found in: {full_path}]\n")
                else:
                    prompt_parts.append(f"\n--- {frontend_file} ---\n[Path not found: {frontend_file}]\n")
        
        # Add backend code
        if section.backend_code_files:
            prompt_parts.append("\nBACKEND CODE FILES:")
            for backend_file in section.backend_code_files:
                full_path = self.build_full_path(backend_file, "backend")
                if full_path:
                    files_to_read = self.get_files_in_path(full_path)
                    if files_to_read:
                        for file_path in files_to_read:
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                # Get relative path for display
                                rel_path = os.path.relpath(file_path, self.project_config.backend_project_path or "")
                                prompt_parts.append(f"\n--- {rel_path} ---\n{content}\n")
                            except Exception as e:
                                prompt_parts.append(f"\n--- {file_path} ---\n[Error reading file: {str(e)}]\n")
                    else:
                        prompt_parts.append(f"\n--- {backend_file} ---\n[No files found in: {full_path}]\n")
                else:
                    prompt_parts.append(f"\n--- {backend_file} ---\n[Path not found: {backend_file}]\n")
        
        # Handle instructions based on mode
        instructions = self._build_instructions(section)
        if instructions:
            prompt_parts.append(f"\nINSTRUCTIONS:\n{instructions}")
        
        return "\n".join(prompt_parts)
    
    def _build_system_prompt(self, section: VerificationSection) -> str:
        """Build system prompt based on the override mode."""
        # Handle legacy boolean fields for backward compatibility
        if section.override_global_system_prompt is not None:
            # Legacy mode - convert to new enum
            if section.override_global_system_prompt:
                section.system_prompt_mode = OverrideMode.OVERRIDE
            else:
                section.system_prompt_mode = OverrideMode.USE_GLOBAL
        
        if section.system_prompt_mode == OverrideMode.USE_GLOBAL:
            return self.project_config.global_system_prompt
        elif section.system_prompt_mode == OverrideMode.OVERRIDE:
            return section.verification_system_prompt or ""
        elif section.system_prompt_mode == OverrideMode.APPEND:
            global_prompt = self.project_config.global_system_prompt
            local_prompt = section.verification_system_prompt or ""
            if global_prompt and local_prompt:
                return f"{global_prompt}\n\n{local_prompt}"
            elif global_prompt:
                return global_prompt
            else:
                return local_prompt
        return ""
    
    def _build_instructions(self, section: VerificationSection) -> str:
        """Build instructions based on the override mode."""
        # Handle legacy boolean fields for backward compatibility
        if section.override_global_instructions is not None:
            # Legacy mode - convert to new enum
            if section.override_global_instructions:
                section.instructions_mode = OverrideMode.OVERRIDE
            else:
                section.instructions_mode = OverrideMode.USE_GLOBAL
        
        if section.instructions_mode == OverrideMode.USE_GLOBAL:
            return self.project_config.global_instructions
        elif section.instructions_mode == OverrideMode.OVERRIDE:
            return section.verification_instructions or ""
        elif section.instructions_mode == OverrideMode.APPEND:
            global_instructions = self.project_config.global_instructions
            local_instructions = section.verification_instructions or ""
            if global_instructions and local_instructions:
                return f"{global_instructions}\n\n{local_instructions}"
            elif global_instructions:
                return global_instructions
            else:
                return local_instructions
        return ""
    
    async def run_verification(self, section: VerificationSection) -> VerificationResult:
        """Run verification for a single section."""
        # Create hierarchical output directory: ProjectName/VerificationName/Provider_Model_Tag
        provider_name = self.ai_config.provider.value
        model_name = self.ai_config.model.replace("/", "_").replace(":", "_")  # Sanitize model name for filesystem
        tag = self.ai_config.tag.strip() if self.ai_config.tag else None
        
        print(f"🔍 [VERIFICATION] Starting verification: {section.name}")
        print(f"🔍 [VERIFICATION] AI Provider: {provider_name}")
        print(f"🔍 [VERIFICATION] AI Model: {self.ai_config.model}")
        print(f"🔍 [VERIFICATION] AI Base URL: {self.ai_config.base_url}")
        print(f"🔍 [VERIFICATION] AI API Key: {'***' if self.ai_config.api_key else 'None'}")
        print(f"🔍 [VERIFICATION] Processing {len(section.documentation_files)} documentation files...")
        print(f"🔍 [VERIFICATION] Processing {len(section.frontend_code_files)} frontend files...")
        print(f"🔍 [VERIFICATION] Processing {len(section.backend_code_files)} backend files...")
        import sys
        sys.stdout.flush()
        
        # Build path components - new structure: output_folder/project_name/verification_name/
        path_components = [
            self.project_config.output_folder, 
            self.project_config.project_name,
            section.name  # verification name as folder
        ]
        
        project_output_dir = os.path.join(*path_components)
        os.makedirs(project_output_dir, exist_ok=True)
        print(f"🔍 [VERIFICATION] Output directory: {project_output_dir}")
        
        try:
            # Emit progress: Starting verification
            await self._emit_progress("verification_start", f"Starting verification: {section.name}", {
                "verification_name": section.name
            })
            
            # Build the prompt
            await self._emit_progress("prompt_building", f"Building prompt for: {section.name}")
            print(f"🔍 [VERIFICATION] Building verification prompt...")
            prompt = self.build_verification_prompt(section)
            print(f"🔍 [VERIFICATION] Prompt built successfully ({len(prompt)} characters)")
            
            # Get AI response
            await self._emit_progress("ai_processing", f"Processing with AI: {section.name}")
            print(f"🔍 [VERIFICATION] Calling AI provider...")
            print(f"🔍 [VERIFICATION] This may take 30-60 seconds depending on AI provider...")
            response = await self.ai_provider.generate_response_with_progress(prompt, section.name)
            print(f"🔍 [VERIFICATION] AI response received ({len(response) if response else 0} characters)")
            
            # Save the report
            await self._emit_progress("saving_report", f"Saving report for: {section.name}")
            # Create filename with provider, model, and tag: provider_model_tag_report.md
            filename_parts = [provider_name, model_name]
            if tag:
                filename_parts.append(tag)
            filename_parts.append("report")
            report_filename = "_".join(filename_parts) + ".md"
            report_path = os.path.join(project_output_dir, report_filename)
            
            print(f"🔍 [VERIFICATION] Report filename: {report_filename}")
            print(f"🔍 [VERIFICATION] Report path: {report_path}")
            print(f"🔍 [VERIFICATION] Response content preview: {response[:200] if response else 'None'}...")
            
            # Write the report with enhanced metadata
            async with aiofiles.open(report_path, 'w', encoding='utf-8') as f:
                await f.write(f"# Verification Report: {section.name}\n\n")
                await f.write(f"**Project:** {self.project_config.project_name}\n")
                await f.write(f"**AI Provider:** {provider_name}\n")
                await f.write(f"**Model:** {self.ai_config.model}\n")
                if tag:
                    await f.write(f"**Tag:** {tag}\n")
                await f.write(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}\n\n")
                
                # Add files used in verification
                await f.write("## Files Used in Verification\n\n")
                
                # Documentation files
                if section.documentation_files:
                    await f.write("### Documentation Files\n")
                    for doc_file in section.documentation_files:
                        await f.write(f"- `{doc_file}`\n")
                    await f.write("\n")
                
                # Frontend code files
                if section.frontend_code_files:
                    await f.write("### Frontend Code Files\n")
                    for frontend_file in section.frontend_code_files:
                        await f.write(f"- `{frontend_file}`\n")
                    await f.write("\n")
                
                # Backend code files
                if section.backend_code_files:
                    await f.write("### Backend Code Files\n")
                    for backend_file in section.backend_code_files:
                        await f.write(f"- `{backend_file}`\n")
                    await f.write("\n")
                
                await f.write("## AI Analysis\n\n")
                await f.write(response)
            
            # Save the prompt if DEBUG is enabled
            prompt_path = None
            if Config.DEBUG:
                # Create prompt filename with provider, model, and tag: provider_model_tag_prompt.md
                prompt_filename_parts = [provider_name, model_name]
                if tag:
                    prompt_filename_parts.append(tag)
                prompt_filename_parts.append("prompt")
                prompt_filename = "_".join(prompt_filename_parts) + ".md"
                prompt_path = os.path.join(project_output_dir, prompt_filename)
                
                async with aiofiles.open(prompt_path, 'w', encoding='utf-8') as f:
                    await f.write(f"# Verification Prompt: {section.name}\n\n")
                    await f.write(f"**Project:** {self.project_config.project_name}\n")
                    await f.write(f"**AI Provider:** {provider_name}\n")
                    await f.write(f"**Model:** {self.ai_config.model}\n")
                    if tag:
                        await f.write(f"**Tag:** {tag}\n")
                    await f.write(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}\n\n")
                    
                    # Add files used in verification
                    await f.write("## Files Used in Verification\n\n")
                    
                    # Documentation files
                    if section.documentation_files:
                        await f.write("### Documentation Files\n")
                        for doc_file in section.documentation_files:
                            await f.write(f"- `{doc_file}`\n")
                        await f.write("\n")
                    
                    # Frontend code files
                    if section.frontend_code_files:
                        await f.write("### Frontend Code Files\n")
                        for frontend_file in section.frontend_code_files:
                            await f.write(f"- `{frontend_file}`\n")
                        await f.write("\n")
                    
                    # Backend code files
                    if section.backend_code_files:
                        await f.write("### Backend Code Files\n")
                        for backend_file in section.backend_code_files:
                            await f.write(f"- `{backend_file}`\n")
                        await f.write("\n")
                    
                    await f.write("## Complete Prompt Sent to AI\n\n")
                    await f.write("```\n")
                    await f.write(prompt)
                    await f.write("\n```\n")
            
            # Emit completion event
            await self._emit_progress("verification_complete", f"Completed verification: {section.name}", {
                "verification_name": section.name,
                "success": True
            })
            
            return VerificationResult(
                verification_name=section.name,
                success=True,
                report_content=response,
                report_file_path=report_path,
                ai_provider=provider_name,
                ai_model=model_name,  # Use sanitized model name for consistency
                ai_tag=tag
            )
            
        except Exception as e:
            # Emit error event
            await self._emit_progress("verification_error", f"Error in verification: {section.name}", {
                "verification_name": section.name,
                "error": str(e),
                "success": False
            })
            
            return VerificationResult(
                verification_name=section.name,
                success=False,
                error_message=str(e),
                ai_provider=provider_name,
                ai_model=model_name,
                ai_tag=tag
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
                # Get sanitized names for consistency
                provider_name = self.ai_config.provider.value
                model_name = self.ai_config.model.replace("/", "_").replace(":", "_")
                
                processed_results.append(VerificationResult(
                    verification_name=sections_to_run[i].name,
                    success=False,
                    error_message=str(result),
                    ai_provider=provider_name,
                    ai_model=model_name
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def run_all_verifications_with_progress(self, verification_names: Optional[List[str]] = None, progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> List[VerificationResult]:
        """Run verifications for specified sections or all sections with progress updates."""
        # Update progress callback if provided
        if progress_callback:
            self.progress_callback = progress_callback
        
        sections_to_run = []
        
        if verification_names:
            # Run specific verifications
            for section in self.project_config.verification_sections:
                if section.name in verification_names:
                    sections_to_run.append(section)
        else:
            # Run all verifications
            sections_to_run = self.project_config.verification_sections
        
        # Emit initial progress
        await self._emit_progress("batch_start", f"Starting batch verification of {len(sections_to_run)} sections", {
            "total_sections": len(sections_to_run),
            "section_names": [s.name for s in sections_to_run]
        })
        
        # Run verifications with progress tracking
        results = []
        for i, section in enumerate(sections_to_run):
            print(f"🔍 [VERIFICATION_ENGINE] Processing section {i+1}/{len(sections_to_run)}: {section.name}")
            print(f"🔍 [VERIFICATION_ENGINE] Progress: {i+1}/{len(sections_to_run)} verifications")
            
            # Emit progress for current section
            await self._emit_progress("section_progress", f"Processing section {i+1}/{len(sections_to_run)}: {section.name}", {
                "current_section": i + 1,
                "total_sections": len(sections_to_run),
                "section_name": section.name
            })
            
            # Run the verification
            print(f"🔍 [VERIFICATION_ENGINE] Calling run_verification for: {section.name}")
            try:
                result = await self.run_verification(section)
                print(f"🔍 [VERIFICATION_ENGINE] Verification result: success={result.success}, error={result.error_message}")
                results.append(result)
            except Exception as e:
                print(f"🔍 [VERIFICATION_ENGINE] Exception in run_verification: {str(e)}")
                import traceback
                print(f"🔍 [VERIFICATION_ENGINE] Full traceback: {traceback.format_exc()}")
                # Create a failed result
                from models import VerificationResult
                result = VerificationResult(
                    verification_name=section.name,
                    success=False,
                    error_message=str(e),
                    ai_provider=self.ai_config.provider.value,
                    ai_model=self.ai_config.model
                )
                results.append(result)
        
        # Emit batch completion
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        await self._emit_progress("batch_complete", f"Batch verification completed: {successful} successful, {failed} failed", {
            "total_sections": len(results),
            "successful": successful,
            "failed": failed
        })
        
        return results
