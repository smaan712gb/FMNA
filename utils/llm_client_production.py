"""
Production-Ready DeepSeek LLM Client
Includes: Retries, Circuit Breaker, Rate Limiting, Monitoring, Fallbacks
"""

from typing import List, Dict, Any, Optional, Generator, Callable
from openai import OpenAI, OpenAIError
from loguru import logger
import time
import json
from datetime import datetime, timedelta
from functools import wraps
from threading import Lock
import asyncio
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from config.settings import get_settings


class CircuitBreaker:
    """Circuit breaker pattern for LLM calls"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.lock = Lock()
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        with self.lock:
            if self.state == "OPEN":
                if self._should_attempt_reset():
                    self.state = "HALF_OPEN"
                    logger.info("Circuit breaker entering HALF_OPEN state")
                else:
                    raise Exception(f"Circuit breaker is OPEN. Recovery timeout: {self.recovery_timeout}s")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit"""
        if self.last_failure_time is None:
            return True
        return (datetime.utcnow() - self.last_failure_time).seconds >= self.recovery_timeout
    
    def _on_success(self):
        """Reset circuit breaker on successful call"""
        with self.lock:
            self.failure_count = 0
            self.state = "CLOSED"
            logger.debug("Circuit breaker reset to CLOSED state")
    
    def _on_failure(self):
        """Handle failure and potentially open circuit"""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger.error(
                    f"Circuit breaker OPENED after {self.failure_count} failures. "
                    f"Will retry after {self.recovery_timeout}s"
                )


