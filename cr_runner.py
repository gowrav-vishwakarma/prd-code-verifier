"""
CR (Continuous Review) runner.
Main entry point for CR mode execution.
"""

import os
import json
import asyncio
import argparse
from pathlib import Path
from typing import List, Optional, Dict, Any
import aiofiles

from cr_config import CRConfig, CRMode
from utils.env_substitution import EnvSubstitution
from utils.git_operations import GitOperations, FileChangeDetector
from models import ProjectConfig, VerificationSection, AIProviderConfig
from verification_engine import VerificationEngine


class CRRunner:
    """Main runner for CR mode."""
    
    def __init__(self, config: CRConfig):
        """Initialize CR runner."""
        self.config = config
        self.git_ops = GitOperations()
        self.project_config: Optional[ProjectConfig] = None
        self.ai_config: Optional[AIProviderConfig] = None
        
    async def run(self) -> Dict[str, Any]:
        """Run the CR process."""
        try:
            print(f"🚀 Starting CR mode: {self.config.mode.value}")
            
            # Step 1: Load and process project configuration
            await self._load_project_config()
            
            # Step 2: Clone repositories if needed
            await self._clone_repositories()
            
            # Step 3: Detect changed files and affected verifications
            affected_verifications = await self._detect_affected_verifications()
            
            # Step 4: Run verifications
            results = await self._run_verifications(affected_verifications)
            
            # Step 5: Publish results if configured
            if self.config.publish_results:
                await self._publish_results(results)
            
            print("✅ CR process completed successfully")
            return {
                "status": "success",
                "affected_verifications": affected_verifications,
                "results": results
            }
            
        except Exception as e:
            print(f"❌ CR process failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            # Cleanup
            self.git_ops.cleanup()
    
    async def _load_project_config(self):
        """Load and process project configuration."""
        print("📋 Loading project configuration...")
        
        # Load project file
        project_file_path = self.config.project_file
        if not os.path.exists(project_file_path):
            raise FileNotFoundError(f"Project file not found: {project_file_path}")
        
        async with aiofiles.open(project_file_path, 'r', encoding='utf-8') as f:
            project_data = await f.read()
        
        # Parse JSON
        project_dict = json.loads(project_data)
        
        # Substitute environment variables
        project_dict = EnvSubstitution.substitute_config(project_dict)
        
        # Create ProjectConfig
        self.project_config = ProjectConfig(**project_dict)
        
        # Extract AI config
        if self.project_config.ai_config:
            self.ai_config = self.project_config.ai_config
            print(f"🔍 [CR_RUNNER] Using AI config from project file")
        else:
            # Create AI config from CR configuration
            from models import AIProviderConfig, AIProvider
            self.ai_config = AIProviderConfig(
                provider=AIProvider(self.config.ai_provider),
                model=self.config.ai_model,
                base_url=self.config.ai_base_url,
                api_key=self._get_ai_api_key()
            )
            print(f"🔍 [CR_RUNNER] Created AI config from CR configuration")
        
        print(f"🔍 [CR_RUNNER] AI Provider: {self.ai_config.provider}")
        print(f"🔍 [CR_RUNNER] AI Model: {self.ai_config.model}")
        print(f"🔍 [CR_RUNNER] AI Base URL: {self.ai_config.base_url}")
        print(f"🔍 [CR_RUNNER] AI API Key: {'***' if self.ai_config.api_key else 'None'}")
        
        print(f"✅ Project loaded: {self.project_config.project_name}")
    
    def _get_ai_api_key(self) -> str:
        """Get AI API key based on provider."""
        if self.config.ai_provider == "openai":
            return os.getenv("OPENAI_API_KEY", "")
        elif self.config.ai_provider == "gemini":
            return os.getenv("GEMINI_API_KEY", "")
        elif self.config.ai_provider == "ollama":
            return ""  # Ollama doesn't require API key
        elif self.config.ai_provider == "lm_studio":
            return ""  # LM Studio doesn't require API key
        else:
            return ""
    
    async def _clone_repositories(self):
        """Clone repositories if in CR mode."""
        if self.config.mode == CRMode.LOCAL:
            print("🏠 Local mode - skipping repository cloning")
            return
        
        print("📥 Cloning repositories...")
        
        repos_to_clone = []
        if self.config.documentation_repo:
            repos_to_clone.append(self.config.documentation_repo)
        if self.config.frontend_repo:
            repos_to_clone.append(self.config.frontend_repo)
        if self.config.backend_repo:
            repos_to_clone.append(self.config.backend_repo)
        
        for repo_config in repos_to_clone:
            print(f"  Cloning {repo_config.name} from {repo_config.url}")
            clone_path = self.git_ops.clone_repository(repo_config.url, repo_config.branch)
            repo_config.clone_path = clone_path
            print(f"  ✅ Cloned to: {clone_path}")
    
    async def _detect_affected_verifications(self) -> List[str]:
        """Detect which verifications are affected by file changes."""
        if self.config.run_all_verifications:
            print("🔄 Running all verifications (configured)")
            return [section.name for section in self.project_config.verification_sections]
        
        if self.config.specific_verifications:
            print(f"🎯 Running specific verifications: {self.config.specific_verifications}")
            return self.config.specific_verifications
        
        print("🔍 Detecting affected verifications from file changes...")
        
        # Get changed files from each repository
        all_changed_files = []
        
        if self.config.documentation_repo and self.config.documentation_repo.clone_path:
            changed_files = self.git_ops.get_changed_files(
                self.config.documentation_repo.clone_path,
                self.config.base_commit,
                self.config.target_commit
            )
            all_changed_files.extend(changed_files)
            print(f"  Documentation changes: {len(changed_files)} files")
        
        if self.config.frontend_repo and self.config.frontend_repo.clone_path:
            changed_files = self.git_ops.get_changed_files(
                self.config.frontend_repo.clone_path,
                self.config.base_commit,
                self.config.target_commit
            )
            all_changed_files.extend(changed_files)
            print(f"  Frontend changes: {len(changed_files)} files")
        
        if self.config.backend_repo and self.config.backend_repo.clone_path:
            changed_files = self.git_ops.get_changed_files(
                self.config.backend_repo.clone_path,
                self.config.base_commit,
                self.config.target_commit
            )
            all_changed_files.extend(changed_files)
            print(f"  Backend changes: {len(changed_files)} files")
        
        # Detect affected verification sections
        detector = FileChangeDetector([section.model_dump() for section in self.project_config.verification_sections])
        affected_sections = detector.get_affected_sections(all_changed_files)
        
        print(f"  ✅ Affected verifications: {list(affected_sections)}")
        return list(affected_sections)
    
    async def _run_verifications(self, verification_names: List[str]) -> List[Dict[str, Any]]:
        """Run the specified verifications."""
        if not verification_names:
            print("⚠️  No verifications to run")
            return []
        
        print(f"🔧 Running {len(verification_names)} verifications...")
        print(f"🔍 [CR_RUNNER] Verification names: {verification_names}")
        print(f"🔍 [CR_RUNNER] Estimated time: {len(verification_names) * 60} seconds (1 minute per verification)")
        import sys
        sys.stdout.flush()
        
        # Update project config with cloned repository paths
        print(f"🔍 [CR_RUNNER] Updating project paths with cloned repositories...")
        await self._update_project_paths()
        print(f"🔍 [CR_RUNNER] Project paths updated successfully")
        
        # Create verification engine
        print(f"🔍 [CR_RUNNER] Creating verification engine...")
        engine = VerificationEngine(self.project_config, self.ai_config)
        print(f"🔍 [CR_RUNNER] Verification engine created successfully")
        
        # Run verifications
        print(f"🔍 [CR_RUNNER] Starting verification process...")
        print(f"🔍 [CR_RUNNER] This will process each verification section sequentially...")
        results = await engine.run_all_verifications_with_progress(verification_names)
        print(f"🔍 [CR_RUNNER] Verification process completed, results count: {len(results)}")
        
        # Convert results to dict format
        results_dict = []
        for result in results:
            results_dict.append({
                "verification_name": result.verification_name,
                "success": result.success,
                "error_message": result.error_message,
                "report_file_path": result.report_file_path,
                "ai_provider": result.ai_provider,
                "ai_model": result.ai_model,
                "ai_tag": result.ai_tag
            })
        
        print(f"✅ Completed {len(results)} verifications")
        return results_dict
    
    async def _update_project_paths(self):
        """Update project configuration with cloned repository paths."""
        if self.config.documentation_repo and self.config.documentation_repo.clone_path:
            self.project_config.documentation_root_path = self.config.documentation_repo.clone_path
        
        if self.config.frontend_repo and self.config.frontend_repo.clone_path:
            self.project_config.frontend_project_path = self.config.frontend_repo.clone_path
        
        if self.config.backend_repo and self.config.backend_repo.clone_path:
            self.project_config.backend_project_path = self.config.backend_repo.clone_path
    
    async def _publish_results(self, results: List[Dict[str, Any]]):
        """Publish results to configured destination."""
        print(f"📤 Publishing results via {self.config.publish_method}...")
        
        if self.config.publish_method == "github":
            await self._publish_to_github(results)
        elif self.config.publish_method == "ftp":
            await self._publish_to_ftp(results)
        elif self.config.publish_method == "local":
            await self._publish_to_local(results)
        else:
            print(f"⚠️  Unknown publish method: {self.config.publish_method}")
    
    async def _publish_to_github(self, results: List[Dict[str, Any]]):
        """Publish results to GitHub."""
        if not self.config.publish_config or not self.config.publish_config.get('token'):
            print("⚠️  GitHub token not configured, skipping publishing")
            return
        
        try:
            from utils.output_publisher import GitHubPublisher
            
            publisher = GitHubPublisher(
                token=self.config.publish_config['token'],
                repo=self.config.publish_config['repo'],
                branch=self.config.publish_config['branch']
            )
            
            # Publish results
            published_files = await publisher.publish_results(
                self.config.output_folder,
                results
            )
            
            print(f"✅ Published {len(published_files)} files to GitHub")
            for file_path in published_files:
                print(f"  - {file_path}")
                
        except Exception as e:
            print(f"❌ Failed to publish to GitHub: {str(e)}")
            raise
    
    async def _publish_to_ftp(self, results: List[Dict[str, Any]]):
        """Publish results to FTP."""
        # This would be implemented based on your specific needs
        print("📤 Publishing to FTP (implementation needed)")
    
    async def _publish_to_local(self, results: List[Dict[str, Any]]):
        """Publish results to local directory."""
        print(f"📤 Results saved to: {self.config.output_folder}")


async def main():
    """Main entry point for CR runner."""
    parser = argparse.ArgumentParser(description="PRD Code Verifier - CR Mode")
    parser.add_argument("--config", help="Path to CR configuration file")
    parser.add_argument("--project-file", help="Path to project JSON file")
    parser.add_argument("--output-folder", help="Output folder for results")
    parser.add_argument("--mode", choices=["local", "github_actions", "gitlab_ci", "jenkins", "manual"], 
                       help="CR mode (defaults to CR_MODE environment variable)")
    parser.add_argument("--run-all", action="store_true", help="Run all verifications")
    parser.add_argument("--verifications", help="Comma-separated list of verification names to run")
    
    args = parser.parse_args()
    
    # Create configuration
    if args.config:
        # Load from file (implementation needed)
        config = CRConfig.from_env()  # For now, use env-based config
    else:
        config = CRConfig.from_env()
        
        # Override with command line arguments
        if args.project_file:
            config.project_file = args.project_file
        if args.output_folder:
            config.output_folder = args.output_folder
        if args.mode:
            config.mode = CRMode(args.mode)
        if args.run_all:
            config.run_all_verifications = True
        if args.verifications:
            config.specific_verifications = args.verifications.split(',')
    
    # Substitute environment variables
    config = config.substitute_env_vars()
    
    # Run CR process
    runner = CRRunner(config)
    result = await runner.run()
    
    # Print summary
    if result["status"] == "success":
        print(f"\n🎉 CR Summary:")
        print(f"  - Affected verifications: {len(result['affected_verifications'])}")
        print(f"  - Results: {len(result['results'])}")
    else:
        print(f"\n💥 CR Failed: {result['error']}")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
