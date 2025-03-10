from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
import hashlib
import hmac
import json
from datetime import datetime
import time
from prometheus_client import Counter, Gauge, Histogram, Info, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
from .models import (
    CodeReviewRequest, 
    CodeReviewResponse, 
    GithubWebhookPayload,
    RateLimitExceededError,
    FeedbackRequest
)
from .llm_service import LLMService
from .github_service import GitHubService
from .config import settings
from .rate_limiter import RateLimiter
from .cache_manager import CacheManager

app = FastAPI(
    title="CodeSage",
    description="An API for automated code review and bug prediction",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm_service = LLMService()
github_service = GitHubService()
cache_manager = CacheManager()
rate_limiter = RateLimiter(
    redis_host=settings.REDIS_HOST,
    redis_port=settings.REDIS_PORT,
    rate_limit=settings.RATE_LIMIT,
    window_minutes=settings.RATE_LIMIT_WINDOW
)

REVIEW_REQUESTS = Counter('codesage_review_requests_total', 'Total code review requests', ['language'])
REVIEW_LATENCY = Histogram('codesage_review_latency_seconds', 'Latency of code review requests', 
                          buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0])
BUGS_DETECTED = Counter('codesage_bugs_detected_total', 'Total bugs detected', ['severity'])
SUGGESTIONS_MADE = Counter('codesage_suggestions_total', 'Total improvement suggestions made')
WEBHOOK_REQUESTS = Counter('codesage_github_webhook_requests_total', 'Total GitHub webhook requests', ['event_type'])
FEEDBACK_SUBMISSIONS = Counter('codesage_feedback_submissions_total', 'Total feedback submissions', ['helpful'])
CACHE_HITS = Counter('codesage_cache_hits_total', 'Total cache hits')
CACHE_MISSES = Counter('codesage_cache_misses_total', 'Total cache misses')
RATE_LIMIT_EXCEEDED = Counter('codesage_rate_limit_exceeded_total', 'Total rate limit exceeded events')
API_INFO = Info('codesage_api', 'Information about the CodeSage API')
API_INFO.info({'version': '1.0.0', 'author': 'CodeSage Team'})
ACTIVE_REVIEWS = Gauge('codesage_active_reviews', 'Number of reviews currently being processed')

@app.get("/")
async def root():
    return {"status": "online", "message": "CodeSage API is running"}

@app.post("/review", response_model=CodeReviewResponse)
async def review_code(
    request: CodeReviewRequest,
    background_tasks: BackgroundTasks,
    user_id: str = "anonymous"
):
    if not await rate_limiter.check_rate_limit(user_id):
        RATE_LIMIT_EXCEEDED.inc()
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    REVIEW_REQUESTS.labels(language=request.language).inc()
    start_time = time.time()
    ACTIVE_REVIEWS.inc()
    
    cache_key = hashlib.md5(f"{request.code}:{request.language}".encode()).hexdigest()
    cached_response = await cache_manager.get_cached_review(cache_key)
    if cached_response:
        CACHE_HITS.inc()
        REVIEW_LATENCY.observe(time.time() - start_time)
        ACTIVE_REVIEWS.dec()
        return cached_response
    
    CACHE_MISSES.inc()
    
    try:
        review_result = await llm_service.review_code(
            code=request.code,
            language=request.language,
            context=request.context
        )
        
        # Track bugs by severity
        for bug in review_result.bugs_detected:
            BUGS_DETECTED.labels(severity=bug.severity.lower()).inc()
            
        # Track suggestions
        SUGGESTIONS_MADE.inc(len(review_result.suggestions))
        
        response = CodeReviewResponse(
            review=review_result.review,
            bugs_detected=review_result.bugs_detected,
            suggestions=review_result.suggestions,
            request_id=review_result.request_id,
            timestamp=datetime.now().isoformat()
        )
        
        background_tasks.add_task(
            cache_manager.cache_review,
            cache_key,
            response
        )
        
        REVIEW_LATENCY.observe(time.time() - start_time)
        ACTIVE_REVIEWS.dec()
        return response
    
    except Exception as e:
        ACTIVE_REVIEWS.dec()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    payload = await request.body()
    event_type = request.headers.get("X-GitHub-Event", "unknown")
    WEBHOOK_REQUESTS.labels(event_type=event_type).inc()
    
    if settings.GITHUB_WEBHOOK_SECRET:
        signature = request.headers.get("X-Hub-Signature-256")
        if not signature:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        digest = hmac.new(
            settings.GITHUB_WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(f"sha256={digest}", signature):
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        payload_dict = json.loads(payload)
        
        if event_type == "pull_request" and payload_dict["action"] in ["opened", "synchronize"]:
            background_tasks.add_task(
                github_service.process_pull_request,
                payload_dict,
                llm_service
            )
    
    return {"status": "processing"}

@app.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    FEEDBACK_SUBMISSIONS.labels(helpful="yes" if feedback.helpful else "no").inc()
    
    await cache_manager.store_feedback(feedback)
    
    return {"status": "success", "message": "Feedback submitted successfully"}

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
