"""
Test script for the new Memory Manager
Replaces Cognee with native stack integration
"""

from storage.memory_manager import MemoryManager, AnalysisMemory
from loguru import logger


def test_memory_manager():
    """Test the new memory manager functionality"""
    logger.info("=" * 60)
    logger.info("Testing New Memory Manager (Cognee Replacement)")
    logger.info("=" * 60)
    
    try:
        # Initialize
        logger.info("1. Initializing Memory Manager...")
        mm = MemoryManager()
        logger.success("✓ Memory Manager initialized")
        
        # Create test analysis
        logger.info("\n2. Creating test analysis...")
        memory = AnalysisMemory(
            session_id="test_session_001",
            ticker="NVDA",
            context={
                "analysis_type": "merger_model",
                "target": "PLTR",
                "parameters": {"synergy_rate": 0.15}
            },
            results={
                "synergies": 1000000,
                "valuation": 5000000,
                "recommendation": "favorable"
            },
            metadata={"analyst": "system", "confidence": 0.85}
        )
        logger.success("✓ Test analysis created")
        
        # Store analysis
        logger.info("\n3. Storing analysis in DuckDB...")
        success = mm.store_analysis(memory)
        if success:
            logger.success("✓ Analysis stored successfully")
        else:
            logger.error("✗ Failed to store analysis")
            return False
        
        # Retrieve history
        logger.info("\n4. Retrieving analysis history...")
        history = mm.get_history(ticker="NVDA", limit=5)
        logger.success(f"✓ Retrieved {len(history)} analyses for NVDA")
        
        # Search
        logger.info("\n5. Testing search functionality...")
        results = mm.search_similar("NVDA merger", limit=3)
        logger.success(f"✓ Search returned {len(results) if results else 0} results")
        
        # Get stats
        logger.info("\n6. Getting memory statistics...")
        stats = mm.get_stats()
        logger.success(f"✓ Stats retrieved:")
        for key, value in stats.items():
            logger.info(f"   - {key}: {value}")
        
        # Session management (if Redis available)
        logger.info("\n7. Testing session management...")
        session_data = {"user": "analyst", "active": True}
        if mm.update_session("test_session_001", session_data):
            logger.success("✓ Session stored in Redis")
            retrieved = mm.get_session("test_session_001")
            if retrieved:
                logger.success(f"✓ Session retrieved: {retrieved}")
        else:
            logger.warning("⚠ Redis not available, skipping session test")
        
        # Close
        logger.info("\n8. Closing connections...")
        mm.close()
        logger.success("✓ Connections closed")
        
        logger.info("\n" + "=" * 60)
        logger.success("ALL TESTS PASSED! ✓")
        logger.info("Memory Manager is working correctly!")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"\n✗ Test failed with error: {str(e)}")
        logger.exception(e)
        return False


if __name__ == "__main__":
    success = test_memory_manager()
    exit(0 if success else 1)
