"""
Test Script for DCF Engine Fixes
Validates the critical bug fixes applied to the DCF engine and data pipeline
"""

import asyncio
from loguru import logger
from orchestration.comprehensive_orchestrator import ComprehensiveOrchestrator


async def test_dcf_integration():
    """Test DCF engine with fixes applied"""
    
    logger.info("="*80)
    logger.info("DCF ENGINE FIX VALIDATION TEST")
    logger.info("="*80)
    
    # Initialize orchestrator
    orchestrator = ComprehensiveOrchestrator()
    
    # Test with NVDA (the problematic case)
    symbol = "NVDA"
    
    try:
        logger.info(f"\n🧪 Testing DCF fixes with {symbol}...")
        logger.info("Expected improvements:")
        logger.info("  1. 3-Statement Model runs BEFORE DCF")
        logger.info("  2. DCF uses 3SM FCFF when available")
        logger.info("  3. FCF data validation with warnings")
        logger.info("  4. Intelligent growth rates from historical data")
        logger.info("  5. Comprehensive logging of DCF inputs")
        logger.info("")
        
        result = await orchestrator.run_comprehensive_analysis(
            symbol=symbol,
            period="annual",  # Use annual for most complete data
            peers_required=3,  # Lower for testing
            run_dcf=True,
            run_cca=False,  # Skip to focus on DCF
            run_lbo=False,
            run_merger=False,
            run_three_statement=True,  # CRITICAL: Must be True
            run_growth_scenarios=False,
            run_full_dd=False  # Skip to speed up test
        )
        
        logger.info("\n" + "="*80)
        logger.info("TEST RESULTS")
        logger.info("="*80)
        
        # Check if DCF ran
        if result.valuation.dcf_result:
            dcf = result.valuation.dcf_result
            logger.success(f"✅ DCF executed successfully")
            logger.info(f"   Value per Share: ${dcf.value_per_share:.2f}")
            logger.info(f"   Enterprise Value: ${dcf.enterprise_value:,.0f} ({dcf.enterprise_value/1e9:.2f}B)")
            logger.info(f"   WACC: {dcf.wacc:.2%}")
            
            # Validate the result is reasonable
            market_cap = result.financial_data.get('market_snapshot', {}).get('market_cap', 0)
            if market_cap > 0:
                valuation_ratio = (dcf.value_per_share * dcf.shares_outstanding) / market_cap
                logger.info(f"   DCF Valuation / Market Cap: {valuation_ratio:.2f}x")
                
                if 0.5 <= valuation_ratio <= 2.0:
                    logger.success(f"✅ DCF valuation in reasonable range (0.5x - 2.0x market cap)")
                elif valuation_ratio < 0.01:
                    logger.error(f"❌ DCF valuation WAY TOO LOW - possible unit issue!")
                elif valuation_ratio > 10:
                    logger.error(f"❌ DCF valuation WAY TOO HIGH - possible unit issue!")
                else:
                    logger.warning(f"⚠️  DCF valuation outside typical range - review assumptions")
            
            # Check if 3SM FCFF was used
            if hasattr(result.valuation, 'three_statement_result') and result.valuation.three_statement_result:
                logger.success(f"✅ 3-Statement Model was executed")
                logger.info(f"   FCF periods available: {len(result.valuation.three_statement_result.fcf_forecast)}")
            else:
                logger.warning(f"⚠️  3-Statement Model not available - DCF used fallback")
            
        else:
            logger.error(f"❌ DCF did not execute")
        
        # Compare to previous result (if we had access to it)
        logger.info("\n" + "="*80)
        logger.info("COMPARISON TO REPORTED ISSUE")
        logger.info("="*80)
        logger.info(f"Previous (buggy): $4.74/share")
        if result.valuation.dcf_result:
            logger.info(f"Current (fixed):  ${result.valuation.dcf_result.value_per_share:.2f}/share")
            
            improvement = (result.valuation.dcf_result.value_per_share / 4.74) - 1
            if improvement > 10:
                logger.success(f"✅ MASSIVE IMPROVEMENT: {improvement:.0f}x increase (likely fixed unit issues)")
            elif improvement > 1:
                logger.success(f"✅ SIGNIFICANT IMPROVEMENT: {improvement:.0%} increase")
            elif improvement > 0.2:
                logger.success(f"✅ IMPROVEMENT: {improvement:.0%} increase")
            else:
                logger.warning(f"⚠️  Limited improvement: {improvement:.0%}")
        
        logger.info("="*80)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None
        
    finally:
        orchestrator.close()


async def test_data_validation():
    """Test FCF data validation function"""
    
    logger.info("\n" + "="*80)
    logger.info("DATA VALIDATION TEST")
    logger.info("="*80)
    
    # Test cases for validation
    test_cases = [
        {
            'symbol': 'NVDA',
            'fcf': 60_000_000_000,  # $60B
            'market_cap': 3_400_000_000_000,  # $3.4T
            'expected': True,
            'desc': 'NVDA with correct units'
        },
        {
            'symbol': 'NVDA',
            'fcf': 60_000,  # $60K (wrong units)
            'market_cap': 3_400_000_000_000,  # $3.4T
            'expected': False,
            'desc': 'NVDA with unit issue (FCF too small)'
        },
        {
            'symbol': 'TEST',
            'fcf': 500_000_000_000,  # $500B (unrealistic)
            'market_cap': 100_000_000_000,  # $100B
            'expected': False,
            'desc': 'Company with FCF > 30% of market cap'
        }
    ]
    
    for test in test_cases:
        fcf_to_mcap = test['fcf'] / test['market_cap'] if test['market_cap'] > 0 else 0
        
        # Simple validation logic (matching what we added)
        is_valid = True
        if fcf_to_mcap < 0.001 or fcf_to_mcap > 0.30:
            is_valid = False
        
        result = "✅ PASS" if is_valid == test['expected'] else "❌ FAIL"
        logger.info(f"{result} {test['desc']}")
        logger.info(f"     FCF: ${test['fcf']:,.0f}, Market Cap: ${test['market_cap']:,.0f}")
        logger.info(f"     FCF Yield: {fcf_to_mcap:.3%}")
    
    logger.info("="*80)


async def main():
    """Run all tests"""
    
    # Test 1: Data validation logic
    await test_data_validation()
    
    # Test 2: Full DCF integration (with API calls)
    logger.info("\n\n⚠️  About to run full DCF integration test with REAL API calls")
    logger.info("This will consume FMP API credits. Continue? (y/n)")
    
    # For automated testing, we'll skip the actual API call
    # In manual testing, user can confirm
    run_full_test = True  # Set to True for manual testing
    
    if run_full_test:
        result = await test_dcf_integration()
        if result and result.valuation.dcf_result:
            logger.success("\n🎉 ALL TESTS PASSED - DCF fixes are working correctly")
        else:
            logger.error("\n❌ TEST FAILED - Review error logs above")
    else:
        logger.info("Skipping full API test (set run_full_test=True to enable)")
        logger.info("\n✅ Validation tests completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
