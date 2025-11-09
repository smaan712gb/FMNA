"""
Unified Memory Manager - Replaces Cognee
Uses existing infrastructure: Redis, DuckDB, ChromaDB
Integrates seamlessly with LangChain, LangGraph, and Pydantic
"""

from typing import Dict, List, Optional, Any
import json
from datetime import datetime, timedelta
from loguru import logger
from pydantic import BaseModel, Field
import duckdb
from config.settings import get_settings


class AnalysisMemory(BaseModel):
    """Financial analysis memory format"""
    session_id: str
    ticker: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context: Dict[str, Any]
    results: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class MemoryManager:
    """
    Manages all memory/storage needs for financial analysis platform
    
    Features:
    - Session management (Redis)
    - Structured data storage (DuckDB)
    - Semantic search (ChromaDB - optional)
    - LangGraph integration ready
    """
    
    def __init__(self, db_path: str = 'data/fmna.duckdb'):
        """Initialize memory manager with existing infrastructure"""
        settings = get_settings()
        
        # DuckDB for structured financial data (read_write mode allows concurrent access)
        self.db = duckdb.connect(db_path, read_only=False)
        self._init_tables()
        
        # Redis for sessions (lazy load)
        self._redis = None
        self.redis_enabled = True
        
        # ChromaDB for semantic search (lazy load)
        self._chroma = None
        self._collection = None
        self.chroma_enabled = True
        
        logger.info("Memory Manager initialized with DuckDB backend")
    
    def _init_tables(self):
        """Initialize DuckDB tables for analysis history"""
        try:
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS analysis_history (
                    session_id VARCHAR,
                    ticker VARCHAR,
                    timestamp TIMESTAMP,
                    context JSON,
                    results JSON,
                    metadata JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.debug("DuckDB tables initialized")
        except Exception as e:
            logger.warning(f"Table already exists or error: {e}")
    
    @property
    def redis(self):
        """Lazy load Redis connection"""
        if self._redis is None and self.redis_enabled:
            try:
                import redis
                settings = get_settings()
                self._redis = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    db=settings.redis_db,
                    password=settings.redis_password,
                    decode_responses=True
                )
                logger.debug("Redis connection established")
            except Exception as e:
                logger.warning(f"Redis not available: {e}")
                self.redis_enabled = False
        return self._redis
    
    @property
    def chroma(self):
        """Lazy load ChromaDB client"""
        if self._chroma is None and self.chroma_enabled:
            try:
                import chromadb
                self._chroma = chromadb.Client()
                self._collection = self._chroma.get_or_create_collection("financial_analyses")
                logger.debug("ChromaDB connection established")
            except Exception as e:
                logger.warning(f"ChromaDB not available: {e}")
                self.chroma_enabled = False
        return self._chroma
    
    def store_analysis(self, memory: AnalysisMemory) -> bool:
        """
        Store complete financial analysis
        
        Args:
            memory: AnalysisMemory object with analysis data
            
        Returns:
            Success status
        """
        try:
            # Custom JSON encoder for Decimal types
            import decimal
            
            def decimal_default(obj):
                if isinstance(obj, decimal.Decimal):
                    return float(obj)
                raise TypeError
            
            # Store in DuckDB for structured queries with Decimal handling
            self.db.execute("""
                INSERT INTO analysis_history 
                (session_id, ticker, timestamp, context, results, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                memory.session_id,
                memory.ticker,
                memory.timestamp,
                json.dumps(memory.context, default=decimal_default),
                json.dumps(memory.results, default=decimal_default),
                json.dumps(memory.metadata or {}, default=decimal_default)
            ))
            
            # Store in ChromaDB for semantic search (if available)
            if self.chroma_enabled and self._collection is not None:
                try:
                    doc_text = f"Analysis for {memory.ticker}: {json.dumps(memory.results)}"
                    self._collection.add(
                        documents=[doc_text],
                        ids=[f"{memory.ticker}_{memory.timestamp.isoformat()}"],
                        metadatas=[{"ticker": memory.ticker, "session_id": memory.session_id}]
                    )
                except Exception as e:
                    logger.warning(f"ChromaDB storage failed: {e}")
            
            logger.info(f"Stored analysis for {memory.ticker} in session {memory.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing analysis: {e}")
            return False
    
    def get_history(self, ticker: Optional[str] = None, 
                   session_id: Optional[str] = None,
                   limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get analysis history from DuckDB
        
        Args:
            ticker: Filter by ticker (optional)
            session_id: Filter by session (optional)
            limit: Maximum results to return
            
        Returns:
            List of analysis records
        """
        try:
            query = "SELECT * FROM analysis_history WHERE 1=1"
            params = []
            
            if ticker:
                query += " AND ticker = ?"
                params.append(ticker)
            
            if session_id:
                query += " AND session_id = ?"
                params.append(session_id)
            
            query += f" ORDER BY timestamp DESC LIMIT {limit}"
            
            result = self.db.execute(query, params).fetchall()
            columns = [desc[0] for desc in self.db.description]
            
            return [dict(zip(columns, row)) for row in result]
            
        except Exception as e:
            logger.error(f"Error retrieving history: {e}")
            return []
    
    def _extract_ticker(self, query: str) -> Optional[str]:
        """Extract potential ticker symbol from query"""
        import re
        
        # Method 1: Look for explicit ticker patterns (2-5 uppercase letters)
        words = query.upper().split()
        for word in words:
            # Remove punctuation
            clean_word = ''.join(c for c in word if c.isalpha())
            if 2 <= len(clean_word) <= 5:
                return clean_word
        
        # Method 2: Look for common ticker patterns in mixed case
        # Match words like "PLTR", "pltr", "Palantir", "AAPL" etc
        ticker_pattern = r'\b([A-Z]{2,5})\b'
        matches = re.findall(ticker_pattern, query.upper())
        if matches:
            return matches[0]
        
        # Method 3: Extract from common phrases
        # "we ran pltr" → "pltr"
        # "analyze aapl" → "aapl"
        common_phrases = [
            r'ran\s+(\w{2,5})\b',
            r'analyze\s+(\w{2,5})\b',
            r'analysis\s+for\s+(\w{2,5})\b',
            r'data\s+for\s+(\w{2,5})\b',
            r'about\s+(\w{2,5})\b',
        ]
        
        for pattern in common_phrases:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        return None
    
    def get_relevant_context(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get relevant context for a query from stored analyses and data
        
        This is the main method multi-agents use to access historical data,
        previous analyses, financial results, and any stored context.
        
        Args:
            query: User query or context request
            limit: Maximum number of relevant items to return
            
        Returns:
            List of relevant context items (analyses, data, results)
        """
        try:
            # Extract potential ticker from query
            ticker = self._extract_ticker(query)
            
            # First try semantic search if available
            if self.chroma_enabled and self._collection is not None:
                try:
                    chroma_results = self._collection.query(
                        query_texts=[query],
                        n_results=limit
                    )
                    
                    # Extract relevant information from ChromaDB results
                    context_items = []
                    if chroma_results and 'documents' in chroma_results:
                        for i, doc in enumerate(chroma_results['documents'][0]):
                            metadata = chroma_results['metadatas'][0][i] if 'metadatas' in chroma_results else {}
                            context_items.append({
                                'content': doc,
                                'metadata': metadata,
                                'source': 'semantic_search'
                            })
                    
                    if context_items:
                        logger.debug(f"Found {len(context_items)} items via semantic search")
                        return context_items
                except Exception as e:
                    logger.warning(f"Semantic search failed: {e}, falling back to SQL search")
            
            # Strategy 1: Direct ticker match (most accurate)
            if ticker:
                result = self.db.execute("""
                    SELECT 
                        session_id,
                        ticker,
                        timestamp,
                        context,
                        results,
                        metadata
                    FROM analysis_history 
                    WHERE UPPER(ticker) = UPPER(?)
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (ticker, limit)).fetchall()
                
                if result:
                    columns = [desc[0] for desc in self.db.description]
                    context_items = self._parse_db_results(result, columns)
                    logger.debug(f"Found {len(context_items)} items via direct ticker match: {ticker}")
                    return context_items
            
            # Strategy 2: Keyword search in all text fields
            search_term = f"%{query}%"
            result = self.db.execute("""
                SELECT 
                    session_id,
                    ticker,
                    timestamp,
                    context,
                    results,
                    metadata
                FROM analysis_history 
                WHERE 
                    LOWER(ticker) LIKE LOWER(?)
                    OR LOWER(CAST(context AS VARCHAR)) LIKE LOWER(?)
                    OR LOWER(CAST(results AS VARCHAR)) LIKE LOWER(?)
                    OR LOWER(CAST(metadata AS VARCHAR)) LIKE LOWER(?)
                ORDER BY timestamp DESC
                LIMIT ?
            """, (search_term, search_term, search_term, search_term, limit)).fetchall()
            
            columns = [desc[0] for desc in self.db.description]
            context_items = self._parse_db_results(result, columns)
            
            logger.debug(f"Found {len(context_items)} items via keyword search")
            return context_items
            
        except Exception as e:
            logger.error(f"Error getting relevant context: {e}")
            return []
    
    def _parse_db_results(self, results, columns) -> List[Dict[str, Any]]:
        """Parse database results and convert JSON strings to objects"""
        context_items = []
        
        for row in results:
            row_dict = dict(zip(columns, row))
            
            # Parse JSON strings back to objects
            if row_dict.get('context'):
                try:
                    row_dict['context'] = json.loads(row_dict['context']) if isinstance(row_dict['context'], str) else row_dict['context']
                except:
                    pass
            
            if row_dict.get('results'):
                try:
                    row_dict['results'] = json.loads(row_dict['results']) if isinstance(row_dict['results'], str) else row_dict['results']
                except:
                    pass
            
            if row_dict.get('metadata'):
                try:
                    row_dict['metadata'] = json.loads(row_dict['metadata']) if isinstance(row_dict['metadata'], str) else row_dict['metadata']
                except:
                    pass
            
            context_items.append({
                'content': row_dict,
                'source': 'database_search',
                'ticker': row_dict.get('ticker', 'Unknown'),
                'timestamp': str(row_dict.get('timestamp', '')),
                'session_id': row_dict.get('session_id', '')
            })
        
        return context_items
    
    def store_context(self, context_type: str, data: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store arbitrary context data (Q&A interactions, custom data, etc.)
        
        This allows multi-agents to store any type of context or data
        that might be relevant for future queries.
        
        Args:
            context_type: Type of context (e.g., 'qa_interaction', 'private_company_data', 'custom')
            data: The data to store (will be JSON serialized)
            metadata: Optional metadata about the context
            
        Returns:
            Success status
        """
        try:
            # Create a synthetic session ID for this context
            session_id = metadata.get('session_id', f"context_{datetime.utcnow().timestamp()}")
            ticker = metadata.get('ticker', metadata.get('symbol', 'GENERAL'))
            
            # Store in DuckDB
            self.db.execute("""
                INSERT INTO analysis_history 
                (session_id, ticker, timestamp, context, results, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                ticker,
                datetime.utcnow(),
                json.dumps({'type': context_type, 'data': data}),
                json.dumps({}),  # Empty results for context storage
                json.dumps(metadata or {})
            ))
            
            # Store in ChromaDB for semantic search if available
            if self.chroma_enabled and self._collection is not None:
                try:
                    doc_text = f"{context_type}: {json.dumps(data)}"
                    self._collection.add(
                        documents=[doc_text],
                        ids=[f"{context_type}_{session_id}_{datetime.utcnow().isoformat()}"],
                        metadatas=[{
                            "type": context_type, 
                            "ticker": ticker,
                            "session_id": session_id,
                            **(metadata or {})
                        }]
                    )
                except Exception as e:
                    logger.warning(f"ChromaDB storage failed for context: {e}")
            
            logger.debug(f"Stored context of type '{context_type}' for {ticker}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing context: {e}")
            return False
    
    def search_similar(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search past analyses semantically using ChromaDB
        
        Args:
            query: Search query
            limit: Number of results
            
        Returns:
            List of similar analyses
        """
        if not self.chroma_enabled or self._collection is None:
            logger.warning("ChromaDB not available, falling back to text search")
            return self._fallback_search(query, limit)
        
        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=limit
            )
            return results
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    def _fallback_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Fallback text search using DuckDB"""
        try:
            result = self.db.execute("""
                SELECT * FROM analysis_history 
                WHERE ticker LIKE ? OR CAST(results AS VARCHAR) LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", limit)).fetchall()
            
            columns = [desc[0] for desc in self.db.description]
            return [dict(zip(columns, row)) for row in result]
        except Exception as e:
            logger.error(f"Fallback search failed: {e}")
            return []
    
    # ===== Session Management (Redis) =====
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session state from Redis"""
        if not self.redis_enabled or self.redis is None:
            return None
        
        try:
            data = self.redis.get(f"session:{session_id}")
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None
    
    def update_session(self, session_id: str, data: Dict[str, Any], 
                      ttl: int = 3600) -> bool:
        """
        Update session state in Redis
        
        Args:
            session_id: Session identifier
            data: Session data
            ttl: Time to live in seconds (default 1 hour)
            
        Returns:
            Success status
        """
        if not self.redis_enabled or self.redis is None:
            return False
        
        try:
            self.redis.setex(
                f"session:{session_id}",
                ttl,
                json.dumps(data)
            )
            logger.debug(f"Updated session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating session: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session from Redis"""
        if not self.redis_enabled or self.redis is None:
            return False
        
        try:
            self.redis.delete(f"session:{session_id}")
            logger.debug(f"Deleted session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False
    
    # ===== Utility Methods =====
    
    def clear_old_sessions(self, days: int = 7) -> int:
        """Clear sessions older than specified days"""
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            result = self.db.execute("""
                DELETE FROM analysis_history 
                WHERE timestamp < ?
            """, (cutoff,))
            
            deleted = result.fetchone()[0] if result else 0
            logger.info(f"Cleared {deleted} old analysis records")
            return deleted
        except Exception as e:
            logger.error(f"Error clearing old sessions: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory manager statistics"""
        try:
            stats = {
                "total_analyses": self.db.execute(
                    "SELECT COUNT(*) FROM analysis_history"
                ).fetchone()[0],
                "unique_tickers": self.db.execute(
                    "SELECT COUNT(DISTINCT ticker) FROM analysis_history"
                ).fetchone()[0],
                "unique_sessions": self.db.execute(
                    "SELECT COUNT(DISTINCT session_id) FROM analysis_history"
                ).fetchone()[0],
                "redis_enabled": self.redis_enabled,
                "chroma_enabled": self.chroma_enabled
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    def close(self):
        """Close all connections"""
        try:
            if self.db:
                self.db.close()
            if self._redis:
                self._redis.close()
            logger.debug("Memory manager connections closed")
        except Exception as e:
            logger.error(f"Error closing connections: {e}")


# Global instance (optional - can be instantiated per request)
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """Get or create global memory manager instance"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager


# Example usage
if __name__ == "__main__":
    # Initialize
    mm = MemoryManager()
    
    # Store an analysis
    memory = AnalysisMemory(
        session_id="test_session_001",
        ticker="NVDA",
        context={"analysis_type": "merger_model"},
        results={"synergies": 1000000, "valuation": 5000000}
    )
    
    mm.store_analysis(memory)
    
    # Retrieve history
    history = mm.get_history(ticker="NVDA")
    print(f"Found {len(history)} analyses for NVDA")
    
    # Get stats
    stats = mm.get_stats()
    print(f"Memory Manager Stats: {stats}")
    
    # Close
    mm.close()

    
    def store_ai_classification(
        self,
        ticker: str,
        company_profile: Any,
        weighted_value: float,
        breakdown: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> bool:
        """
        Store AI classification and valuation weighting
        
        Args:
            ticker: Stock ticker
            company_profile: CompanyProfile from AI engine
            weighted_value: AI-weighted fair value
            breakdown: Methodology breakdown
            session_id: Optional session ID
            
        Returns:
            Success status
        """
        try:
            # Store in context for AI QA retrieval
            ai_data = {
                'company_type': company_profile.company_type.value,
                'development_stage': company_profile.development_stage.value,
                'key_value_drivers': company_profile.key_value_drivers,
                'classification_confidence': company_profile.classification_confidence,
                'reasoning': company_profile.reasoning,
                'valuation_methodologies': [
                    {
                        'method': m.method_name,
                        'weight': m.weight,
                        'reason': m.reason,
                        'focus_multiples': m.focus_multiples
                    }
                    for m in company_profile.valuation_methodologies if m.use
                ],
                'ai_weighted_value': weighted_value,
                'methodology_breakdown': breakdown
            }
            
            self.store_context(
                context_type='ai_classification',
                data=ai_data,
                metadata={
                    'ticker': ticker,
                    'session_id': session_id or f'ai_{ticker}_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}',
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"✓ Stored AI classification for {ticker}")
            logger.info(f"  Type: {company_profile.company_type.value}")
            logger.info(f"  Stage: {company_profile.development_stage.value}")
            logger.info(f"  AI Fair Value: ${weighted_value:.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store AI classification: {e}")
            return False
