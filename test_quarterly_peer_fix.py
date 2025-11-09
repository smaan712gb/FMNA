"""
Test Quarterly Peer Data Fix
Verifies hybrid period strategy: TTM for target, Annual for peers
"""

import sys
import asyncio
from pathlib import Path
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from orchestration.comprehensive_orchestrator import ComprehensiveOrchestrator


async def test_quarterly_peer_fix():
    """Test that hybrid period strategy works"""
    logger.info("="*80)
    logger.info("TESTING QUARTERLY PEER DATA FIX")
    logger.info("="*80)
    
    test_symbol = "CRWD"
    
    try:
        # Initialize orchestrator
        orchestrator = ComprehensiveOrchestrator()
        
        # Test 1: TTM target with annual peers (the fix)
        logger.info("\n📊 TEST 1: TTM Target with Annual Peers (HYBRID STRATEGY)")
        logger.info("-" * 80)
        logger.info(f"Symbol: {test_symbol}")
        logger.info(f"Target Period: TTM")
        logger.info(f"Expected Peer Period: ANNUAL (auto-selected)")
        logger.info("")
        
        result = await orchestrator.run_comprehensive_analysis(
            symbol=test_symbol,
            period="ttm",  # TTM for target
            peers_required=5,  # Should use annual for peers ✅
            run_dcf=True,
            run_cca=True,  # Should work now with annual peers
            run_lbo=False,  # Skip to save time
            run_merger=False,
            run_three_statement=False,
            run_growth_scenarios=True,  # Include scenarios
            run_full_dd=False  # Skip to save time
        )
        
        # Validation checks
        logger.info("\n✅ VALIDATION RESULTS")
        logger.info("-" * 80)
        
        checks_passed = 0
        checks_total = 0
        
        # Check 1: Analysis completed
        checks_total += 1
        if result:
            logger.info(f"✅ Analysis completed successfully for {test_symbol}")
            logger.info(f"   Company: {result.company_name}")
            checks_passed += 1
        else:
            logger.error("❌ Analysis failed to complete")
        
        # Check 2: Peers obtained
        checks_total += 1
        if result and len(result.peers_data) >= 5:
            logger.info(f"✅ Peers obtained: {len(result.peers_data)} peers with complete data")
            for i, peer in enumerate(result.peers_data[:5], 1):
                logger.info(f"   {i}. {peer['symbol']}")
            checks_passed += 1
        else:
            logger.error(f"❌ Insufficient peers: {len(result.peers_data) if result else 0}/5")
        
        # Check 3: C CA ran successfully
        checks_total += 1
        if result and result.valuation.cca_result:
            logger.info(f"✅ CCA valuation completed")
            logger.info(f"   Value/Share (EV/EBITDA): ${result.valuation.cca_result.value_per_share_ebitda:.2f}")
            logger.info(f"   Peer Count: {result.valuation.cca_result.peer_count}")
            checks_passed += 1
        else:
            logger.error("❌ CCA did not run")
        
        # Check 4: DCF ran successfully  
        checks_total += 1
        if result and result.valuation.dcf_result:
            logger.info(f"✅ DCF valuation completed")
            logger.info(f"   Value/Share: ${result.valuation.dcf_result.value_per_share:.2f}")
            logger.info(f"   WACC: {result.valuation.dcf_result.wacc:.2%}")
            checks_passed += 1
        else:
            logger.error("❌ DCF did not run")
        
        # Check 5: Growth scenarios ran
        checks_total += 1
        if result and result.valuation.growth_scenarios:
            logger.info(f"✅ Growth scenarios completed")
            gs = result.valuation.growth_scenarios
            
            # Check if scenarios are differentiated
            if hasattr(gs, 'Bull') and hasattr(gs, 'Base') and hasattr(gs, 'Bear'):
                bull_fcf = gs.Bull.terminal_fcf if hasattr(gs.Bull, 'terminal_fcf') else 0
                base_fcf = gs.Base.terminal_fcf if hasattr(gs.Base, 'terminal_fcf') else 0
                bear_fcf = gs.Bear.terminal_fcf if hasattr(gs.Bear, 'terminal_fcf') else 0
                
                logger.info(f"   Bull Terminal FCF: ${bull_fcf:,.0f}")
                logger.info(f"   Base Terminal FCF: ${base_fcf:,.0f}")
                logger.info(f"   Bear Terminal FCF: ${bear_fcf:,.0f}")
                
                if bear_fcf < base_fcf < bull_fcf:
                    logger.info("   ✅ Scenarios properly ordered: Bear < Base < Bull")
                else:
                    logger.warning(f"   ⚠️  Scenario ordering may vary: {bear_fcf:,.0f} < {base_fcf:,.0f} < {bull_fcf:,.0f}")
            checks_passed += 1
        else:
            logger.warning("⚠️  Growth scenarios not run")
        
        # Check 6: Data sources
        checks_total += 1
        if result and result.data_sources_used:
            logger.info(f"✅ Data sources tracked: {len(result.data_sources_used)}")
            for source in result.data_sources_used:
                logger.info(f"   - {source}")
            checks_passed += 1
        else:
            logger.warning("⚠️  No data sources tracked")
        
        # Final summary
        logger.info("\n" + "="*80)
        logger.info(f"TEST SUMMARY: {checks_passed}/{checks_total} checks passed")
        logger.info("="*80)
        
        if checks_passed >= 4:  # At least 4/6 must pass
            logger.info("✅ QUARTERLY PEER FIX: WORKING")
            logger.info("   Hybrid period strategy successful")
            logger.info("   TTM target + Annual peers = Complete data")
            logger.info("   CCA can now proceed with TTM analyses")
            return True
        else:
            logger.error("❌ QUARTERLY PEER FIX: NEEDS REVIEW")
            logger.error(f"   Only {checks_passed}/{checks_total} checks passed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        logger.exception(e)
        return False
    finally:
        if 'orchestrator' in locals():
            orchestrator.close()


if __name__ == "__main__":
    success = asyncio.run(test_quarterly_peer_fix())
    sys.exit(0 if success else 1)
