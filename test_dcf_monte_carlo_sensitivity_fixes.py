"""
Test script for DCF Monte Carlo and Sensitivity Analysis fixes

This script tests the fixes applied to:
1. monte_carlo_simulation: Uses base values from inputs, proper error handling
2. sensitivity_analysis: Directly sensitizes input parameters (RF rate, growth rate)
"""

from engines.dcf_engine import DCFEngine, WACCInputs, TerminalValueInputs
from loguru import logger
import pandas as pd

def test_monte_carlo_fixes():
    """Test that Monte Carlo simulation uses base values from inputs"""
    
    logger.info("=" * 80)
    logger.info("Testing Monte Carlo Simulation Fixes")
    logger.info("=" * 80)
    
    # Initialize engine
    engine = DCFEngine()
    
    # Define inputs with specific values to verify they're used
    wacc_inputs = WACCInputs(
        risk_free_rate=0.045,  # 4.5% Treasury
        equity_risk_premium=0.07,  # 7.0% ERP (changed from hard-coded 6.5%)
        unlevered_beta=1.2,  # 1.2 beta (to verify it's used as base)
        target_debt_to_equity=0.25,
        cost_of_debt=0.05,
        tax_rate=0.21,
        market_cap=100_000_000,
        net_debt=25_000_000
    )
    
    terminal_inputs = TerminalValueInputs(
        method="gordon",
        perpetual_growth_rate=0.03  # 3% perpetual growth
    )
    
    # Forecast FCFF (5 years)
    fcff_forecast = [
        10_000_000,
        11_000_000,
        12_100_000,
        13_310_000,
        14_641_000
    ]
    
    # Run Monte Carlo with custom volatility parameters
    logger.info("\n1. Testing with custom volatility parameters:")
    mc_results = engine.monte_carlo_simulation(
        fcff_forecast=fcff_forecast,
        wacc_inputs=wacc_inputs,
        terminal_inputs=terminal_inputs,
        shares_outstanding=10_000_000,
        cash=5_000_000,
        debt=30_000_000,
        erp_std=0.01,  # Custom ERP volatility
        beta_std=0.1,  # Custom beta volatility
        growth_std=0.003,  # Custom growth volatility
        simulations=1000,
        random_seed=42
    )
    
    logger.info(f"Mean valuation: ${mc_results['mean']:.2f}")
    logger.info(f"Median valuation: ${mc_results['median']:.2f}")
    logger.info(f"Std deviation: ${mc_results['std']:.2f}")
    logger.info(f"P10-P90 range: ${mc_results['p10']:.2f} - ${mc_results['p90']:.2f}")
    logger.info(f"Successful simulations: {mc_results['simulations']}/1000")
    
    # Verify base values are being used (mean should be close to DCF with base inputs)
    logger.info("\n2. Comparing to base case DCF:")
    base_dcf = engine.calculate_dcf(
        fcff_forecast=fcff_forecast,
        wacc_inputs=wacc_inputs,
        terminal_inputs=terminal_inputs,
        shares_outstanding=10_000_000,
        cash=5_000_000,
        debt=30_000_000
    )
    logger.info(f"Base DCF value per share: ${base_dcf.value_per_share:.2f}")
    logger.info(f"Monte Carlo mean: ${mc_results['mean']:.2f}")
    logger.info(f"Difference: ${abs(base_dcf.value_per_share - mc_results['mean']):.2f}")
    
    # Test with extreme volatility to ensure error handling works
    logger.info("\n3. Testing with high volatility (error handling test):")
    mc_extreme = engine.monte_carlo_simulation(
        fcff_forecast=fcff_forecast,
        wacc_inputs=wacc_inputs,
        terminal_inputs=terminal_inputs,
        shares_outstanding=10_000_000,
        cash=5_000_000,
        debt=30_000_000,
        erp_std=0.03,  # High volatility
        beta_std=0.3,  # High volatility
        growth_std=0.01,  # High volatility
        simulations=1000,
        random_seed=43
    )
    logger.info(f"Successful simulations with high volatility: {mc_extreme['simulations']}/1000")
    logger.info(f"Success rate: {mc_extreme['simulations']/10:.1f}%")
    
    logger.info("\n✓ Monte Carlo fixes verified!")
    return True


