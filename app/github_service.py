import os
import logging
import aiohttp
from typing import Dict, Any, List
from .config import settings
from .llm_service import LLMService
from .prompts import PULL_REQUEST_REVIEW_PROMPT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitHubService:
    def __init__(self):
        self.github_token = settings.GITHUB_TOKEN
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.api_base_url = "https://api.github.com"
    
    async def get_pr_diff(self, repo_full_name: str, pr_number: int) -> str:
        url = f"{self.api_base_url}/repos/{repo_full_name}/pulls/{pr_number}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, 
                headers={"Authorization": f"token {self.github_token}", 
                         "Accept": "application/vnd.github.v3.diff"}
            ) as response:
                if response.status != 200:
                    logger.error(f"Error fetching PR diff: {await response.text()}")
                    return ""
                return await response.text()
    
    async def get_pr_files(self, repo_full_name: str, pr_number: int) -> List[Dict[str, Any]]:
        url = f"{self.api_base_url}/repos/{repo_full_name}/pulls/{pr_number}/files"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status != 200:
                    logger.error(f"Error fetching PR files: {await response.text()}")
                    return []
                return await response.json()
    
    async def get_file_content(self, repo_full_name: str, path: str, ref: str) -> str:
        url = f"{self.api_base_url}/repos/{repo_full_name}/contents/{path}?ref={ref}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status != 200:
                    logger.error(f"Error fetching file content: {await response.text()}")
                    return ""
                data = await response.json()
                if data.get("encoding") == "base64":
                    import base64
                    return base64.b64decode(data.get("content", "")).decode("utf-8")
                return ""
    
    async def create_pr_comment(self, repo_full_name: str, pr_number: int, comment: str) -> bool:
        url = f"{self.api_base_url}/repos/{repo_full_name}/issues/{pr_number}/comments"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=self.headers,
                json={"body": comment}
            ) as response:
                if response.status != 201:
                    logger.error(f"Error creating PR comment: {await response.text()}")
                    return False
                return True
    
    async def process_pull_request(self, payload: Dict[str, Any], llm_service: LLMService) -> None:
        try:
            pr = payload["pull_request"]
            repo = payload["repository"]
            
            repo_full_name = repo["full_name"]
            pr_number = pr["number"]
            pr_title = pr["title"]
            pr_description = pr["body"] or "No description provided"
            pr_head_sha = pr["head"]["sha"]
            
            pr_files = await self.get_pr_files(repo_full_name, pr_number)
            
            files_to_review = []
            important_extensions = ['.py', '.js', '.ts', '.java', '.go', '.cpp', '.c', '.h', '.cs', '.php', '.rb']
            
            for file in pr_files:
                _, ext = os.path.splitext(file["filename"])
                if ext in important_extensions:
                    files_to_review.append(file)
                    
                    if len(files_to_review) >= 5:
                        break
            
            if len(files_to_review) < 5:
                remaining_slots = 5 - len(files_to_review)
                file_names_to_review = [f["filename"] for f in files_to_review]
                
                for file in pr_files:
                    if file["filename"] not in file_names_to_review:
                        files_to_review.append(file)
                        remaining_slots -= 1
                        
                        if remaining_slots <= 0:
                            break
            
            files_content = ""
            for file in files_to_review:
                filename = file["filename"]
                _, ext = os.path.splitext(filename)
                language = ext[1:] if ext else "text"
                
                content = await self.get_file_content(repo_full_name, filename, pr_head_sha)
                if content:
                    files_content += f"\n--- {filename} ---\n```{language}\n{content}\n```\n"
            
            review_prompt = PULL_REQUEST_REVIEW_PROMPT.format(
                repo=repo_full_name,
                title=pr_title,
                description=pr_description,
                files=files_content
            )
            
            review_response = await llm_service.model.generate_content(review_prompt)
            review_text = review_response.text
            
            comment = (
                "# 🤖 Automated Code Review\n\n"
                "I've reviewed this pull request and here's my feedback:\n\n"
                f"{review_text}\n\n"
                "_This review was automatically generated by the Intelligent Code Review system._"
            )
            
            await self.create_pr_comment(repo_full_name, pr_number, comment)
            logger.info(f"Created review comment on PR #{pr_number} in {repo_full_name}")
            
        except Exception as e:
            logger.error(f"Error processing pull request: {e}")
