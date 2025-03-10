import google.generativeai as genai
from google.api_core import retry_async
import uuid
import json
from typing import Optional
import logging
from .models import LLMReviewResult, BugInfo, Suggestion
from .config import settings
from .prompts import CODE_REVIEW_PROMPT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            logger.info("Successfully initialized Gemini AI client")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI client: {e}")
            raise
    
    @retry_async.AsyncRetry(predicate=retry_async.if_exception_type(Exception))
    async def review_code(
        self,
        code: str,
        language: str,
        context: Optional[str] = None
    ) -> LLMReviewResult:
        try:
            prompt = CODE_REVIEW_PROMPT.format(
                language=language,
                context=context if context else "No additional context provided",
                code=code
            )
            
            response = self.model.generate_content(prompt)
            
            review_text = response.text
            
            bugs_detected = []
            suggestions = []
            
            try:
                if "```json" in review_text:
                    json_parts = review_text.split("```json")
                    if len(json_parts) > 1:
                        json_content = json_parts[1].split("```")[0].strip()
                        structured_data = json.loads(json_content)
                        
                        if "bugs" in structured_data:
                            for bug in structured_data["bugs"]:
                                bugs_detected.append(
                                    BugInfo(
                                        line=bug.get("line", 0),
                                        description=bug.get("description", ""),
                                        severity=bug.get("severity", "medium"),
                                        suggestion=bug.get("suggestion")
                                    )
                                )
                        
                        if "suggestions" in structured_data:
                            for suggestion in structured_data["suggestions"]:
                                suggestions.append(
                                    Suggestion(
                                        description=suggestion.get("description", ""),
                                        code_snippet=suggestion.get("code_snippet")
                                    )
                                )
            except Exception as parse_error:
                logger.warning(f"Error parsing structured data: {parse_error}")
                pass
            
            request_id = str(uuid.uuid4())
            
            return LLMReviewResult(
                review=review_text,
                bugs_detected=bugs_detected,
                suggestions=suggestions,
                request_id=request_id
            )
            
        except Exception as e:
            logger.error(f"Error in code review: {e}")
            raise