class RateLimiter:
    """Token bucket rate limiter for API calls"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.tokens = requests_per_minute
        self.last_update = time.time()
        self.lock = Lock()
    
    def acquire(self):
        """Acquire a token for API call, blocking if necessary"""
        with self.lock:
            self._refill()
            
            if self.tokens < 1:
                sleep_time = 60.0 / self.requests_per_minute
                logger.warning(f"Rate limit reached, sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
                self._refill()
            
            self.tokens -= 1
    
    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_update
        
        tokens_to_add = (elapsed / 60.0) * self.requests_per_minute
        self.tokens = min(self.requests_per_minute, self.tokens + tokens_to_add)
        self.last_update = now


class LLMMetrics:
    """Collect and track LLM usage metrics"""
    
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        self.response_times = []
        self.lock = Lock()
    
    def record_request(
        self,
        success: bool,
        tokens: int = 0,
        response_time: float = 0.0,
        cost: float = 0.0
    ):
        """Record metrics for a request"""
        with self.lock:
            self.total_requests += 1
            if success:
                self.successful_requests += 1
            else:
                self.failed_requests += 1
            
            self.total_tokens += tokens
            self.total_cost += cost
            self.response_times.append(response_time)
            
            # Keep only last 1000 response times
            if len(self.response_times) > 1000:
                self.response_times = self.response_times[-1000:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        with self.lock:
            avg_response_time = (
                sum(self.response_times) / len(self.response_times)
                if self.response_times else 0.0
            )
            
            return {
                "total_requests": self.total_requests,
                "successful_requests": self.successful_requests,
                "failed_requests": self.failed_requests,
                "success_rate": (
                    self.successful_requests / self.total_requests
                    if self.total_requests > 0 else 0.0
                ),
                "total_tokens": self.total_tokens,
                "total_cost_usd": self.total_cost,
                "avg_response_time_seconds": avg_response_time
            }


class ProductionLLMClient:
    """
    Production-ready LLM client with:
    - Automatic retries with exponential backoff
    - Circuit breaker pattern
    - Rate limiting
    - Health checks
    - Metrics collection
    - Timeout handling
    - Logging and monitoring
    """
    
    # DeepSeek pricing (approximate, update as needed)
    COST_PER_1K_TOKENS_INPUT = 0.00014  # $0.14 per million tokens
    COST_PER_1K_TOKENS_OUTPUT = 0.00028  # $0.28 per million tokens
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 60,
        rate_limit_per_minute: int = 60
    ):
        """
        Initialize production LLM client
        
        Args:
            api_key: DeepSeek API key
            model: Model name
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
            rate_limit_per_minute: Maximum requests per minute
        """
        settings = get_settings()
        self.api_key = api_key or settings.deepseek_api_key
        self.model = model or settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
        self.base_url = settings.deepseek_api_url
        self.timeout = timeout
        
        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=timeout
        )
        
        # Production components
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=OpenAIError
        )
        self.rate_limiter = RateLimiter(requests_per_minute=rate_limit_per_minute)
        self.metrics = LLMMetrics()
        
        self.max_retries = max_retries
        self.is_healthy = True
        self.last_health_check = None
        
        logger.info(
            f"Production LLM Client initialized: "
            f"model={self.model}, timeout={timeout}s, "
            f"rate_limit={rate_limit_per_minute}/min"
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((OpenAIError, TimeoutError)),
        before_sleep=before_sleep_log(logger, "WARNING")
    )
    def _make_request(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ):
        """Internal method with retry logic"""
        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
            stream=stream
        )
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> str:
        """
        Send chat completion request with production safeguards
        
        Args:
            messages: List of message dicts
            temperature: Override default temperature
            max_tokens: Override default max tokens
            stream: Whether to stream response
            
        Returns:
            Response text
            
        Raises:
            Exception: If circuit breaker is open or request fails
        """
        start_time = time.time()
        success = False
        tokens_used = 0
        cost = 0.0
        
        try:
            # Rate limiting
            self.rate_limiter.acquire()
            
            # Circuit breaker
            response = self.circuit_breaker.call(
                self._make_request,
                messages,
                temperature,
                max_tokens,
                stream
            )
            
            if stream:
                return response
            
            # Extract response
            content = response.choices[0].message.content
            
            # Calculate tokens and cost
            if hasattr(response, 'usage'):
                tokens_used = response.usage.total_tokens
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                
                cost = (
                    (input_tokens / 1000) * self.COST_PER_1K_TOKENS_INPUT +
                    (output_tokens / 1000) * self.COST_PER_1K_TOKENS_OUTPUT
                )
            
            success = True
            logger.debug(
                f"LLM request successful: {tokens_used} tokens, "
                f"${cost:.6f}, {time.time() - start_time:.2f}s"
            )
            
            return content
            
        except Exception as e:
            logger.error(f"LLM request failed after retries: {str(e)}")
            self.is_healthy = False
            raise
        
        finally:
            # Record metrics
            response_time = time.time() - start_time
            self.metrics.record_request(
                success=success,
                tokens=tokens_used,
                response_time=response_time,
                cost=cost
            )
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on LLM service
        
        Returns:
            Health status dictionary
        """
        try:
            # Simple health check message
            test_messages = [
                {"role": "user", "content": "Hello"}
            ]
            
            start_time = time.time()
            response = self.chat(test_messages, max_tokens=10)
            response_time = time.time() - start_time
            
            self.is_healthy = True
            self.last_health_check = datetime.utcnow()
            
            return {
                "status": "healthy",
                "response_time_ms": response_time * 1000,
                "circuit_breaker_state": self.circuit_breaker.state,
                "last_check": self.last_health_check.isoformat()
            }
            
        except Exception as e:
            self.is_healthy = False
            logger.error(f"Health check failed: {str(e)}")
            
            return {
                "status": "unhealthy",
                "error": str(e),
                "circuit_breaker_state": self.circuit_breaker.state,
                "last_check": datetime.utcnow().isoformat()
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current usage metrics"""
        return {
            "metrics": self.metrics.get_stats(),
            "health": {
                "is_healthy": self.is_healthy,
                "circuit_breaker_state": self.circuit_breaker.state,
                "last_health_check": (
                    self.last_health_check.isoformat()
                    if self.last_health_check else None
                )
            }
        }
    
    def reset_circuit_breaker(self):
        """Manually reset circuit breaker (admin operation)"""
        self.circuit_breaker.failure_count = 0
        self.circuit_breaker.state = "CLOSED"
        logger.info("Circuit breaker manually reset")
    
    # Original methods with production wrappers
    
    def analyze_mda(self, mda_text: str) -> Dict[str, Any]:
        """Analyze MD&A section - production wrapped"""
        prompt = f"""Analyze the following Management Discussion & Analysis (MD&A) section and provide:

1. Key business trends and developments
2. Revenue drivers and headwinds
3. Profitability analysis (margin trends, cost pressures)
4. Liquidity and capital resources assessment
5. Forward-looking risks and opportunities
6. Red flags or areas of concern

MD&A Text:
{mda_text[:8000]}

Provide a structured JSON response with these sections."""

        messages = [
            {"role": "system", "content": "You are a financial analyst specializing in M&A due diligence."},
            {"role": "user", "content": prompt}
        ]
        
        response = self.chat(messages, temperature=0.1)
        
        try:
            return json.loads(response)
        except:
            return {"raw_analysis": response}
    
    def generate_red_flags_summary(
        self,
        financial_data: Dict[str, Any],
        filing_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate red flags summary - production wrapped"""
        prompt = f"""Conduct a quality of earnings analysis and identify potential red flags.

Financial Data:
{json.dumps(financial_data, indent=2)[:3000]}

Filing Data:
{json.dumps(filing_data, indent=2)[:3000]}

For each red flag identified, provide:
1. Category (Revenue Recognition, Working Capital, Debt, Governance, etc.)
2. Severity (Low/Medium/High/Critical)
3. Description
4. Estimated financial impact (if quantifiable)
5. Recommended mitigation or further diligence

Provide response as a JSON array of red flag objects."""

        messages = [
            {"role": "system", "content": "You are a due diligence expert conducting financial quality of earnings analysis."},
            {"role": "user", "content": prompt}
        ]
        
        response = self.chat(messages, temperature=0.1, max_tokens=3000)
        
        try:
            return json.loads(response)
        except:
            return [{"raw_analysis": response}]


# Global instance
_client: Optional[ProductionLLMClient] = None
_client_lock = Lock()


def get_llm_client() -> ProductionLLMClient:
    """Get or create global production LLM client instance"""
    global _client
    
    if _client is None:
        with _client_lock:
            if _client is None:  # Double-check locking
                _client = ProductionLLMClient()
    
    return _client


# Example usage
if __name__ == "__main__":
    client = get_llm_client()
    
    # Test basic chat
    try:
        response = client.chat([
            {"role": "user", "content": "What is 2+2?"}
        ])
        print(f"Response: {response}")
        
        # Check health
        health = client.health_check()
        print(f"Health: {health}")
        
        # Get metrics
        metrics = client.get_metrics()
        print(f"Metrics: {json.dumps(metrics, indent=2)}")
        
    except Exception as e:
        print(f"Error: {e}")
