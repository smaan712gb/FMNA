"""
Truly Integrated 3-Statement Model
Builds year-by-year to handle circular references properly
NO PLUGS - Cash is the result, Equity is a roll-forward
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np
import pandas as pd
from loguru import logger


@dataclass
class HistoricalData:
    """Historical financial data - MUST balance or you have data integrity issues"""
    periods: List[str]
    
    # Income Statement
    revenue: List[float]
    cogs: List[float]
    sga: List[float]
    rnd: List[float]
    da: List[float]
    interest_expense: List[float]
    interest_income: List[float]
    taxes: List[float]
    net_income: List[float]
    
    # Balance Sheet - MUST BALANCE
    cash: List[float]
    ar: List[float]
    inventory: List[float]
    ppe_net: List[float]
    goodwill: List[float]
    
    ap: List[float]
    accrued_liabilities: List[float]
    debt: List[float]
    equity: List[float]
    
    # Cash Flow items
    capex: List[float]
    dividends: Optional[List[float]] = None
    sbc: Optional[List[float]] = None


@dataclass
class DriverInputs:
    """Smart drivers for forecast periods"""
    # Revenue growth
    revenue_growth_rates: List[float]
    
    # Margins (% of revenue)
    cogs_pct_revenue: List[float]
    sga_pct_revenue: List[float]
    
    # Working capital (in days)
    ar_days: List[float]
    inventory_days: List[float]
    ap_days: List[float]
    accrued_days_sga: List[float]  # Accrued as days of SG&A
    
    # CapEx
    capex_pct_revenue: List[float]
    
    # Financing
    interest_rate_debt: float
    tax_rate: float
    
    # Optional fields (must come after required fields)
    rnd_pct_revenue: Optional[List[float]] = None
    sbc_pct_revenue: Optional[List[float]] = None
    ppe_depreciation_years: float = 10.0  # For depreciation schedule
    interest_rate_cash: float = 0.02  # Earn interest on cash
    mandatory_debt_payment: float = 0.0
    
    # Revolver (optional)
    has_revolver: bool = True
    revolver_rate: float = 0.06
    min_cash_balance: float = 0.0
    
    # Other
    dividends_pct_ni: float = 0.0  # % of NI paid as dividends


@dataclass  
class YearResult:
    """Results for a single year"""
    period: str
    
    # Income Statement
    revenue: float
    cogs: float
    gross_profit: float
    sga: float
    rnd: float
    da: float
    sbc: float
    ebitda: float
    ebit: float
    interest_expense: float
    interest_income: float
    ebt: float
    taxes: float
    net_income: float
    
    # Balance Sheet - Beginning
    beg_cash: float
    beg_debt: float
    beg_revolver: float
    beg_equity: float
    beg_ppe_net: float
    
    # Balance Sheet - Ending
    cash: float
    ar: float
    inventory: float
    ppe_net: float
    goodwill: float
    total_assets: float
    
    ap: float
    accrued_liabilities: float
    debt: float
    revolver: float
    total_liabilities: float
    equity: float
    total_liab_equity: float
    
    # Cash Flow
    cfo: float
    capex: float  # Stored as a positive expense
    cfi: float
    dividends: float
    debt_payment: float
    revolver_draw: float
    cff: float
    net_cash_flow: float
    
    # Validation
    balance_check: bool
    balance_error: float


@dataclass
class ThreeStatementResult:
    """Complete 3-statement model output"""
    years: List[YearResult]
    
    # Periods
    historical_periods: List[str]
    forecast_periods: List[str]
    
    # DataFrames
    income_statement: pd.DataFrame
    balance_sheet: pd.DataFrame
    cash_flow_statement: pd.DataFrame
    
    # Forecast metrics
    fcf_forecast: List[float]
    ebitda_forecast: List[float]
    net_income_forecast: List[float]
    
    # Validation
    all_balance_checks_pass: bool
    max_balance_error: float


class IntegratedThreeStatementModel:
    """
    Truly integrated 3-statement model
    Builds year-by-year, handles circular references, NO PLUGS
    """
    
    def __init__(self):
        logger.info("Integrated 3-Statement Model initialized (year-by-year construction)")
    
    def _validate_historical_data(self, hist: HistoricalData) -> None:
        """Validate that historical data balances and is internally consistent"""
        for i, period in enumerate(hist.periods):
            # --- FIX: Added Income Statement validation ---
            ebitda = hist.revenue[i] - hist.cogs[i] - hist.sga[i] - hist.rnd[i]
            ebit = ebitda - hist.da[i]
            ebt = ebit - hist.interest_expense[i] + hist.interest_income[i]
            ni = ebt - hist.taxes[i]
            
            if abs(ni - hist.net_income[i]) > 1.0:
                 raise ValueError(
                    f"Historical IS data does not roll for {period}: "
                    f"Calculated NI={ni:,.0f}, Provided NI={hist.net_income[i]:,.0f}"
                )

            # Check balance sheet equation
            assets = hist.cash[i] + hist.ar[i] + hist.inventory[i] + hist.ppe_net[i] + hist.goodwill[i]
            liab = hist.ap[i] + hist.accrued_liabilities[i] + hist.debt[i]
            equity = hist.equity[i]
            
            error = abs(assets - (liab + equity))
            if error > 1.0:  # Allow $1 rounding error
                raise ValueError(
                    f"Historical BS data does not balance for {period}: "
                    f"Assets={assets:,.0f}, Liab+Equity={liab+equity:,.0f}, Error={error:,.0f}"
                )
        
        logger.info(f"✓ Historical data validated for {len(hist.periods)} periods")
    
    def _build_one_year(
        self,
        period: str,
        is_forecast: bool,
        
        # Drivers
        revenue: float,
        drivers: DriverInputs,
        driver_idx: int,
        
        # Prior year balance sheet
        prior_cash: float,
        prior_ar: float,
        prior_inventory: float,
        prior_ppe_net: float,
        prior_goodwill: float,
        prior_ap: float,
        prior_accrued: float,
        prior_debt: float,
        prior_revolver: float,
        prior_equity: float,
        
    ) -> YearResult:
        """
        Build one year of integrated financials
        This is where the circular reference magic happens
        """
        
        # ================================================================
        # Step 1: Build Income Statement (Top Half - Revenue to EBIT)
        # ================================================================
        cogs = revenue * drivers.cogs_pct_revenue[driver_idx]
        gross_profit = revenue - cogs
        sga = revenue * drivers.sga_pct_revenue[driver_idx]
        rnd = revenue * drivers.rnd_pct_revenue[driver_idx] if drivers.rnd_pct_revenue else 0.0
        sbc = revenue * drivers.sbc_pct_revenue[driver_idx] if drivers.sbc_pct_revenue else 0.0
        
        # ================================================================
        # Step 2: Build Asset Schedules (Non-Cash)
        # ================================================================
        # Accounts Receivable (from Revenue)
        ar = revenue * (drivers.ar_days[driver_idx] / 365.0)
        
        # Inventory (from COGS)
        inventory = cogs * (drivers.inventory_days[driver_idx] / 365.0)
        
        # PP&E Net (from CapEx and D&A)
        capex = revenue * drivers.capex_pct_revenue[driver_idx]
        
        # --- FIX: Simplified D&A calculation ---
        # Assumes straight-line depreciation on the *prior* asset base
        # This is a common simplification. A more complex model would use vintages.
        da = prior_ppe_net / drivers.ppe_depreciation_years
        
        ppe_net = prior_ppe_net + capex - da
        goodwill = prior_goodwill  # Goodwill doesn't change unless impairment
        
        # EBITDA and EBIT (now that we have D&A)
        ebitda = gross_profit - sga - rnd
        ebit = ebitda - da
        
        # ================================================================
        # Step 3: Build Liability Schedules (Non-Debt)
        # ================================================================
        # Accounts Payable (from COGS)
        ap = cogs * (drivers.ap_days[driver_idx] / 365.0)
        
        # Accrued Liabilities (smart: from SG&A, not revenue)
        accrued_liabilities = sga * (drivers.accrued_days_sga[driver_idx] / 365.0)
        
        # ================================================================
        # Step 4: Build Partial Cash Flow Statement
        # ================================================================
        # Changes in NWC
        delta_ar = ar - prior_ar
        delta_inventory = inventory - prior_inventory
        delta_ap = ap - prior_ap
        delta_accrued = accrued_liabilities - prior_accrued
        
        change_in_nwc = delta_ar + delta_inventory - delta_ap - delta_accrued
        
        # ================================================================
        # Step 5: Debt & Cash Schedule (CIRCULAR REFERENCE SOLVER)
        # ================================================================
        # We need to solve for: Cash, Revolver, Interest, Taxes, Net Income
        # This is circular because Interest depends on avg debt/cash, which depends 
        # on ending cash, which depends on net income, which depends on interest!
        
        # Calculate debt payment ONCE (not circular)
        debt_payment = min(drivers.mandatory_debt_payment, max(0.0, prior_debt))
        ending_debt = max(0.0, prior_debt - debt_payment)
        
        # Use iterative approach for circular references (cash, revolver, interest)
        MAX_ITERATIONS = 20
        TOLERANCE = 0.01
        
        # Initial guesses
        ending_cash = prior_cash
        ending_revolver = prior_revolver
        
        for iteration in range(MAX_ITERATIONS):
            # Calculate average balances for interest
            avg_debt = (prior_debt + ending_debt) / 2.0
            avg_revolver = (prior_revolver + ending_revolver) / 2.0
            avg_cash = (prior_cash + ending_cash) / 2.0
            
            # Calculate interest
            interest_expense = (avg_debt * drivers.interest_rate_debt + 
                                avg_revolver * drivers.revolver_rate)
            interest_income = avg_cash * drivers.interest_rate_cash
            
            # Complete Income Statement
            ebt = ebit - interest_expense + interest_income
            taxes = max(0.0, ebt * drivers.tax_rate)  # TODO: Add NOL tracking
            net_income = ebt - taxes
            
            # Cash From Operations
            cfo = net_income + da + sbc - change_in_nwc
            
            # Cash From Investing
            cfi = -capex
            
            # Cash Flow Before Financing
            cf_before_financing = cfo + cfi
            
            # Calculate new ending balances
            cash_available = prior_cash + cf_before_financing
            
            # Pay mandatory debt (already calculated above)
            cash_available -= debt_payment
            
            # Pay dividends
            dividends = net_income * drivers.dividends_pct_ni
            cash_available -= dividends
            
            # Handle revolver / cash balance
            if cash_available < drivers.min_cash_balance:
                # Draw from revolver
                revolver_draw = drivers.min_cash_balance - cash_available
                new_ending_cash = drivers.min_cash_balance
                # --- FIX: Must be based on prior_revolver, not iteration guess ---
                new_ending_revolver = prior_revolver + revolver_draw
                
            elif cash_available > drivers.min_cash_balance and prior_revolver > 0:
                # Pay down revolver (cash sweep)
                excess_cash = cash_available - drivers.min_cash_balance
                revolver_paydown = min(excess_cash, prior_revolver)
                new_ending_cash = cash_available - revolver_paydown
                # --- FIX: Must be based on prior_revolver, not iteration guess ---
                new_ending_revolver = prior_revolver - revolver_paydown
                revolver_draw = -revolver_paydown
            else:
                # Keep cash as is
                new_ending_cash = cash_available
                # --- FIX: Must be based on prior_revolver, not iteration guess ---
                new_ending_revolver = prior_revolver
                revolver_draw = 0.0
            
            # Check convergence (only cash and revolver are circular)
            cash_error = abs(new_ending_cash - ending_cash)
            revolver_error = abs(new_ending_revolver - ending_revolver)
            
            if cash_error < TOLERANCE and revolver_error < TOLERANCE:
                # Converged!
                ending_cash = new_ending_cash
                ending_revolver = new_ending_revolver
                break
            
            # Update for next iteration
            ending_cash = new_ending_cash
            ending_revolver = new_ending_revolver
        
        else:
            logger.warning(f"Circular reference did not converge for {period} after {MAX_ITERATIONS} iterations")
        
        # ================================================================
        # Step 6: Complete Equity Roll-Forward
        # ================================================================
        # Equity = Prior Equity + Net Income - Dividends + Share Issuances - Repurchases
        # For now, no issuances/repurchases
        ending_equity = prior_equity + net_income - dividends
        
        # ================================================================
        # Step 7: Assemble Balance Sheet & Validate
        # ================================================================
        total_assets = ending_cash + ar + inventory + ppe_net + goodwill
        total_liabilities = ap + accrued_liabilities + ending_debt + ending_revolver
        total_liab_equity = total_liabilities + ending_equity
        
        balance_error = abs(total_assets - total_liab_equity)
        balance_check = balance_error < 1.0  # $1 tolerance
        
        if not balance_check:
            logger.warning(f"{period}: Balance sheet error = ${balance_error:,.2f}")
        
        # ================================================================
        # Step 8: Assemble Cash Flow Statement
        # ================================================================
        cff = -debt_payment + revolver_draw - dividends
        net_cash_flow = cfo + cfi + cff
        
        # Validation: net_cash_flow should equal change in cash
        expected_cash_change = ending_cash - prior_cash
        if abs(net_cash_flow - expected_cash_change) > 0.01:
            logger.warning(f"{period}: Cash flow mismatch: {net_cash_flow:.2f} vs {expected_cash_change:.2f}")
        
        # ================================================================
        # Return complete year result
        # ================================================================
        return YearResult(
            period=period,
            revenue=revenue,
            cogs=cogs,
            gross_profit=gross_profit,
            sga=sga,
            rnd=rnd,
            da=da,
            sbc=sbc,
            ebitda=ebitda,
            ebit=ebit,
            interest_expense=interest_expense,
            interest_income=interest_income,
            ebt=ebt,
            taxes=taxes,
            net_income=net_income,
            beg_cash=prior_cash,
            beg_debt=prior_debt,
            beg_revolver=prior_revolver,
            beg_equity=prior_equity,
            beg_ppe_net=prior_ppe_net,
            cash=ending_cash,
            ar=ar,
            inventory=inventory,
            ppe_net=ppe_net,
            goodwill=goodwill,
            total_assets=total_assets,
            ap=ap,
            accrued_liabilities=accrued_liabilities,
            debt=ending_debt,
            revolver=ending_revolver,
            total_liabilities=total_liabilities,
            equity=ending_equity,
            total_liab_equity=total_liab_equity,
            cfo=cfo,
            capex=capex,  # --- FIX: Store positive expense ---
            cfi=cfi,
            dividends=dividends,
            debt_payment=debt_payment,
            revolver_draw=revolver_draw,
            cff=cff,
            net_cash_flow=net_cash_flow,
            balance_check=balance_check,
            balance_error=balance_error
        )
    
    def build_integrated_model(
        self,
        historical: HistoricalData,
        drivers: DriverInputs,
        forecast_years: int = 5
    ) -> ThreeStatementResult:
        """
        Build truly integrated 3-statement model
        NO PLUGS - everything flows naturally
        """
        
        logger.info(f"Building integrated model: {len(historical.periods)} historical + {forecast_years} forecast")
        
        # Validate historical data
        self._validate_historical_data(historical)
        
        all_years: List[YearResult] = []
        
        # ================================================================
        # Build Historical Years (just convert to YearResult format)
        # ================================================================
        for i, period in enumerate(historical.periods):
            # Calculate values needed for packaging
            ebitda = historical.revenue[i] - historical.cogs[i] - historical.sga[i] - historical.rnd[i]
            ebit = ebitda - historical.da[i]
            ebt = ebit - historical.interest_expense[i] + historical.interest_income[i]
            assets = historical.cash[i] + historical.ar[i] + historical.inventory[i] + historical.ppe_net[i] + historical.goodwill[i]
            liab = historical.ap[i] + historical.accrued_liabilities[i] + historical.debt[i]
            
            # --- FIX: Use np.nan for i=0 "Beginning" balances ---
            beg_cash = historical.cash[i-1] if i > 0 else np.nan
            beg_debt = historical.debt[i-1] if i > 0 else np.nan
            beg_equity = historical.equity[i-1] if i > 0 else np.nan
            beg_ppe_net = historical.ppe_net[i-1] if i > 0 else np.nan
            net_cash_flow = historical.cash[i] - beg_cash if i > 0 else np.nan
            
            # Historical is already balanced, just package it
            year = YearResult(
                period=period,
                revenue=historical.revenue[i],
                cogs=historical.cogs[i],
                gross_profit=historical.revenue[i] - historical.cogs[i],
                sga=historical.sga[i],
                rnd=historical.rnd[i],
                da=historical.da[i],
                sbc=historical.sbc[i] if historical.sbc else 0.0,
                ebitda=ebitda,
                ebit=ebit,
                interest_expense=historical.interest_expense[i],
                interest_income=historical.interest_income[i],
                ebt=ebt,
                taxes=historical.taxes[i],
                net_income=historical.net_income[i],
                beg_cash=beg_cash,
                beg_debt=beg_debt,
                beg_revolver=0.0,
                beg_equity=beg_equity,
                beg_ppe_net=beg_ppe_net,
                cash=historical.cash[i],
                ar=historical.ar[i],
                inventory=historical.inventory[i],
                ppe_net=historical.ppe_net[i],
                goodwill=historical.goodwill[i],
                total_assets=assets,
                ap=historical.ap[i],
                accrued_liabilities=historical.accrued_liabilities[i],
                debt=historical.debt[i],
                revolver=0.0,
                total_liabilities=liab,
                equity=historical.equity[i],
                total_liab_equity=liab + historical.equity[i],
                cfo=np.nan,  # Can't derive from partial data
                capex=historical.capex[i], # --- FIX: Store positive ---
                cfi=-historical.capex[i], # --- FIX: CFI is negative ---
                dividends=historical.dividends[i] if historical.dividends else 0.0,
                debt_payment=np.nan,
                revolver_draw=np.nan,
                cff=np.nan,
                net_cash_flow=net_cash_flow,
                balance_check=True,
                balance_error=0.0
            )
            all_years.append(year)
        
        # ================================================================
        # Build Forecast Years (year-by-year with circular references)
        # ================================================================
        for year_idx in range(forecast_years):
            period = f"FY+{year_idx + 1}"
            
            # Get prior year (last forecast year or last historical year)
            prior = all_years[-1]
            
            # --- FIX: Simplified revenue calculation (no if/else needed) ---
            revenue = prior.revenue * (1 + drivers.revenue_growth_rates[year_idx])
            
            # Build the year
            year = self._build_one_year(
                period=period,
                is_forecast=True,
                revenue=revenue,
                drivers=drivers,
                driver_idx=year_idx,
                prior_cash=prior.cash,
                prior_ar=prior.ar,
                prior_inventory=prior.inventory,
                prior_ppe_net=prior.ppe_net,
                prior_goodwill=prior.goodwill,
                prior_ap=prior.ap,
                prior_accrued=prior.accrued_liabilities,
                prior_debt=prior.debt,
                prior_revolver=prior.revolver,
                prior_equity=prior.equity
            )
            
            all_years.append(year)
        
        # ================================================================
        # Convert to DataFrames
        # ================================================================
        is_data = []
        bs_data = []
        cf_data = []
        
        for year in all_years:
            is_data.append({
                'Period': year.period,
                'Revenue': year.revenue,
                'COGS': year.cogs,
                'Gross_Profit': year.gross_profit,
                'Gross_Margin_%': (year.gross_profit / year.revenue * 100) if year.revenue > 0 else 0,
                'SGA': year.sga,
                'RD': year.rnd,
                'DA': year.da,
                'SBC': year.sbc,
                'EBITDA': year.ebitda,
                'EBITDA_Margin_%': (year.ebitda / year.revenue * 100) if year.revenue > 0 else 0,
                'EBIT': year.ebit,
                'EBIT_Margin_%': (year.ebit / year.revenue * 100) if year.revenue > 0 else 0,
                'Interest_Expense': year.interest_expense,
                'Interest_Income': year.interest_income,
                'Net_Interest': year.interest_income - year.interest_expense,
                'EBT': year.ebt,
                'Taxes': year.taxes,
                'Tax_Rate_%': (year.taxes / year.ebt * 100) if year.ebt > 0 else 0,
                'Net_Income': year.net_income,
                'Net_Margin_%': (year.net_income / year.revenue * 100) if year.revenue > 0 else 0
            })
            
            bs_data.append({
                'Period': year.period,
                'Cash': year.cash,
                'AR': year.ar,
                'Inventory': year.inventory,
                'Current_Assets': year.cash + year.ar + year.inventory,
                'PPE_Net': year.ppe_net,
                'Goodwill': year.goodwill,
                'Total_Assets': year.total_assets,
                'AP': year.ap,
                'Accrued_Liabilities': year.accrued_liabilities,
                'Current_Liabilities': year.ap + year.accrued_liabilities,
                'Debt': year.debt,
                'Revolver': year.revolver,
                'Total_Debt': year.debt + year.revolver,
                'Total_Liabilities': year.total_liabilities,
                'Equity': year.equity,
                'Total_Liab_Equity': year.total_liab_equity,
                'Balance_Check': year.balance_check,
                'Balance_Error': year.balance_error
            })
            
            cf_data.append({
                'Period': year.period,
                'Net_Income': year.net_income,
                'DA': year.da,
                'SBC': year.sbc,
                'CFO': year.cfo,
                'CapEx': -year.capex, # --- FIX: Show negative on CF statement ---
                'CFI': year.cfi,
                'FCF': year.cfo + year.cfi,
                'Debt_Payment': -year.debt_payment,
                'Revolver_Draw': year.revolver_draw,
                'Dividends': -year.dividends,
                'CFF': year.cff,
                'Net_Cash_Flow': year.net_cash_flow
            })
        
        income_statement = pd.DataFrame(is_data)
        balance_sheet = pd.DataFrame(bs_data)
        cash_flow = pd.DataFrame(cf_data)
        
        # Extract forecast metrics
        forecast_start_idx = len(historical.periods)
        fcf_forecast = cash_flow['FCF'].iloc[forecast_start_idx:].tolist()
        ebitda_forecast = income_statement['EBITDA'].iloc[forecast_start_idx:].tolist()
        net_income_forecast = income_statement['Net_Income'].iloc[forecast_start_idx:].tolist()
        
        # Validation
        all_balance_checks = all(year.balance_check for year in all_years)
        max_error = max(abs(year.balance_error) for year in all_years)
        
        logger.info(f"✓ Model complete: {len(all_years)} periods")
        logger.info(f"✓ All balance sheets validate: {all_balance_checks}")
        logger.info(f"✓ Max balance error: ${max_error:,.2f}")
        
        return ThreeStatementResult(
            years=all_years,
            historical_periods=historical.periods,
            forecast_periods=[f"FY+{i+1}" for i in range(forecast_years)],
            income_statement=income_statement,
            balance_sheet=balance_sheet,
            cash_flow_statement=cash_flow,
            fcf_forecast=fcf_forecast,
            ebitda_forecast=ebitda_forecast,
            net_income_forecast=net_income_forecast,
            all_balance_checks_pass=all_balance_checks,
            max_balance_error=max_error
        )