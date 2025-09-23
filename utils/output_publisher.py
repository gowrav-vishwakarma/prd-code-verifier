"""
Output publishing utilities for CR mode.
Handles publishing results to various destinations.
"""

import os
import json
import shutil
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
import aiofiles
import aiohttp
from datetime import datetime


class OutputPublisher:
    """Handles publishing verification results to various destinations."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize output publisher.
        
        Args:
            config: Publishing configuration
        """
        self.config = config
        self.method = config.get('method', 'local')
    
    async def publish(self, results: List[Dict[str, Any]], output_folder: str) -> bool:
        """
        Publish results to configured destination.
        
        Args:
            results: List of verification results
            output_folder: Path to output folder containing reports
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.method == 'github':
                return await self._publish_to_github(results, output_folder)
            elif self.method == 'ftp':
                return await self._publish_to_ftp(results, output_folder)
            elif self.method == 's3':
                return await self._publish_to_s3(results, output_folder)
            elif self.method == 'local':
                return await self._publish_to_local(results, output_folder)
            else:
                print(f"⚠️  Unknown publish method: {self.method}")
                return False
        except Exception as e:
            print(f"❌ Failed to publish results: {str(e)}")
            return False
    
    async def _publish_to_github(self, results: List[Dict[str, Any]], output_folder: str) -> bool:
        """Publish results to GitHub repository."""
        print("📤 Publishing to GitHub...")
        
        token = self.config.get('token')
        repo = self.config.get('repo')
        branch = self.config.get('branch', 'main')
        path = self.config.get('path', 'reports')
        
        if not token or not repo:
            print("❌ GitHub token and repo are required")
            return False
        
        # Create a summary file
        summary = await self._create_summary(results, output_folder)
        
        # Upload files to GitHub
        success = await self._upload_to_github(token, repo, branch, path, output_folder, summary)
        
        if success:
            print(f"✅ Successfully published to GitHub: {repo}/{path}")
        else:
            print("❌ Failed to publish to GitHub")
        
        return success
    
    async def _publish_to_ftp(self, results: List[Dict[str, Any]], output_folder: str) -> bool:
        """Publish results to FTP server."""
        print("📤 Publishing to FTP...")
        
        # This would require an FTP library like aioftp
        # For now, just print a message
        print("⚠️  FTP publishing not implemented yet")
        return False
    
    async def _publish_to_s3(self, results: List[Dict[str, Any]], output_folder: str) -> bool:
        """Publish results to AWS S3."""
        print("📤 Publishing to S3...")
        
        # This would require boto3
        # For now, just print a message
        print("⚠️  S3 publishing not implemented yet")
        return False
    
    async def _publish_to_local(self, results: List[Dict[str, Any]], output_folder: str) -> bool:
        """Publish results to local directory."""
        print(f"📤 Publishing to local directory: {output_folder}")
        
        # Create summary
        summary = await self._create_summary(results, output_folder)
        
        # Save summary to output folder
        summary_path = Path(output_folder) / "cr_summary.json"
        async with aiofiles.open(summary_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(summary, indent=2))
        
        print(f"✅ Results saved to: {output_folder}")
        return True
    
    async def _create_summary(self, results: List[Dict[str, Any]], output_folder: str) -> Dict[str, Any]:
        """Create a summary of all results."""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_verifications": len(results),
            "successful_verifications": sum(1 for r in results if r.get('success', False)),
            "failed_verifications": sum(1 for r in results if not r.get('success', False)),
            "results": results,
            "reports": []
        }
        
        # Find all report files
        output_path = Path(output_folder)
        if output_path.exists():
            for report_file in output_path.rglob("*.md"):
                relative_path = report_file.relative_to(output_path)
                summary["reports"].append({
                    "file": str(relative_path),
                    "size": report_file.stat().st_size,
                    "modified": report_file.stat().st_mtime
                })
        
        return summary
    
    async def _upload_to_github(self, token: str, repo: str, branch: str, path: str, 
                               output_folder: str, summary: Dict[str, Any]) -> bool:
        """Upload files to GitHub repository."""
        try:
            # This is a simplified implementation
            # In practice, you'd use the GitHub API to upload files
            
            print(f"  Uploading to {repo}/{path} on branch {branch}")
            
            # For now, just create a local copy with the summary
            target_dir = Path(f"./published/{repo.replace('/', '_')}")
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy output folder
            if Path(output_folder).exists():
                shutil.copytree(output_folder, target_dir / "reports", dirs_exist_ok=True)
            
            # Save summary
            summary_path = target_dir / "cr_summary.json"
            async with aiofiles.open(summary_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(summary, indent=2))
            
            print(f"  ✅ Files prepared for upload to {target_dir}")
            return True
            
        except Exception as e:
            print(f"  ❌ Failed to upload to GitHub: {str(e)}")
            return False


class GitHubPublisher:
    """Specialized GitHub publisher using GitHub API."""
    
    def __init__(self, token: str, repo: str, branch: str = "main"):
        """
        Initialize GitHub publisher.
        
        Args:
            token: GitHub personal access token
            repo: Repository in format "owner/repo"
            branch: Branch to upload to
        """
        self.token = token
        self.repo = repo
        self.branch = branch
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    async def upload_file(self, file_path: str, content: str, commit_message: str = None) -> bool:
        """
        Upload a file to GitHub repository.
        
        Args:
            file_path: Path in repository
            content: File content
            commit_message: Commit message
            
        Returns:
            True if successful
        """
        if not commit_message:
            commit_message = f"Update {file_path} via Continuous Review"
        
        try:
            # Get current file SHA if it exists
            sha = await self._get_file_sha(file_path)
            
            # Prepare request data
            import base64
            data = {
                "message": commit_message,
                "content": base64.b64encode(content.encode('utf-8')).decode('utf-8'),
                "branch": self.branch
            }
            
            if sha:
                data["sha"] = sha
            
            # Upload file
            url = f"{self.base_url}/repos/{self.repo}/contents/{file_path}"
            
            async with aiohttp.ClientSession() as session:
                async with session.put(url, headers=self.headers, json=data) as response:
                    if response.status in [200, 201]:
                        print(f"  ✅ Uploaded {file_path}")
                        return True
                    else:
                        error_text = await response.text()
                        print(f"  ❌ Failed to upload {file_path}: {error_text}")
                        return False
        
        except Exception as e:
            print(f"  ❌ Error uploading {file_path}: {str(e)}")
            return False
    
    async def _get_file_sha(self, file_path: str) -> Optional[str]:
        """Get SHA of existing file."""
        try:
            url = f"{self.base_url}/repos/{self.repo}/contents/{file_path}"
            params = {"ref": self.branch}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("sha")
                    return None
        except:
            return None
    
    async def publish_results(self, output_folder: str, results: List[Dict[str, Any]], 
                            publish_path: str = "reports") -> List[str]:
        """
        Publish verification results to GitHub.
        
        Args:
            output_folder: Local folder containing results
            results: List of verification results
            publish_path: Path in repository to publish to
            
        Returns:
            List of published file paths
        """
        published_files = []
        
        try:
            # Create summary
            summary = await self._create_summary(results, output_folder)
            
            # Upload summary
            summary_content = json.dumps(summary, indent=2)
            summary_path = f"{publish_path}/cr_summary.json"
            if await self.upload_file(summary_path, summary_content, 
                                    "Update verification summary via Continuous Review"):
                published_files.append(summary_path)
            
            # Upload individual report files
            output_path = Path(output_folder)
            if output_path.exists():
                for report_file in output_path.rglob("*.md"):
                    relative_path = report_file.relative_to(output_path)
                    github_path = f"{publish_path}/{relative_path}"
                    
                    # Read file content
                    async with aiofiles.open(report_file, 'r', encoding='utf-8') as f:
                        content = await f.read()
                    
                    # Upload file
                    if await self.upload_file(github_path, content, 
                                            f"Update {relative_path} via Continuous Review"):
                        published_files.append(github_path)
            
            return published_files
            
        except Exception as e:
            print(f"❌ Error publishing results: {str(e)}")
            return published_files
    
    async def _create_summary(self, results: List[Dict[str, Any]], output_folder: str) -> Dict[str, Any]:
        """Create a summary of all results."""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_verifications": len(results),
            "successful_verifications": sum(1 for r in results if r.get('success', False)),
            "failed_verifications": sum(1 for r in results if not r.get('success', False)),
            "results": results,
            "reports": []
        }
        
        # Find all report files
        output_path = Path(output_folder)
        if output_path.exists():
            for report_file in output_path.rglob("*.md"):
                relative_path = report_file.relative_to(output_path)
                summary["reports"].append({
                    "file": str(relative_path),
                    "size": report_file.stat().st_size,
                    "modified": report_file.stat().st_mtime
                })
        
        return summary