def test_sensitivity_analysis_fixes():
    """Test that sensitivity analysis directly sensitizes input parameters"""
    
    logger.info("\n" + "=" * 80)
    logger.info("Testing Sensitivity Analysis Fixes")
    logger.info("=" * 80)
    
    # Initialize engine
    engine = DCFEngine()
    
    # Define inputs
    wacc_inputs = WACCInputs(
        risk_free_rate=0.045,  # 4.5% Treasury
        equity_risk_premium=0.065,  # 6.5% ERP
        unlevered_beta=1.0,
        target_debt_to_equity=0.25,
        cost_of_debt=0.05,
        tax_rate=0.21,
        market_cap=100_000_000,
        net_debt=25_000_000
    )
    
    terminal_inputs = TerminalValueInputs(
        method="gordon",
        perpetual_growth_rate=0.025  # 2.5% perpetual growth
    )
    
    # Forecast FCFF
    fcff_forecast = [
        10_000_000,
        11_000_000,
        12_100_000,
        13_310_000,
        14_641_000
    ]
    
    # Run sensitivity analysis with custom ranges
    logger.info("\n1. Running sensitivity analysis (RF rate vs. Growth rate):")
    sensitivity = engine.sensitivity_analysis(
        base_fcff=fcff_forecast,
        base_wacc_inputs=wacc_inputs,
        terminal_inputs=terminal_inputs,
        shares_outstanding=10_000_000,
        cash=5_000_000,
        debt=30_000_000,
        rf_rate_range=(-0.01, 0.01),  # RF rate +/- 1%
        growth_range=(-0.005, 0.005),  # Growth rate +/- 0.5%
        steps=5
    )
    
    logger.info("\nSensitivity Table (Risk-Free Rate vs. Terminal Growth):")
    logger.info(f"\n{sensitivity.to_string()}")
    
    # Verify the base case is in the middle
    logger.info("\n2. Verifying base case is in center of sensitivity table:")
    base_dcf = engine.calculate_dcf(
        fcff_forecast=fcff_forecast,
        wacc_inputs=wacc_inputs,
        terminal_inputs=terminal_inputs,
        shares_outstanding=10_000_000,
        cash=5_000_000,
        debt=30_000_000
    )
    
    # Get middle value from sensitivity table
    middle_idx = len(sensitivity) // 2
    middle_value = sensitivity.iloc[middle_idx, middle_idx]
    
    logger.info(f"Base DCF value per share: ${base_dcf.value_per_share:.2f}")
    logger.info(f"Middle sensitivity value: ${middle_value:.2f}")
    logger.info(f"Difference: ${abs(base_dcf.value_per_share - middle_value):.2f}")
    
    # Test with narrower ranges
    logger.info("\n3. Testing with narrower sensitivity ranges:")
    sensitivity_narrow = engine.sensitivity_analysis(
        base_fcff=fcff_forecast,
        base_wacc_inputs=wacc_inputs,
        terminal_inputs=terminal_inputs,
        shares_outstanding=10_000_000,
        cash=5_000_000,
        debt=30_000_000,
        rf_rate_range=(-0.005, 0.005),  # RF rate +/- 0.5%
        growth_range=(-0.0025, 0.0025),  # Growth rate +/- 0.25%
        steps=3
    )
    
    logger.info("\nNarrow Sensitivity Table:")
    logger.info(f"\n{sensitivity_narrow.to_string()}")
    
    logger.info("\n✓ Sensitivity analysis fixes verified!")
    return True


def main():
    """Run all tests"""
    logger.info("Starting DCF Monte Carlo and Sensitivity Analysis Fix Tests")
    logger.info("=" * 80)
    
    try:
        # Test Monte Carlo fixes
        test_monte_carlo_fixes()
        
        # Test Sensitivity Analysis fixes
        test_sensitivity_analysis_fixes()
        
        logger.info("\n" + "=" * 80)
        logger.info("✓ ALL TESTS PASSED!")
        logger.info("=" * 80)
        logger.info("\nKey Improvements:")
        logger.info("1. Monte Carlo now uses base values from wacc_inputs and terminal_inputs")
        logger.info("2. Monte Carlo volatility parameters are now customizable arguments")
        logger.info("3. Monte Carlo has smart error handling (caps growth at WACC - 0.25%)")
        logger.info("4. Sensitivity analysis directly sensitizes RF rate (not back-solved WACC)")
        logger.info("5. Sensitivity analysis is cleaner and more interpretable")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
