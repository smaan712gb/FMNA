"""
FastAPI Application
REST API for FMNA platform - user interaction layer
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger

from orchestration.langgraph_orchestrator import LangGraphOrchestrator
from agents.ingestion_agent import IngestionAgent
from agents.modeling_agent import ModelingAgent
from agents.exporter_agent import ExporterAgent
from agents.normalization_agent import NormalizationAgent
from agents.dd_agents import DDAgentsSuite
from storage.redis_adapter import RedisAdapter
from config.settings import get_settings


# API Models
class AnalysisRequest(BaseModel):
    """Request for M&A analysis"""
    symbol: str
    company_name: Optional[str] = None
    analysis_type: str = "full"  # full, dcf_only, cca_only, lbo_only, dd_only
    years: int = 5
    include_filing: bool = True


class ValuationResponse(BaseModel):
    """Valuation response"""
    symbol: str
    company_name: str
    timestamp: str
    valuation_range: Optional[tuple] = None
    recommended_value: Optional[float] = None
    methods_used: List[str]
    status: str


class DDRequest(BaseModel):
    """Due diligence request"""
    symbol: str
    categories: List[str] = ["financial", "commercial", "legal", "tech", "esg", "hr"]


class DDResponse(BaseModel):
    """Due diligence response"""
    symbol: str
    total_risks: int
    critical_risks: int
    by_category: Dict[str, int]
    by_severity: Dict[str, int]


# Initialize FastAPI
app = FastAPI(
    title="FMNA - Financial M&A Analytics Platform",
    description="Production-grade M&A analytics with Cognee, FMP, and EDGAR",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
settings = get_settings()
orchestrator = LangGraphOrchestrator() if settings.environment != "test" else None
cache = RedisAdapter()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "FMNA Platform API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "api": "healthy",
        "orchestrator": orchestrator.enabled if orchestrator else False,
        "redis_cache": cache.enabled,
        "environment": settings.environment
    }


@app.post("/analysis/run", response_model=ValuationResponse)
async def run_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Run M&A analysis workflow
    
    Args:
        request: Analysis request parameters
        background_tasks: FastAPI background tasks
        
    Returns:
        ValuationResponse with results
    """
    logger.info(f"API: Analysis request for {request.symbol}")
    
    # Check cache first
    cached_result = cache.get_valuation(request.symbol)
    if cached_result and request.analysis_type == "full":
        logger.info(f"Returning cached result for {request.symbol}")
        return ValuationResponse(
            symbol=request.symbol,
            company_name=cached_result.get('company_name', request.symbol),
            timestamp=cached_result.get('timestamp', datetime.utcnow().isoformat()),
            valuation_range=cached_result.get('valuation_range'),
            recommended_value=cached_result.get('recommended_value'),
            methods_used=cached_result.get('methods_used', []),
            status="completed_cached"
        )
    
    # Run analysis via orchestrator
    if orchestrator and orchestrator.enabled:
        try:
            task_description = f"{request.analysis_type} analysis for {request.symbol}"
            final_state = orchestrator.execute_workflow(request.symbol, task_description)
            
            response = ValuationResponse(
                symbol=request.symbol,
                company_name=final_state.get('company_name', request.symbol),
                timestamp=datetime.utcnow().isoformat(),
                valuation_range=None,  # Extract from final_state
                recommended_value=None,
                methods_used=['DCF', 'CCA'],
                status="completed"
            )
            
            # Cache result in background
            background_tasks.add_task(
                cache.cache_valuation,
                request.symbol,
                response.dict()
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=503, detail="Orchestrator not available")


@app.post("/dd/run", response_model=DDResponse)
async def run_due_diligence(request: DDRequest):
    """
    Run due diligence analysis
    
    Args:
        request: DD request parameters
        
    Returns:
        DDResponse with risk assessment
    """
    logger.info(f"API: DD request for {request.symbol}")
    
    try:
        dd_suite = DDAgentsSuite()
        
        # Mock data for demo - in production, fetch from database
        financial_data = {'revenue': [1_000_000_000]}
        
        import asyncio
        results = asyncio.run(dd_suite.run_full_dd(
            symbol=request.symbol,
            financial_data=financial_data
        ))
        
        summary = dd_suite.generate_dd_summary(results)
        
        return DDResponse(
            symbol=request.symbol,
            total_risks=summary['total_risks'],
            critical_risks=len(summary['critical_risks']),
            by_category=summary['by_category'],
            by_severity=summary['by_severity']
        )
        
    except Exception as e:
        logger.error(f"DD analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/company/{symbol}/profile")
async def get_company_profile(symbol: str):
    """Get company profile from cache or fetch"""
    logger.info(f"API: Profile request for {symbol}")
    
    # Try cache first
    cached = cache.get_peer_snapshot(symbol)
    if cached:
        return cached
    
    # Fetch from FMP
    try:
        from ingestion.fmp_client import FMPClient
        fmp = FMPClient()
        profile = fmp.get_company_profile(symbol)
        
        if profile:
            profile_dict = profile.dict()
            cache.cache_peer_snapshot(symbol, profile_dict)
            return profile_dict
        else:
            raise HTTPException(status_code=404, detail=f"Company {symbol} not found")
            
    except Exception as e:
        logger.error(f"Profile fetch failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/{symbol}")
async def ingest_company_data(symbol: str, years: int = 5):
    """Trigger data ingestion for a company"""
    logger.info(f"API: Ingestion request for {symbol}")
    
    try:
        agent = IngestionAgent()
        results = agent.ingest_company_full(
            symbol=symbol,
            years_of_financials=years,
            include_filings=True,
            include_market_data=True
        )
        agent.close()
        
        return {
            "symbol": symbol,
            "status": "completed",
            "financials_count": results['financials_count'],
            "filings_count": results['filings_count'],
            "cognee_nodes": results['cognee_nodes']
        }
        
    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/cache/{symbol}")
async def invalidate_cache(symbol: str):
    """Invalidate all cache for a symbol"""
    logger.info(f"API: Cache invalidation for {symbol}")
    
    count = cache.invalidate(f"*{symbol}*")
    
    return {
        "symbol": symbol,
        "invalidated_count": count
    }


if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*70)
    print("FMNA API SERVER")
    print("="*70)
    print(f"\nStarting API server on {settings.backend_url}")
    print(f"Environment: {settings.environment}")
    print(f"\nAPI Documentation: {settings.backend_url}/docs")
    print("="*70 + "\n")
    
    uvicorn.run(
        "main_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
