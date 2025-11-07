"""
Test script to verify Cognee configuration is working properly
"""
import asyncio
from loguru import logger
from storage.cognee_adapter import CogneeAdapter


async def test_cognee_basic():
    """Test basic Cognee functionality"""
    logger.info("Testing Cognee configuration...")
    
    try:
        # Initialize Cognee adapter
        adapter = CogneeAdapter()
        
        if not adapter.enabled:
            logger.error("Cognee is not enabled")
            return False
        
        logger.info("Cognee adapter initialized successfully!")
        
        # Try to add some simple text
        test_text = "This is a test document for Cognee."
        result = await adapter.cognify(test_text)
        
        if result:
            logger.success("✓ Cognee cognify test passed!")
            return True
        else:
            logger.error("✗ Cognee cognify test failed")
            return False
            
    except Exception as e:
        logger.error(f"Error testing Cognee: {str(e)}")
        logger.exception(e)
        return False


async def main():
    """Main test function"""
    logger.info("=" * 60)
    logger.info("Testing Cognee Configuration Fix")
    logger.info("=" * 60)
    
    success = await test_cognee_basic()
    
    if success:
        logger.success("All tests passed! ✓")
        logger.info("Cognee is now properly configured with DeepSeek (custom provider)")
    else:
        logger.error("Tests failed. Please check the error messages above.")
    
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
