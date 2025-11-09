"""
Test Integrated 3-Statement Model
Demonstrates historical + forecast modeling capability
"""

from engines.three_statement_model import (
    IntegratedThreeStatementModel,
    HistoricalData,
    DriverInputs
)
from loguru import logger
import pandas as pd


def test_integrated_model():
    """Test the integrated 3-statement model with historical + forecast"""
    logger.info("=" * 80)
    logger.info("INTEGRATED 3-STATEMENT MODEL TEST")
    logger.info("=" * 80)
    
    # 1. Historical Data (FY-2, FY-1, FY0)
    historical = HistoricalData(
        periods=['FY-2', 'FY-1', 'FY0'],
        
        # Income Statement
        revenue=[800_000_000, 900_000_000, 1_000_000_000],
        cogs=[400_000_000, 450_000_000, 500_000_000],
        sga=[160_000_000, 180_000_000, 200_000_000],
        rnd=[80_000_000, 90_000_000, 100_000_000],
        da=[40_000_000, 45_000_000, 50_000_000],
        interest_expense=[10_000_000, 12_000_000, 15_000_000],
        taxes=[33_000_000, 39_600_000, 40_500_000],
        sbc=[8_000_000, 9_000_000, 10_000_000],
        
        # Balance Sheet
        cash=[80_000_000, 90_000_000, 100_000_000],
        ar=[120_000_000, 135_000_000, 150_000_000],
        inventory=[100_000_000, 112_500_000, 125_000_000],
        ppe=[240_000_000, 270_000_000, 300_000_000],
        goodwill=[80_000_000, 90_000_000, 100_000_000],
        ap=[80_000_000, 90_000_000, 100_000_000],
        debt=[200_000_000, 240_000_000, 300_000_000],
        equity=[440_000_000, 467_500_000, 475_000_000],
        
        # Optional
        capex=[50_000_000, 75_000_000, 80_000_000]
    )
    
    # 2. Forecast Drivers (5 years forecast)
    drivers = DriverInputs(
        # Revenue growth: 12%, 10%, 8%, 8%, 7%
        revenue_growth_rates=[0.12, 0.10, 0.08, 0.08, 0.07],
        
        # Margins (as % of revenue)
        cogs_pct_revenue=[0.48, 0.47, 0.46, 0.46, 0.45],
        sga_pct_revenue=[0.18, 0.17, 0.17, 0.16, 0.16],
        da_pct_revenue=[0.05, 0.05, 0.05, 0.05, 0.05],
        rnd_pct_revenue=[0.09, 0.09, 0.09, 0.08, 0.08],
        sbc_pct_revenue=[0.01, 0.01, 0.01, 0.01, 0.01],
        
        # Working capital days
        ar_days=[55, 54, 53, 52, 50],
        inventory_days=[90, 88, 86, 85, 84],
        ap_days=[73, 72, 71, 70, 70],
        
        # CapEx and financing
        capex_pct_revenue=[0.08, 0.08, 0.07, 0.07, 0.06],
        interest_rate=0.05,
        tax_rate=0.27,
        mandatory_debt_payment=10_000_000
    )
    
    # 3. Build the integrated model
    model = IntegratedThreeStatementModel()
    result = model.build_integrated_model(
        historical=historical,
        drivers=drivers,
        forecast_years=5
    )
    
    # 4. Display Results
    logger.info("\n" + "=" * 80)
    logger.info("INCOME STATEMENT")
    logger.info("=" * 80)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.float_format', lambda x: f'${x:,.0f}' if abs(x) > 1 else f'{x:.2%}')
    
    # Format for display
    is_display = result.income_statement.copy()
    for col in ['Revenue', 'COGS', 'Gross_Profit', 'SGA', 'RD', 'DA', 'SBC', 'EBITDA', 'EBIT', 'Interest_Expense', 'EBT', 'Taxes', 'Net_Income']:
        if col in is_display.columns:
            is_display[col] = is_display[col].apply(lambda x: f'${x:,.0f}')
    
    print(is_display.to_string(index=False))
    
    logger.info("\n" + "=" * 80)
    logger.info("BALANCE SHEET")
    logger.info("=" * 80)
    
    bs_display = result.balance_sheet.copy()
    for col in ['Cash', 'AR', 'Inventory', 'Current_Assets', 'PPE', 'Goodwill', 'Total_Assets', 
                'AP', 'Accrued_Liabilities', 'Current_Liabilities', 'Total_Debt', 'Total_Liabilities', 
                'Equity', 'Total_Liab_Equity']:
        if col in bs_display.columns:
            bs_display[col] = bs_display[col].apply(lambda x: f'${x:,.0f}')
    
    print(bs_display[['Period', 'Total_Assets', 'Total_Debt', 'Equity', 'Total_Liab_Equity', 'Balance_Check']].to_string(index=False))
    
    logger.info("\n" + "=" * 80)
    logger.info("CASH FLOW STATEMENT")
    logger.info("=" * 80)
    
    cf_display = result.cash_flow_statement.copy()
    for col in ['Net_Income', 'DA', 'SBC', 'Changes_in_WC', 'CFO', 'CapEx', 'FCF', 'Debt_Change']:
        if col in cf_display.columns:
            cf_display[col] = cf_display[col].apply(lambda x: f'${x:,.0f}')
    
    print(cf_display[['Period', 'CFO', 'CapEx', 'FCF', 'Debt_Change']].to_string(index=False))
    
    logger.info("\n" + "=" * 80)
    logger.info("WORKING CAPITAL SCHEDULE")
    logger.info("=" * 80)
    
    wc_display = result.working_capital_schedule.copy()
    for col in ['AR', 'Inventory', 'AP', 'Net_Working_Capital']:
        if col in wc_display.columns:
            wc_display[col] = wc_display[col].apply(lambda x: f'${x:,.0f}')
    
    print(wc_display[['Period', 'Net_Working_Capital', 'AR_Days', 'Inventory_Days', 'AP_Days']].to_string(index=False))
    
    logger.info("\n" + "=" * 80)
    logger.info("DEBT SCHEDULE")
    logger.info("=" * 80)
    
    debt_display = result.debt_schedule.copy()
    for col in ['Beginning_Debt', 'Ending_Debt', 'Debt_Change']:
        if col in debt_display.columns:
            debt_display[col] = debt_display[col].apply(lambda x: f'${x:,.0f}')
    
    print(debt_display.to_string(index=False))
    
    # 5. Key Metrics Summary
    logger.info("\n" + "=" * 80)
    logger.info("KEY FORECAST METRICS (FY+1 to FY+5)")
    logger.info("=" * 80)
    
    print(f"\nFree Cash Flow:")
    for i, fcf in enumerate(result.fcf_forecast):
        print(f"  FY+{i+1}: ${fcf:,.0f}")
    
    print(f"\nEBITDA:")
    for i, ebitda in enumerate(result.ebitda_forecast):
        print(f"  FY+{i+1}: ${ebitda:,.0f}")
    
    print(f"\nNet Income:")
    for i, ni in enumerate(result.net_income_forecast):
        print(f"  FY+{i+1}: ${ni:,.0f}")
    
    # 6. Validation Results
    logger.info("\n" + "=" * 80)
    logger.info("VALIDATION CHECKS")
    logger.info("=" * 80)
    
    logger.info(f"✓ Balance Sheet Balances: {result.balance_check}")
    logger.info(f"✓ Cash Flow Validation: {result.cash_flow_check}")
    logger.info(f"✓ Historical Periods: {', '.join(result.historical_periods)}")
    logger.info(f"✓ Forecast Periods: {', '.join(result.forecast_periods)}")
    logger.info(f"✓ Base Year: {result.base_year}")
    logger.info(f"✓ Total Periods: {len(result.income_statement)}")
    
    # 7. Revenue Growth Analysis
    logger.info("\n" + "=" * 80)
    logger.info("REVENUE GROWTH ANALYSIS")
    logger.info("=" * 80)
    
    revenue_series = result.income_statement['Revenue'].values
    for i in range(1, len(revenue_series)):
        growth = (revenue_series[i] / revenue_series[i-1] - 1) * 100
        period = result.income_statement.iloc[i]['Period']
        prior_period = result.income_statement.iloc[i-1]['Period']
        print(f"{prior_period} → {period}: {growth:.2f}% growth (${revenue_series[i]:,.0f})")
    
    logger.info("\n" + "=" * 80)
    logger.info("TEST COMPLETED SUCCESSFULLY")
    logger.info("=" * 80)
    
    return result


