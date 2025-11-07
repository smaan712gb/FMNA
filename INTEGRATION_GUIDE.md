# Integration Guide: Using the New Memory Manager

## Quick Start

The new `MemoryManager` is now available and ready to use in your platform!

### Import

```python
# Option 1: Direct import
from storage.memory_manager import MemoryManager, AnalysisMemory, get_memory_manager

# Option 2: From storage module
from storage import MemoryManager, get_memory_manager
```

### Basic Usage

```python
# Get the global instance (recommended)
mm = get_memory_manager()

# Or create a new instance
mm = MemoryManager()
```

## Integration Examples

### 1. In Your Agents

Update your agents to use the memory manager:

```python
# agents/modeling_agent.py
from storage import get_memory_manager, AnalysisMemory

class ModelingAgent:
    def __init__(self):
        self.memory = get_memory_manager()
    
    def run_merger_analysis(self, ticker: str, target: str):
        # Your analysis logic here
        results = self.analyze_merger(ticker, target)
        
        # Store in memory
        memory = AnalysisMemory(
            session_id=self.session_id,
            ticker=ticker,
            context={
                "analysis_type": "merger_model",
                "target": target
            },
            results=results
        )
        self.memory.store_analysis(memory)
        
        return results
```

### 2. In Your Orchestrator

Update `orchestration/langgraph_orchestrator.py`:

```python
from langgraph.checkpoint import MemorySaver
from langgraph.graph import StateGraph
from storage import get_memory_manager

class FinancialAnalysisOrchestrator:
    def __init__(self):
        # LangGraph's built-in memory
        self.graph_memory = MemorySaver()
        
        # Our custom memory manager for analysis storage
        self.analysis_memory = get_memory_manager()
        
        self.graph = self.build_graph()
    
    def build_graph(self):
        graph = StateGraph(FinancialAnalysisState)
        # Add your nodes
        return graph.compile(checkpointer=self.graph_memory)
    
    def store_analysis_result(self, state: dict):
        """Store completed analysis"""
        memory = AnalysisMemory(
            session_id=state['session_id'],
            ticker=state['ticker'],
            context=state['context'],
            results=state['results']
        )
        self.analysis_memory.store_analysis(memory)
```

### 3. In Your API

Update `api/main_api.py` to include memory endpoints:

```python
from fastapi import FastAPI, HTTPException
from storage import get_memory_manager

app = FastAPI()
mm = get_memory_manager()

@app.get("/api/analysis/history/{ticker}")
async def get_analysis_history(ticker: str, limit: int = 10):
    """Get analysis history for a ticker"""
    history = mm.get_history(ticker=ticker, limit=limit)
    return {"ticker": ticker, "count": len(history), "analyses": history}

@app.get("/api/analysis/search")
async def search_analyses(query: str, limit: int = 5):
    """Search past analyses"""
    results = mm.search_similar(query, limit=limit)
    return {"query": query, "results": results}

@app.get("/api/analysis/stats")
async def get_stats():
    """Get memory manager statistics"""
    stats = mm.get_stats()
    return stats

@app.post("/api/session/{session_id}")
async def update_session(session_id: str, data: dict):
    """Update session state"""
    success = mm.update_session(session_id, data)
    if success:
        return {"status": "success", "session_id": session_id}
    raise HTTPException(status_code=500, detail="Failed to update session")
```

### 4. Session Management

Track user sessions and analysis state:

```python
from storage import get_memory_manager

mm = get_memory_manager()

# Start a session
session_id = "user_123_session"
session_data = {
    "user_id": "user_123",
    "started_at": datetime.utcnow().isoformat(),
    "active_analysis": "NVDA_merger",
    "preferences": {"output_format": "pdf"}
}
mm.update_session(session_id, session_data, ttl=7200)  # 2 hour session

# Later, retrieve session state
current_session = mm.get_session(session_id)
if current_session:
    print(f"User preferences: {current_session['preferences']}")

# Clean up
mm.delete_session(session_id)
```

### 5. Analysis History & Retrieval

Query past analyses:

```python
from storage import get_memory_manager

mm = get_memory_manager()

# Get all analyses for a ticker
nvda_analyses = mm.get_history(ticker="NVDA", limit=10)

# Get analyses from a specific session
session_analyses = mm.get_history(session_id="session_123", limit=5)

# Search semantically (uses ChromaDB if available, falls back to text search)
similar = mm.search_similar("NVDA merger with PLTR", limit=5)

# Get statistics
stats = mm.get_stats()
print(f"Total analyses: {stats['total_analyses']}")
print(f"Unique tickers: {stats['unique_tickers']}")
```

## Advanced Usage

### Custom Data Models

