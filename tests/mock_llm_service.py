from app.models import LLMReviewResult, BugInfo, Suggestion
import uuid

class MockLLMService:
    """Mock LLM service for testing."""
    
    async def review_code(self, code, language, context=None):
        """Return a mock review result."""
        
        if not code.strip():
            return LLMReviewResult(
                review="No code provided for review.",
                bugs_detected=[],
                suggestions=[],
                request_id=str(uuid.uuid4())
            )
        
        if language.lower() == "python":
            return LLMReviewResult(
                review="This is a mock review of Python code. The code looks good overall, but there are a few issues to address.",
                bugs_detected=[
                    BugInfo(
                        line=1,
                        description="Potential division by zero if x is 0",
                        severity="medium",
                        suggestion="Add a check to ensure x is not zero before division."
                    )
                ],
                suggestions=[
                    Suggestion(
                        description="Consider using a docstring to document this function",
                        code_snippet='def calculate_ratio(x, y):\n    """Calculate the ratio of y to x."""\n    if x == 0:\n        return 0\n    return y / x'
                    )
                ],
                request_id=str(uuid.uuid4())
            )
        
        return LLMReviewResult(
            review=f"This is a mock review of {language} code.",
            bugs_detected=[],
            suggestions=[
                Suggestion(
                    description="This is a mock suggestion",
                    code_snippet="// This is a mock code snippet"
                )
            ],
            request_id=str(uuid.uuid4())
        )