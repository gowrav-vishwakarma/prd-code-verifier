"""
Git operations for CR mode.
Handles repository cloning and file change detection.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
import shutil


class GitOperations:
    """Handles Git repository operations for CR mode."""
    
    def __init__(self, work_dir: str = ".cr_workspace"):
        """
        Initialize Git operations.
        
        Args:
            work_dir: Directory to use for cloning repositories
        """
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(exist_ok=True)
        self.cloned_repos: Dict[str, str] = {}  # repo_url -> local_path
    
    def clone_repository(self, repo_url: str, branch: str = "main") -> str:
        """
        Clone a repository to the workspace.
        
        Args:
            repo_url: The repository URL (can contain $TOKEN patterns)
            branch: The branch to clone
            
        Returns:
            The local path where the repository was cloned
        """
        # Substitute environment variables in the repository URL
        from utils.env_substitution import EnvSubstitution
        processed_repo_url = EnvSubstitution.substitute(repo_url)
        
        # Generate a unique directory name based on repo URL (before token substitution)
        repo_name = self._get_repo_name(repo_url)
        clone_dir = self.work_dir / repo_name
        
        # Remove existing directory if it exists
        if clone_dir.exists():
            shutil.rmtree(clone_dir)
        
        try:
            # Clone the repository with processed URL
            cmd = ["git", "clone", "--depth", "1", "--branch", branch, processed_repo_url, str(clone_dir)]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            self.cloned_repos[repo_url] = str(clone_dir)
            return str(clone_dir)
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to clone repository {repo_url}: {e.stderr}")
    
    def get_changed_files(self, repo_path: str, base_commit: str = "HEAD~1", target_commit: str = "HEAD") -> List[str]:
        """
        Get list of changed files between two commits.
        
        Args:
            repo_path: Path to the repository
            base_commit: Base commit to compare from
            target_commit: Target commit to compare to
            
        Returns:
            List of changed file paths (relative to repo root)
        """
        try:
            cmd = ["git", "diff", "--name-only", base_commit, target_commit]
            result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, check=True)
            
            changed_files = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            return changed_files
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to get changed files: {e.stderr}")
    
    def get_file_content(self, repo_path: str, file_path: str) -> str:
        """
        Get content of a file from a specific commit.
        
        Args:
            repo_path: Path to the repository
            file_path: Relative path to the file
            
        Returns:
            File content as string
        """
        try:
            full_path = os.path.join(repo_path, file_path)
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise Exception(f"Failed to read file {file_path}: {str(e)}")
    
    def cleanup(self):
        """Clean up cloned repositories."""
        if self.work_dir.exists():
            shutil.rmtree(self.work_dir)
    
    def _get_repo_name(self, repo_url: str) -> str:
        """Extract repository name from URL."""
        # Remove .git extension and get the last part
        name = repo_url.split('/')[-1]
        if name.endswith('.git'):
            name = name[:-4]
        return name
    
    def get_repo_path(self, repo_url: str) -> Optional[str]:
        """Get the local path of a cloned repository."""
        return self.cloned_repos.get(repo_url)


class FileChangeDetector:
    """Detects which verification sections are affected by file changes."""
    
    def __init__(self, verification_sections: List[Dict]):
        """
        Initialize file change detector.
        
        Args:
            verification_sections: List of verification section configurations
        """
        self.verification_sections = verification_sections
        self.file_to_sections_map = self._build_file_mapping()
    
    def _build_file_mapping(self) -> Dict[str, List[str]]:
        """Build mapping from file paths to verification section names."""
        file_map = {}
        
        for section in self.verification_sections:
            section_name = section.get('name', '')
            
            # Map documentation files
            for doc_file in section.get('documentation_files', []):
                file_map[doc_file] = file_map.get(doc_file, []) + [section_name]
            
            # Map frontend files
            for frontend_file in section.get('frontend_code_files', []):
                file_map[frontend_file] = file_map.get(frontend_file, []) + [section_name]
            
            # Map backend files
            for backend_file in section.get('backend_code_files', []):
                file_map[backend_file] = file_map.get(backend_file, []) + [section_name]
        
        return file_map
    
    def get_affected_sections(self, changed_files: List[str]) -> Set[str]:
        """
        Get verification sections affected by changed files.
        
        Args:
            changed_files: List of changed file paths
            
        Returns:
            Set of verification section names that need to be run
        """
        affected_sections = set()
        
        for changed_file in changed_files:
            # Check if this file is used in any verification section
            if changed_file in self.file_to_sections_map:
                affected_sections.update(self.file_to_sections_map[changed_file])
        
        return affected_sections
    
    def get_sections_by_repo_type(self, changed_files: List[str], repo_type: str) -> Set[str]:
        """
        Get verification sections affected by changes in a specific repo type.
        
        Args:
            changed_files: List of changed file paths
            repo_type: Type of repository ('documentation', 'frontend', 'backend')
            
        Returns:
            Set of verification section names that need to be run
        """
        affected_sections = set()
        
        for changed_file in changed_files:
            # Check if this file is used in any verification section for the specific repo type
            for section in self.verification_sections:
                section_name = section.get('name', '')
                
                if repo_type == 'documentation':
                    if changed_file in section.get('documentation_files', []):
                        affected_sections.add(section_name)
                elif repo_type == 'frontend':
                    if changed_file in section.get('frontend_code_files', []):
                        affected_sections.add(section_name)
                elif repo_type == 'backend':
                    if changed_file in section.get('backend_code_files', []):
                        affected_sections.add(section_name)
        
        return affected_sections
