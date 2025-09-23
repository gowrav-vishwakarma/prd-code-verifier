"""
CR (Continuous Review) mode configuration.
"""

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from utils.env_substitution import EnvSubstitution


class CRMode(Enum):
    """CR mode types."""
    LOCAL = "local"
    GITHUB_ACTIONS = "github_actions"
    GITLAB_CI = "gitlab_ci"
    JENKINS = "jenkins"
    MANUAL = "manual"


@dataclass
class CRRepositoryConfig:
    """Configuration for a repository in CR mode."""
    name: str
    url: str  # Can contain $TOKEN patterns
    branch: str = "main"
    repo_type: str = "code"  # 'documentation', 'frontend', 'backend', 'code'
    clone_path: Optional[str] = None  # Will be set after cloning


@dataclass
class CRConfig:
    """CR mode configuration."""
    mode: CRMode
    project_file: str  # Path to project JSON file (can contain $VARS)
    output_folder: str  # Where to save results (can contain $VARS)
    
    # Repository configurations
    documentation_repo: Optional[CRRepositoryConfig] = None
    frontend_repo: Optional[CRRepositoryConfig] = None
    backend_repo: Optional[CRRepositoryConfig] = None
    
    # Git configuration
    base_commit: str = "HEAD~1"
    target_commit: str = "HEAD"
    
    # Verification configuration
    run_all_verifications: bool = False
    specific_verifications: Optional[List[str]] = None
    
    # AI configuration
    ai_provider: str = "openai"
    ai_model: str = "gpt-3.5-turbo"
    ai_base_url: Optional[str] = None
    
    # Output publishing
    publish_results: bool = False
    publish_method: str = "github"  # 'github', 'ftp', 's3', 'local'
    publish_config: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_env(cls) -> 'CRConfig':
        """Create CR configuration from environment variables."""
        mode = CRMode(os.getenv('CR_MODE', 'local'))
        
        # Get project file path
        project_file = os.getenv('CR_PROJECT_FILE', 'projects/default.json')
        
        # Get output folder
        output_folder = os.getenv('CR_OUTPUT_FOLDER', './output')
        
        # Get repository configurations
        doc_repo = None
        if os.getenv('CR_DOCUMENTATION_REPO_URL'):
            doc_repo = CRRepositoryConfig(
                name="documentation",
                url=os.getenv('CR_DOCUMENTATION_REPO_URL'),
                branch=os.getenv('CR_DOCUMENTATION_REPO_BRANCH', 'main'),
                repo_type='documentation'
            )
        
        frontend_repo = None
        if os.getenv('CR_FRONTEND_REPO_URL'):
            frontend_repo = CRRepositoryConfig(
                name="frontend",
                url=os.getenv('CR_FRONTEND_REPO_URL'),
                branch=os.getenv('CR_FRONTEND_REPO_BRANCH', 'main'),
                repo_type='frontend'
            )
        
        backend_repo = None
        if os.getenv('CR_BACKEND_REPO_URL'):
            backend_repo = CRRepositoryConfig(
                name="backend",
                url=os.getenv('CR_BACKEND_REPO_URL'),
                branch=os.getenv('CR_BACKEND_REPO_BRANCH', 'main'),
                repo_type='backend'
            )
        
        # Get verification configuration
        run_all = os.getenv('CR_RUN_ALL_VERIFICATIONS', 'false').lower() == 'true'
        specific_verifications = None
        if os.getenv('CR_SPECIFIC_VERIFICATIONS'):
            specific_verifications = os.getenv('CR_SPECIFIC_VERIFICATIONS').split(',')
        
        # Get AI configuration
        ai_provider = os.getenv('CR_AI_PROVIDER', 'openai')
        ai_model = os.getenv('CR_AI_MODEL', 'gpt-3.5-turbo')
        ai_base_url = os.getenv('CR_AI_BASE_URL')
        
        # Get output publishing configuration
        publish_results = os.getenv('CR_PUBLISH_RESULTS', 'false').lower() == 'true'
        publish_method = os.getenv('CR_PUBLISH_METHOD', 'github')
        
        publish_config = {}
        if publish_method == 'github':
            publish_config = {
                'token': os.getenv('CR_GITHUB_TOKEN'),
                'repo': os.getenv('CR_GITHUB_REPO'),
                'branch': os.getenv('CR_GITHUB_BRANCH', 'main'),
                'path': os.getenv('CR_GITHUB_PATH', 'reports')
            }
        elif publish_method == 'ftp':
            publish_config = {
                'host': os.getenv('CR_FTP_HOST'),
                'username': os.getenv('CR_FTP_USERNAME'),
                'password': os.getenv('CR_FTP_PASSWORD'),
                'path': os.getenv('CR_FTP_PATH', '/reports')
            }
        
        return cls(
            mode=mode,
            project_file=project_file,
            output_folder=output_folder,
            documentation_repo=doc_repo,
            frontend_repo=frontend_repo,
            backend_repo=backend_repo,
            base_commit=os.getenv('CR_BASE_COMMIT', 'HEAD~1'),
            target_commit=os.getenv('CR_TARGET_COMMIT', 'HEAD'),
            run_all_verifications=run_all,
            specific_verifications=specific_verifications,
            ai_provider=ai_provider,
            ai_model=ai_model,
            ai_base_url=ai_base_url,
            publish_results=publish_results,
            publish_method=publish_method,
            publish_config=publish_config
        )
    
    def substitute_env_vars(self) -> 'CRConfig':
        """Substitute environment variables in configuration."""
        # Convert to dict, substitute, and recreate
        config_dict = {
            'mode': self.mode.value,  # Convert enum to string for substitution
            'project_file': self.project_file,
            'output_folder': self.output_folder,
            'documentation_repo': self.documentation_repo.__dict__ if self.documentation_repo else None,
            'frontend_repo': self.frontend_repo.__dict__ if self.frontend_repo else None,
            'backend_repo': self.backend_repo.__dict__ if self.backend_repo else None,
            'base_commit': self.base_commit,
            'target_commit': self.target_commit,
            'run_all_verifications': self.run_all_verifications,
            'specific_verifications': self.specific_verifications,
            'ai_provider': self.ai_provider,
            'ai_model': self.ai_model,
            'ai_base_url': self.ai_base_url,
            'publish_results': self.publish_results,
            'publish_method': self.publish_method,
            'publish_config': self.publish_config
        }
        
        # Substitute environment variables
        substituted = EnvSubstitution.substitute_config(config_dict)
        
        # Recreate the configuration
        return CRConfig(
            mode=CRMode(substituted['mode']),
            project_file=substituted['project_file'],
            output_folder=substituted['output_folder'],
            documentation_repo=CRRepositoryConfig(**substituted['documentation_repo']) if substituted['documentation_repo'] else None,
            frontend_repo=CRRepositoryConfig(**substituted['frontend_repo']) if substituted['frontend_repo'] else None,
            backend_repo=CRRepositoryConfig(**substituted['backend_repo']) if substituted['backend_repo'] else None,
            base_commit=substituted['base_commit'],
            target_commit=substituted['target_commit'],
            run_all_verifications=substituted['run_all_verifications'],
            specific_verifications=substituted['specific_verifications'],
            ai_provider=substituted['ai_provider'],
            ai_model=substituted['ai_model'],
            ai_base_url=substituted['ai_base_url'],
            publish_results=substituted['publish_results'],
            publish_method=substituted['publish_method'],
            publish_config=substituted['publish_config']
        )
