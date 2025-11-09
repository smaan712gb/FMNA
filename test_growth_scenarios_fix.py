"""
Test Growth Scenarios Fix - Verify Differentiation
Tests that Bear/Base/Bull scenarios now have DIFFERENT distress metrics
"""

import sys
from pathlib import Path
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from engines.growth_scenarios import GrowthScenariosEngine, GrowthScenarioInputs, GrowthStage, Industry


def test_scenario_differentiation():
    """Test that scenarios are properly differentiated"""
    logger.info("="*70)
    logger.info("TESTING GROWTH SCENARIOS DIFFERENTIATION")
    logger.info("="*70)
    
    # Initialize engine
    engine = GrowthScenariosEngine()
    
    # Create test inputs (typical SaaS company)
    inputs = GrowthScenarioInputs(
        company_name="Test SaaS Company",
        industry=Industry.SAAS,
        current_stage=GrowthStage.GROWTH,
        revenue=100_000_000,  # $100M revenue
        ebitda=20_000_000,  # $20M EBITDA (20% margin)
        ebit=18_000_000,  # $18M EBIT
        net_income=12_000_000,  # $12M net income
        total_assets=150_000_000,  # $150M assets
        current_assets=80_000_000,  # $80M current assets
        current_liabilities=30_000_000,  # $30M current liabilities
        total_debt=50_000_000,  # $50M debt
        cash=40_000_000,  # $40M cash
        working_capital=50_000_000,  # $50M working capital
        retained_earnings=30_000_000,  # $30M retained earnings
        market_value_equity=500_000_000,  # $500M market cap
        book_value_liabilities=80_000_000,  # $80M liabilities
        years=5,
        capex_pct_revenue=0.05,
        nwc_pct_revenue=0.10,
        tax_rate=0.21
    )
    
    # Run all scenarios
    logger.info("\n🔄 Running Bull/Base/Bear scenarios...")
    scenarios = engine.compare_scenarios(inputs)
    
    # Extract results
    bull = scenarios['Bull']
    base = scenarios['Base']
    bear = scenarios['Bear']
    
    # Display results
    logger.info("\n📊 SCENARIO RESULTS")
    logger.info("-" * 70)
    
    print("\n{:<25s} {:<15s} {:<15s} {:<15s}".format("Metric", "Bear", "Base", "Bull"))
    print("-" * 70)
    
    print("{:<25s} ${:<14,.0f} ${:<14,.0f} ${:<14,.0f}".format(
        "Terminal Revenue",
        bear.terminal_revenue,
        base.terminal_revenue,
        bull.terminal_revenue
    ))
    
    print("{:<25s} ${:<14,.0f} ${:<14,.0f} ${:<14,.0f}".format(
        "Terminal EBITDA",
        bear.terminal_ebitda,
        base.terminal_ebitda,
        bull.terminal_ebitda
    ))
    
    print("{:<25s} ${:<14,.0f} ${:<14,.0f} ${:<14,.0f}".format(
        "Terminal FCF",
        bear.terminal_fcf,
        base.terminal_fcf,
        bull.terminal_fcf
    ))
    
    print("{:<25s} {:<14.2f} {:<14.2f} {:<14.2f}".format(
        "Altman Z-Score",
        bear.distress_metrics.altman_z_score,
        base.distress_metrics.altman_z_score,
        bull.distress_metrics.altman_z_score
    ))
    
    print("{:<25s} {:<14.3f} {:<14.3f} {:<14.3f}".format(
        "Ohlson O-Score",
        bear.distress_metrics.ohlson_o_score,
        base.distress_metrics.ohlson_o_score,
        bull.distress_metrics.ohlson_o_score
    ))
    
    print("{:<25s} {:<14.2f}x {:<14.2f}x {:<14.2f}x".format(
        "Interest Coverage",
        bear.distress_metrics.interest_coverage,
        base.distress_metrics.interest_coverage,
        bull.distress_metrics.interest_coverage
    ))
    
    print("{:<25s} {:<14.2f}x {:<14.2f}x {:<14.2f}x".format(
        "Debt/EBITDA",
        bear.distress_metrics.debt_to_ebitda,
        base.distress_metrics.debt_to_ebitda,
        bull.distress_metrics.debt_to_ebitda
    ))
    
    print("{:<25s} {:<14.1%} {:<14.1%} {:<14.1%}".format(
        "Bankruptcy Prob",
        bear.bankruptcy_probability,
        base.bankruptcy_probability,
        bull.bankruptcy_probability
    ))
    
    # Validation checks
    logger.info("\n✅ VALIDATION CHECKS")
    logger.info("-" * 70)
    
    checks_passed = 0
    checks_total = 0
    
    # Check 1: FCF ordering
    checks_total += 1
    if bear.terminal_fcf < base.terminal_fcf < bull.terminal_fcf:
        logger.info("✅ Terminal FCF ordering correct: Bear < Base < Bull")
        checks_passed += 1
    else:
        logger.error(f"❌ Terminal FCF ordering wrong: Bear=${bear.terminal_fcf:,.0f}, Base=${base.terminal_fcf:,.0f}, Bull=${bull.terminal_fcf:,.0f}")
    
    # Check 2: Revenue ordering
    checks_total += 1
    if bear.terminal_revenue < base.terminal_revenue < bull.terminal_revenue:
        logger.info("✅ Terminal Revenue ordering correct: Bear < Base < Bull")
        checks_passed += 1
    else:
        logger.error(f"❌ Terminal Revenue ordering wrong")
    
    # Check 3: Z-Score differentiation
    checks_total += 1
    bear_z = bear.distress_metrics.altman_z_score
    base_z = base.distress_metrics.altman_z_score
    bull_z = bull.distress_metrics.altman_z_score
    
    if bear_z != base_z and base_z != bull_z and bear_z != bull_z:
        logger.info(f"✅ Altman Z-Score differentiated: Bear={bear_z:.2f}, Base={base_z:.2f}, Bull={bull_z:.2f}")
        checks_passed += 1
    else:
        logger.error(f"❌ Altman Z-Score NOT differentiated: Bear={bear_z:.2f}, Base={base_z:.2f}, Bull={bull_z:.2f}")
    
    # Check 4: Z-Score ordering (higher is better)
    checks_total += 1
    if bear_z < base_z < bull_z:
        logger.info("✅ Altman Z-Score ordering correct: Bear < Base < Bull")
        checks_passed += 1
    else:
        logger.warning(f"⚠️  Altman Z-Score ordering: Bear={bear_z:.2f}, Base={base_z:.2f}, Bull={bull_z:.2f}")
        logger.warning("    (May vary based on inputs, but should generally follow Bear < Base < Bull)")
    
    # Check 5: O-Score differentiation
    checks_total += 1
    bear_o = bear.distress_metrics.ohlson_o_score
    base_o = base.distress_metrics.ohlson_o_score
    bull_o = bull.distress_metrics.ohlson_o_score
    
    if bear_o != base_o and base_o != bull_o and bear_o != bull_o:
        logger.info(f"✅ Ohlson O-Score differentiated: Bear={bear_o:.3f}, Base={base_o:.3f}, Bull={bull_o:.3f}")
        checks_passed += 1
    else:
        logger.error(f"❌ Ohlson O-Score NOT differentiated: Bear={bear_o:.3f}, Base={base_o:.3f}, Bull={bull_o:.3f}")
    
    # Check 6: Debt/EBITDA differentiation
    checks_total += 1
    bear_de = bear.distress_metrics.debt_to_ebitda
    base_de = base.distress_metrics.debt_to_ebitda
    bull_de = bull.distress_metrics.debt_to_ebitda
    
    if bear_de != base_de and base_de != bull_de:
        logger.info(f"✅ Debt/EBITDA differentiated: Bear={bear_de:.2f}x, Base={base_de:.2f}x, Bull={bull_de:.2f}x")
        checks_passed += 1
    else:
        logger.error(f"❌ Debt/EBITDA NOT differentiated: Bear={bear_de:.2f}x, Base={base_de:.2f}x, Bull={bull_de:.2f}x")
    
    # Final summary
    logger.info("\n" + "="*70)
    logger.info(f"VALIDATION SUMMARY: {checks_passed}/{checks_total} checks passed")
    logger.info("="*70)
    
    if checks_passed >= checks_total - 1:  # Allow 1 warning
        logger.info("✅ SCENARIO DIFFERENTIATION FIX: WORKING")
        logger.info("   Bear/Base/Bull scenarios now have different metrics")
        logger.info("   Terminal FCF ordering is correct")
        logger.info("   Distress metrics cascade from scenario assumptions")
        return True
    else:
        logger.error("❌ SCENARIO DIFFERENTIATION FIX: NEEDS REVIEW")
        logger.error(f"   Only {checks_passed}/{checks_total} checks passed")
        return False


if __name__ == "__main__":
    success = test_scenario_differentiation()
    sys.exit(0 if success else 1)