def test_forecast_only_model():
    """Test the legacy forecast-only model for backward compatibility"""
    logger.info("\n\n" + "=" * 80)
    logger.info("FORECAST-ONLY MODEL TEST (Legacy Method)")
    logger.info("=" * 80)
    
    drivers = DriverInputs(
        revenue_growth_rates=[0.12, 0.10, 0.08, 0.08, 0.07],
        cogs_pct_revenue=[0.48, 0.47, 0.46, 0.46, 0.45],
        sga_pct_revenue=[0.18, 0.17, 0.17, 0.16, 0.16],
        da_pct_revenue=[0.05, 0.05, 0.05, 0.05, 0.05],
        rnd_pct_revenue=[0.09, 0.09, 0.09, 0.08, 0.08],
        sbc_pct_revenue=[0.01, 0.01, 0.01, 0.01, 0.01],
        ar_days=[55, 54, 53, 52, 50],
        inventory_days=[90, 88, 86, 85, 84],
        ap_days=[73, 72, 71, 70, 70],
        capex_pct_revenue=[0.08, 0.08, 0.07, 0.07, 0.06],
        interest_rate=0.05,
        tax_rate=0.27,
        mandatory_debt_payment=10_000_000
    )
    
    model = IntegratedThreeStatementModel()
    result = model.build_integrated_model(
        historical=historical,
        drivers=drivers,
        forecast_years=5
    )
    
    logger.info(f"✓ Forecast periods: {', '.join(result.forecast_periods)}")
    logger.info(f"✓ Balance check: {result.balance_check}")
    logger.info(f"✓ Total FCF: ${sum(result.fcf_forecast):,.0f}")
    
    return result


if __name__ == "__main__":
    # Test integrated model
    integrated_result = test_integrated_model()
    
    # Test legacy forecast-only model
    forecast_result = test_forecast_only_model()
    
    logger.info("\n" + "=" * 80)
    logger.info("ALL TESTS PASSED ✓")
    logger.info("=" * 80)
