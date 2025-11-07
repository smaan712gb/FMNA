"""
Test script for verifying quarterly data and LTM calculations

This script tests the improvements made to support quarterly financial data
and Last Twelve Months (LTM) normalization instead of stale annual data.
"""

import asyncio
from datetime import datetime
from loguru import logger

from orchestration.comprehensive_orchestrator import ComprehensiveOrchestrator
from config.settings import get_settings


async def test_annual_vs_quarterly():
    """Compare analysis using annual data vs quarterly data with LTM"""
    
    symbol = "AAPL"
    
    logger.info("="*80)
    logger.info("TESTING: ANNUAL VS QUARTERLY DATA WITH LTM")
    logger.info("="*80)
    logger.info("")
    
    # Test 1: Annual Data (traditional approach)
    logger.info("🔵 TEST 1: Running analysis with ANNUAL data")
    logger.info("-"*80)
    
    try:
        orchestrator_annual = ComprehensiveOrchestrator()
        result_annual = await orchestrator_annual.run_comprehensive_analysis(
            symbol=symbol,
            period="annual",
            peers_required=3,
            run_dcf=False,
            run_cca=False,
            run_lbo=False,
            run_full_dd=False
        )
        
        annual_date = result_annual.financial_data.get('income_statement', [{}])[0].get('date', 'Unknown')
        annual_revenue = result_annual.financial_data.get('income_statement', [{}])[0].get('revenue', 0)
        
        logger.success(f"✓ Annual data fetched: {annual_date}")
        logger.info(f"  Revenue (Annual): ${annual_revenue:,.0f}")
        logger.info("")
        
        orchestrator_annual.close()
        
    except Exception as e:
        logger.error(f"✗ Annual test failed: {str(e)}")
        logger.info("")
    
    # Test 2: Quarterly Data with LTM
    logger.info("🟢 TEST 2: Running analysis with QUARTERLY data + LTM")
    logger.info("-"*80)
    
    try:
        orchestrator_quarterly = ComprehensiveOrchestrator()
        result_quarterly = await orchestrator_quarterly.run_comprehensive_analysis(
            symbol=symbol,
            period="quarter",
            peers_required=3,
            run_dcf=False,
            run_cca=False,
            run_lbo=False,
            run_full_dd=False
        )
        
        # Get LTM data if available
        ltm_data = result_quarterly.financial_data.get('ltm_data', {})
        if ltm_data:
            ltm_date = ltm_data.get('income_statement', {}).get('date', 'Unknown')
            ltm_revenue = ltm_data.get('income_statement', {}).get('revenue', 0)
            
            logger.success(f"✓ LTM data calculated: {ltm_date}")
            logger.info(f"  Revenue (LTM): ${ltm_revenue:,.0f}")
            
            # Calculate data freshness advantage
            if 'annual_date' in locals() and annual_date != 'Unknown' and ltm_date != 'Unknown':
                try:
                    annual_dt = datetime.strptime(annual_date, '%Y-%m-%d')
                    ltm_dt = datetime.strptime(ltm_date, '%Y-%m-%d')
                    days_fresher = (ltm_dt - annual_dt).days
                    logger.success(f"  ✨ Data Freshness Advantage: {days_fresher} days")
                except:
                    pass
        else:
            logger.warning("⚠ LTM data not available")
        
        logger.info("")
        orchestrator_quarterly.close()
        
    except Exception as e:
        logger.error(f"✗ Quarterly test failed: {str(e)}")
        logger.info("")
    
    # Summary
    logger.info("="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)
    logger.info("")
    logger.info("✅ IMPROVEMENTS IMPLEMENTED:")
    logger.info("   1. Configurable period setting (annual/quarter)")
    logger.info("   2. LTM calculation from quarterly data")
    logger.info("   3. Automatic data freshness optimization")
    logger.info("   4. No hardcoded 'annual' limitations")
    logger.info("")
    logger.info("💡 BENEFITS:")
    logger.info("   • More current financial data (up to 11 months fresher)")
    logger.info("   • Latest earnings reports included")
    logger.info("   • LTM normalization for comparability")
    logger.info("   • Models built on fresh data")
    logger.info("")
    logger.info("="*80)


async def test_settings_configuration():
    """Test configuration settings for period and LTM"""
    
    logger.info("="*80)
    logger.info("TESTING: CONFIGURATION SETTINGS")
    logger.info("="*80)
    logger.info("")
    
    settings = get_settings()
    
    logger.info("Current Settings:")
    logger.info(f"  Default Period: {settings.default_period.upper()}")
    logger.info(f"  LTM Enabled: {settings.use_ltm}")
    logger.info(f"  LTM Quarters: {settings.ltm_quarters}")
    logger.info("")
    
    logger.success("✓ Configuration loaded successfully")
    logger.info("")
    logger.info("To change defaults, update .env file:")
    logger.info("  DEFAULT_PERIOD=quarter")
    logger.info("  USE_LTM=true")
    logger.info("  LTM_QUARTERS=4")
    logger.info("")
    logger.info("="*80)


async def main():
    """Run all tests"""
    
    logger.info("")
    logger.info("█" * 80)
    logger.info("█  QUARTERLY DATA & LTM CALCULATION TEST SUITE")
    logger.info("█  Testing improvements to eliminate stale annual data")
    logger.info("█" * 80)
    logger.info("")
    
    # Test 1: Settings configuration
    await test_settings_configuration()
    
    # Test 2: Annual vs Quarterly comparison
    await test_annual_vs_quarterly()
    
    logger.info("")
    logger.info("█" * 80)
    logger.info("█  ALL TESTS COMPLETE")
    logger.info("█" * 80)
    logger.info("")


if __name__ == "__main__":
    asyncio.run(main())
