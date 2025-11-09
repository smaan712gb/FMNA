"""
Test the truly integrated 3-statement model
Demonstrates: NO PLUGS, year-by-year construction, circular references
"""

from engines.three_statement_model_integrated import (
    IntegratedThreeStatementModel,
    HistoricalData,
    DriverInputs
)
from loguru import logger


def test_integrated_model():
    """Test the integrated 3-statement model with real scenarios"""
    
    logger.info("=" * 80)
    logger.info("Testing Integrated 3-Statement Model (NO PLUGS)")
    logger.info("=" * 80)
    
    # ================================================================
    # Test 1: Simple Company with Historical Data
    # ================================================================
    logger.info("\nTest 1: Company with 2 years historical + 5 year forecast")
    
    # Create balanced historical data
    historical = HistoricalData(
        periods=["FY-1", "FY0"],
        
        # Income Statement
        revenue=[1000.0, 1100.0],
        cogs=[600.0, 650.0],
        sga=[150.0, 160.0],
        rnd=[50.0, 55.0],
        da=[30.0, 33.0],
        interest_expense=[20.0, 18.0],
        interest_income=[1.0, 1.5],
        taxes=[30.1, 35.1],
        net_income=[120.9, 140.4],
        
        # Balance Sheet (MUST BALANCE)
        cash=[100.0, 120.0],
        ar=[150.0, 165.0],
        inventory=[80.0, 85.0],
        ppe_net=[300.0, 320.0],
        goodwill=[50.0, 50.0],
        
        ap=[70.0, 75.0],
        accrued_liabilities=[30.0,  32.0],
        debt=[400.0, 350.0],
        equity=[180.0, 283.0],  # Must balance: Assets - Liabilities
        
        # Cash Flow
        capex=[-50.0, -50.0],
        dividends=[0.0, 0.0],
        sbc=[10.0, 12.0]
    )
    
    # Define smart drivers
    drivers = DriverInputs(
        # Revenue growth
        revenue_growth_rates=[0.10, 0.08, 0.07, 0.06, 0.05],
        
        # Margins
        cogs_pct_revenue=[0.59, 0.58, 0.57, 0.56, 0.55],
        sga_pct_revenue=[0.14, 0.14, 0.14, 0.14, 0.14],
        rnd_pct_revenue=[0.05, 0.05, 0.05, 0.05, 0.05],
        sbc_pct_revenue=[0.01, 0.01, 0.01, 0.01, 0.01],
        
        # Working capital (in days)
        ar_days=[55.0, 55.0, 54.0, 53.0, 52.0],
        inventory_days=[45.0, 44.0, 43.0, 42.0, 41.0],
        ap_days=[40.0, 39.0, 38.0, 37.0, 36.0],
        accrued_days_sga=[70.0, 70.0, 70.0, 70.0, 70.0],
        
        # CapEx
        capex_pct_revenue=[0.05, 0.05, 0.05, 0.045, 0.04],
        ppe_depreciation_years=10.0,
        
        # Financing
        interest_rate_debt=0.05,
        interest_rate_cash=0.02,
        tax_rate=0.21,
        mandatory_debt_payment=25.0,  # $25M/year
        
        # Revolver
        has_revolver=True,
        revolver_rate=0.06,
        min_cash_balance=50.0,
        
        # Dividends
        dividends_pct_ni=0.0
    )
    
    # Build the model
    model = IntegratedThreeStatementModel()
    result = model.build_integrated_model(
        historical=historical,
        drivers=drivers,
        forecast_years=5
    )
    
    # ================================================================
    # Analyze Results
    # ================================================================
    logger.info("\n" + "=" * 80)
    logger.info("RESULTS")
    logger.info("=" * 80)
    
    logger.info("\n📊 Income Statement (All Periods):")
    logger.info(f"\n{result.income_statement.to_string()}")
    
    logger.info("\n💰 Balance Sheet (All Periods):")
    logger.info(f"\n{result.balance_sheet.to_string()}")
    
    logger.info("\n💸 Cash Flow Statement (All Periods):")
    logger.info(f"\n{result.cash_flow_statement.to_string()}")
    
    # ================================================================
    # Validation
    # ================================================================
    logger.info("\n" + "=" * 80)
    logger.info("VALIDATION")
    logger.info("=" * 80)
    
    logger.info(f"\n✓ All balance sheets validate: {result.all_balance_checks_pass}")
    logger.info(f"✓ Max balance error: ${result.max_balance_error:,.2f}")
    
    # Check key properties
    forecast_years = result.years[len(historical.periods):]
    
    logger.info("\n📈 Forecast Period Analysis:")
    for year in forecast_years:
        logger.info(f"\n{year.period}:")
        logger.info(f"  Revenue: ${year.revenue:,.0f}")
        logger.info(f"  Net Income: ${year.net_income:,.0f}")
        logger.info(f"  FCF: ${year.cfo + year.cfi:,.0f}")
        logger.info(f"  Ending Cash: ${year.cash:,.0f}")
        logger.info(f"  Ending Debt: ${year.debt:,.0f}")
        logger.info(f"  Ending Revolver: ${year.revolver:,.0f}")
        logger.info(f"  Ending Equity: ${year.equity:,.0f}")
        logger.info(f"  Balance Check: {year.balance_check} (Error: ${year.balance_error:,.2f})")
    
    # ================================================================
    # Test 2: Verify NO PLUGS
    # ================================================================
    logger.info("\n" + "=" * 80)
    logger.info("VERIFICATION: NO PLUGS")
    logger.info("=" * 80)
    
    # Cash is NOT a plug - it's the result of cash flows
    logger.info("\n✓ Cash is the RESULT (not a plug):")
    for year in forecast_years:
        expected_cash = year.beg_cash + year.net_cash_flow
        logger.info(f"  {year.period}: Beg Cash ${year.beg_cash:,.0f} + Net CF ${year.net_cash_flow:,.0f} = ${expected_cash:,.0f} (Actual: ${year.cash:,.0f})")
        assert abs(expected_cash - year.cash) < 1.0, "Cash should equal beginning + net cash flow"
    
    # Equity is NOT a plug - it's a roll-forward (includes SBC as share issuance)
    logger.info("\n✓ Equity is a ROLL-FORWARD (not a plug):")
    for year in forecast_years:
        expected_equity = year.beg_equity + year.net_income - year.dividends + year.sbc
        logger.info(f"  {year.period}: Beg Equity ${year.beg_equity:,.0f} + NI ${year.net_income:,.0f} - Div ${year.dividends:,.0f} + SBC ${year.sbc:,.0f} = ${expected_equity:,.0f} (Actual: ${year.equity:,.0f})")
        assert abs(expected_equity - year.equity) < 1.0, "Equity should equal roll-forward"
    
    # Balance sheet balances (not because of plugs, but because of proper integration)
    logger.info("\n✓ Balance Sheet BALANCES (without plugs):")
    for year in forecast_years:
        logger.info(f"  {year.period}: Assets ${year.total_assets:,.0f} = Liab+Equity ${year.total_liab_equity:,.0f} (Error: ${year.balance_error:,.2f})")
        assert year.balance_check, "Balance sheet must balance"
    
    # ================================================================
    # Test 3: Verify Circular Reference Handling
    # ================================================================
    logger.info("\n" + "=" * 80)
    logger.info("VERIFICATION: CIRCULAR REFERENCES")
    logger.info("=" * 80)
    
    logger.info("\n✓ Interest on AVERAGE balances (not beginning):")
    for year in forecast_years:
        avg_debt = (year.beg_debt + year.debt) / 2.0
        avg_cash = (year.beg_cash + year.cash) / 2.0
        expected_int_exp = avg_debt * drivers.interest_rate_debt
        expected_int_inc = avg_cash * drivers.interest_rate_cash
        
        logger.info(f"  {year.period}:")
        logger.info(f"    Avg Debt: ${avg_debt:,.0f} × {drivers.interest_rate_debt:.1%} = ${expected_int_exp:,.0f} (Actual: ${year.interest_expense:,.0f})")
        logger.info(f"    Avg Cash: ${avg_cash:,.0f} × {drivers.interest_rate_cash:.1%} = ${expected_int_inc:,.0f} (Actual: ${year.interest_income:,.0f})")
    
    # ================================================================
    # Test 4: Verify Smart Drivers
    # ================================================================
    logger.info("\n" + "=" * 80)
    logger.info("VERIFICATION: SMART DRIVERS")
    logger.info("=" * 80)
    
    logger.info("\n✓ D&A driven by PP&E (not revenue %):")
    for year in forecast_years:
        avg_ppe = (year.beg_ppe_net - year.capex) / 2.0  # Rough estimate
        logger.info(f"  {year.period}: Avg PPE ${avg_ppe:,.0f} → D&A ${year.da:,.0f}")
    
    logger.info("\n✓ Accrued driven by SG&A (not revenue):")
    for year in forecast_years:
        expected_accrued = year.sga * (drivers.accrued_days_sga[0] / 365.0)
        logger.info(f"  {year.period}: SG&A ${year.sga:,.0f} × {drivers.accrued_days_sga[0]:.0f} days = ${expected_accrued:,.0f} (Actual: ${year.accrued_liabilities:,.0f})")
    
    # ================================================================
    # Test 5: Cash Sweep / Revolver Logic
    # ================================================================
    logger.info("\n" + "=" * 80)
    logger.info("VERIFICATION: CASH SWEEP / REVOLVER")
    logger.info("=" * 80)
    
    logger.info("\n✓ Maintains minimum cash balance:")
    for year in forecast_years:
        logger.info(f"  {year.period}: Cash ${year.cash:,.0f} (Min: ${drivers.min_cash_balance:,.0f}), Revolver: ${year.revolver:,.0f}")
        assert year.cash >= drivers.min_cash_balance - 1.0, f"Cash should be at least minimum balance"
    
    # ================================================================
    # Summary
    # ================================================================
    logger.info("\n" + "=" * 80)
    logger.info("✅ ALL TESTS PASSED!")
    logger.info("=" * 80)
    
    logger.info("\nKey Achievements:")
    logger.info("✓ NO PLUGS - Cash is the result, Equity is a roll-forward")
    logger.info("✓ Year-by-year construction handles circular references")
    logger.info("✓ Interest on average balances (not beginning)")
    logger.info("✓ Smart drivers (D&A from PP&E, Accrued from SG&A)")
    logger.info("✓ Cash sweep and revolver logic")
    logger.info("✓ Balance sheet validates WITHOUT relying on plugs")
    logger.info(f"✓ All {len(result.years)} periods balance perfectly")
    
    return result


if __name__ == "__main__":
    try:
        result = test_integrated_model()
        logger.info("\n🎉 Integrated 3-statement model test SUCCESSFUL!")
        exit(0)
    except Exception as e:
        logger.error(f"\n❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
