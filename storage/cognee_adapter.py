"""
Cognee Knowledge Graph Adapter
Integrates Cognee (open-source knowledge graph) for memory and graph storage
GitHub: https://github.com/topoteretes/cognee
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from loguru import logger

try:
    import cognee
    COGNEE_AVAILABLE = True
except ImportError:
    COGNEE_AVAILABLE = False
    logger.warning("Cognee not available. Install with: pip install cognee")

from config.settings import get_settings
from config.schemas import CogneeNode, CogneeEdge


class CogneeAdapter:
    """Adapter for Cognee knowledge graph integration"""
    
    def __init__(self):
        """
        Initialize Cognee adapter
        
        Cognee is open-source and doesn't require API keys!
        Just install via pip: pip install cognee
        """
        settings = get_settings()
        
        if not COGNEE_AVAILABLE:
            logger.error("Cognee is not installed. Please install: pip install cognee")
            self.enabled = False
            return
        
        self.enabled = settings.cognee_enabled
        
        if self.enabled:
            try:
                # Initialize Cognee (newer version doesn't need set_logging_level)
                logger.info("Cognee adapter initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Cognee: {str(e)}")
                self.enabled = False
    
    async def add_node(
        self,
        node_id: str,
        node_type: str,
        properties: Dict[str, Any],
        embedding: Optional[List[float]] = None
    ) -> CogneeNode:
        """
        Add a node to the knowledge graph
        
        Args:
            node_id: Unique node identifier
            node_type: Type of node (Filing, Company, Transaction, etc.)
            properties: Node properties/attributes
            embedding: Optional vector embedding
            
        Returns:
            CogneeNode object
        """
        if not self.enabled:
            logger.warning("Cognee is disabled")
            return None
        
        node = CogneeNode(
            node_id=node_id,
            node_type=node_type,
            properties=properties,
            embedding=embedding,
            created_at=datetime.utcnow()
        )
        
        try:
            # Add to Cognee
            await cognee.add(json.dumps({
                "id": node_id,
                "type": node_type,
                "data": properties
            }))
            
            logger.debug(f"Added node: {node_id} ({node_type})")
            return node
            
        except Exception as e:
            logger.error(f"Error adding node to Cognee: {str(e)}")
            return None
    
    async def add_edge(
        self,
        edge_id: str,
        source_node_id: str,
        target_node_id: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None,
        weight: Optional[float] = None
    ) -> CogneeEdge:
        """
        Add an edge (relationship) between two nodes
        
        Args:
            edge_id: Unique edge identifier
            source_node_id: Source node ID
            target_node_id: Target node ID
            relationship_type: Type of relationship (supports, contradicts, etc.)
            properties: Optional edge properties
            weight: Optional relationship weight/strength
            
        Returns:
            CogneeEdge object
        """
        if not self.enabled:
            logger.warning("Cognee is disabled")
            return None
        
        edge = CogneeEdge(
            edge_id=edge_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            relationship_type=relationship_type,
            properties=properties,
            weight=weight,
            created_at=datetime.utcnow()
        )
        
        try:
            # Add relationship to Cognee
            await cognee.add(json.dumps({
                "id": edge_id,
                "source": source_node_id,
                "target": target_node_id,
                "type": relationship_type,
                "properties": properties or {},
                "weight": weight
            }))
            
            logger.debug(f"Added edge: {source_node_id} -> {target_node_id} ({relationship_type})")
            return edge
            
        except Exception as e:
            logger.error(f"Error adding edge to Cognee: {str(e)}")
            return None
    
    async def store_filing(
        self,
        filing_id: str,
        cik: str,
        symbol: str,
        filing_data: Dict[str, Any]
    ) -> CogneeNode:
        """
        Store SEC filing in knowledge graph
        
        Args:
            filing_id: Unique filing identifier
            cik: Company CIK
            symbol: Ticker symbol
            filing_data: Filing metadata and content
            
        Returns:
            CogneeNode for the filing
        """
        properties = {
            "cik": cik,
            "symbol": symbol,
            **filing_data
        }
        
        return await self.add_node(
            node_id=filing_id,
            node_type="Filing",
            properties=properties
        )
    
    async def store_company(
        self,
        symbol: str,
        company_data: Dict[str, Any]
    ) -> CogneeNode:
        """
        Store company information in knowledge graph
        
        Args:
            symbol: Ticker symbol
            company_data: Company profile and metrics
            
        Returns:
            CogneeNode for the company
        """
        return await self.add_node(
            node_id=f"company_{symbol}",
            node_type="Company",
            properties=company_data
        )
    
    async def store_transaction(
        self,
        transaction_id: str,
        transaction_data: Dict[str, Any]
    ) -> CogneeNode:
        """
        Store M&A transaction in knowledge graph
        
        Args:
            transaction_id: Unique transaction identifier
            transaction_data: Transaction details
            
        Returns:
            CogneeNode for the transaction
        """
        return await self.add_node(
            node_id=transaction_id,
            node_type="Transaction",
            properties=transaction_data
        )
    
    async def link_filing_to_company(
        self,
        filing_id: str,
        symbol: str
    ) -> CogneeEdge:
        """
        Create relationship between filing and company
        
        Args:
            filing_id: Filing identifier
            symbol: Company symbol
            
        Returns:
            CogneeEdge for the relationship
        """
        return await self.add_edge(
            edge_id=f"filing_{filing_id}_company_{symbol}",
            source_node_id=filing_id,
            target_node_id=f"company_{symbol}",
            relationship_type="belongs_to",
            weight=1.0
        )
    
    async def search(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge graph using Cognee
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching nodes/documents
        """
        if not self.enabled:
            logger.warning("Cognee is disabled")
            return []
        
        try:
            # Search using Cognee
            results = await cognee.search(query, limit=limit)
            logger.info(f"Search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error searching Cognee: {str(e)}")
            return []
    
    async def cognify(
        self,
        text: str or List[str]
    ) -> bool:
        """
        Process text/documents through Cognee's cognify function
        This creates knowledge graph from unstructured text
        
        Args:
            text: Text string or list of texts to process
            
        Returns:
            Success status
        """
        if not self.enabled:
            logger.warning("Cognee is disabled")
            return False
        
        try:
            await cognee.add(text)
            await cognee.cognify()
            logger.info("Successfully cognified text")
            return True
            
        except Exception as e:
            logger.error(f"Error cognifying text: {str(e)}")
            return False
    
    async def reset(self) -> bool:
        """
        Reset Cognee knowledge graph (use with caution!)
        
        Returns:
            Success status
        """
        if not self.enabled:
            logger.warning("Cognee is disabled")
            return False
        
        try:
            await cognee.prune.prune_data()
            await cognee.prune.prune_system()
            logger.info("Cognee graph reset")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting Cognee: {str(e)}")
            return False


# Example usage
async def example_usage():
    """Example of how to use Cognee adapter"""
    
    adapter = CogneeAdapter()
    
    # Store a company
    await adapter.store_company(
        symbol="AAPL",
        company_data={
            "name": "Apple Inc.",
            "sector": "Technology",
            "market_cap": 2800000000000
        }
    )
    
    # Store a filing
    await adapter.store_filing(
        filing_id="0000320193-24-000010",
        cik="0000320193",
        symbol="AAPL",
        filing_data={
            "filing_type": "10-K",
            "filing_date": "2024-01-26",
            "items": ["Item 7", "Item 7A", "Item 8"]
        }
    )
    
    # Link them
    await adapter.link_filing_to_company(
        filing_id="0000320193-24-000010",
        symbol="AAPL"
    )
    
    # Process some MD&A text
    await adapter.cognify(
        "Apple's revenue grew 15% year-over-year driven by strong iPhone sales..."
    )
    
    # Search
    results = await adapter.search("Apple revenue growth")
    print(f"Found {len(results)} results")
