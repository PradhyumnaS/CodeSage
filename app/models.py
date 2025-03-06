from pydantic import BaseModel
from typing import List, Dict, Optional, Any

class CodeReviewRequest(BaseModel):
    code: str
    language: str
    context: Optional[str] = None
    
class BugInfo(BaseModel):
    line: int
    description: str
    severity: str
    suggestion: Optional[str] = None

class Suggestion(BaseModel):
    description: str
    code_snippet: Optional[str] = None
    
class LLMReviewResult(BaseModel):
    review: str
    bugs_detected: List[BugInfo]
    suggestions: List[Suggestion]
    request_id: str
    
class CodeReviewResponse(BaseModel):
    review: str
    bugs_detected: List[BugInfo]
    suggestions: List[Suggestion]
    request_id: str
    timestamp: str

class RateLimitExceededError(Exception):
    pass

class GithubWebhookPayload(BaseModel):
    action: str
    pull_request: Dict[str, Any]
    repository: Dict[str, Any]

class FeedbackRequest(BaseModel):
    request_id: str
    helpful: bool
    comment: Optional[str] = None
    user_id: Optional[str] = "anonymous"