Extend the `AnalysisMemory` model for your specific needs:

```python
from storage.memory_manager import AnalysisMemory
from pydantic import Field
from typing import List

class MergerAnalysisMemory(AnalysisMemory):
    """Extended memory for merger analyses"""
    target_ticker: str
    synergies: float
    valuation_methods: List[str]
    confidence_score: float = Field(ge=0.0, le=1.0)
    
    class Config:
        extra = "allow"

# Use it
memory = MergerAnalysisMemory(
    session_id="session_123",
    ticker="NVDA",
    target_ticker="PLTR",
    synergies=1_000_000_000,
    valuation_methods=["DCF", "CCA", "LBO"],
    confidence_score=0.85,
    context={"analysis_date": "2025-11-06"},
    results={"recommendation": "favorable"}
)

mm.store_analysis(memory)
```

### Maintenance Tasks

```python
from storage import get_memory_manager

mm = get_memory_manager()

# Clear old analyses (older than 7 days)
deleted_count = mm.clear_old_sessions(days=7)
print(f"Cleaned up {deleted_count} old analyses")

# Get statistics for monitoring
stats = mm.get_stats()
if stats['total_analyses'] > 10000:
    print("Consider archiving old analyses")
```

## Migration from Cognee

If you have existing code using Cognee, here's how to migrate:

```python
# OLD (Cognee)
from storage.cognee_adapter import CogneeAdapter

adapter = CogneeAdapter()
await adapter.cognify(text)
results = await adapter.search(query)

# NEW (MemoryManager)
from storage import get_memory_manager, AnalysisMemory

mm = get_memory_manager()

# Store structured data
memory = AnalysisMemory(
    session_id="session_123",
    ticker="NVDA",
    context={"type": "text_analysis"},
    results={"text": text, "insights": insights}
)
mm.store_analysis(memory)

# Search
results = mm.search_similar(query, limit=5)
```

## Performance Tips

1. **Use the global instance** (`get_memory_manager()`) to reuse connections
2. **Batch operations** when storing multiple analyses
3. **Set appropriate session TTLs** based on your use case
4. **Use ChromaDB** for semantic search when available
5. **Regular cleanup** of old analyses to maintain performance

## Troubleshooting

### Redis Not Available
The memory manager gracefully handles Redis unavailability:
```python
mm = get_memory_manager()
# Will log warning: "Redis not available"
# Session methods will return False/None but won't crash
```

### ChromaDB Not Available
Falls back to DuckDB text search automatically:
```python
results = mm.search_similar("query")
# Will log warning: "ChromaDB not available, falling back to text search"
# Still returns results using DuckDB LIKE queries
```

### Database Connection Issues
```python
try:
    mm = get_memory_manager()
except Exception as e:
    logger.error(f"Failed to initialize memory manager: {e}")
    # Handle gracefully
```

## Complete Example

Here's a complete workflow example:

```python
from storage import get_memory_manager, AnalysisMemory
from datetime import datetime

# Initialize
mm = get_memory_manager()
session_id = f"user_analyst_{datetime.utcnow().timestamp()}"

# Store session state
mm.update_session(session_id, {
    "user": "analyst_1",
    "started_at": datetime.utcnow().isoformat(),
    "analysis_queue": ["NVDA", "PLTR", "TSLA"]
})

# Run and store multiple analyses
for ticker in ["NVDA", "PLTR"]:
    # Your analysis logic
    results = run_analysis(ticker)
    
    # Store in memory
    memory = AnalysisMemory(
        session_id=session_id,
        ticker=ticker,
        context={
            "analysis_type": "valuation",
            "methods": ["DCF", "CCA"],
            "analyst": "analyst_1"
        },
        results=results,
        metadata={
            "duration_seconds": 45.2,
            "data_sources": ["FMP", "SEC"]
        }
    )
    mm.store_analysis(memory)

# Retrieve session analyses
session_analyses = mm.get_history(session_id=session_id)
print(f"Completed {len(session_analyses)} analyses")

# Search across all analyses
merger_insights = mm.search_similar("merger synergies", limit=10)

# Get statistics
stats = mm.get_stats()
print(f"Platform stats: {stats}")

# Cleanup
mm.delete_session(session_id)
mm.close()
```

## Next Steps

1. ✅ Memory Manager is installed and working
2. Update your agents to use `MemoryManager`
3. Add memory storage to your analysis workflows
4. Create API endpoints for history/search
5. Set up periodic cleanup tasks
6. Monitor statistics for performance

## Support

- Full documentation: `MEMORY_ALTERNATIVES_RECOMMENDATION.md`
- Code examples: `storage/memory_manager.py`
- Test examples: `test_memory_manager.py`
