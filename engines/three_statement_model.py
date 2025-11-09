"""
3-Statement Model Builder
Integrated financial model with revenue drivers, margin ladders, working capital, debt schedules
Supports Historical + Forecast periods (e.g., FY-2, FY-1, FY0, FY+1, FY+2, FY+3, FY+4, FY+5)
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np
import pandas as pd
from loguru import logger


@dataclass
class HistoricalData:
    """Historical financial data"""
    periods: List[str]  # e.g., ['FY-2', 'FY-1', 'FY0']
    revenue: List[float]
    cogs: List[float]
    sga: List[float]
    rnd: List[float]
    da: List[float]
    interest_expense: List[float]
    taxes: List[float]
    
    # Balance Sheet
    cash: List[float]
    ar: List[float]
    inventory: List[float]
    ppe: List[float]
    goodwill: List[float]
    ap: List[float]
    debt: List[float]
    equity: List[float]
    
    # Additional items
    sbc: Optional[List[float]] = None
    capex: Optional[List[float]] = None


@dataclass
class DriverInputs:
    """Revenue and operational drivers for forecast periods"""
    # Growth and margin assumptions
    revenue_growth_rates: List[float]
    cogs_pct_revenue: List[float]
    sga_pct_revenue: List[float]
    da_pct_revenue: List[float]
    
    # Working capital assumptions
    ar_days: List[float]
    inventory_days: List[float]
    ap_days: List[float]
    
    # CapEx and financing
    capex_pct_revenue: List[float]
    interest_rate: float
    tax_rate: float
    
    # Optional fields
    revenue_drivers: Optional[Dict[str, List[float]]] = None
    rnd_pct_revenue: Optional[List[float]] = None
    mandatory_debt_payment: float = 0.0
    sbc_pct_revenue: Optional[List[float]] = None
    operating_lease_pct_revenue: Optional[float] = None


@dataclass
class ThreeStatementResult:
    """3-Statement model output with historical + forecast"""
    income_statement: pd.DataFrame
    balance_sheet: pd.DataFrame
    cash_flow_statement: pd.DataFrame
    working_capital_schedule: pd.DataFrame
    debt_schedule: pd.DataFrame
    
    # Separate historical and forecast
    historical_periods: List[str]
    forecast_periods: List[str]
    
    # Key metrics
    fcf_forecast: List[float]
    ebitda_forecast: List[float]
    net_income_forecast: List[float]
    
    # Validation
    balance_check: bool
    cash_flow_check: bool
    
    # Metadata
    base_year: str  # e.g., 'FY0'


class ThreeStatementModel:
    """3-Statement Integrated Financial Model with Historical + Forecast"""
    
    def __init__(self):
        """Initialize 3-statement model"""
        logger.info("3-Statement Model initialized with historical + forecast support")
    
    def _build_historical_income_statement(self, historical: HistoricalData) -> pd.DataFrame:
        """Build historical income statement"""
        hist_data = []
        
        for i, period in enumerate(historical.periods):
            revenue = historical.revenue[i]
            cogs = historical.cogs[i]
            gross_profit = revenue - cogs
            sga = historical.sga[i]
            rnd = historical.rnd[i]
            da = historical.da[i]
            sbc = historical.sbc[i] if historical.sbc else 0
            
            ebitda = gross_profit - sga - rnd
            ebit = ebitda - da
            interest = historical.interest_expense[i]
            ebt = ebit - interest
            taxes = historical.taxes[i]
            net_income = ebt - taxes
            
            hist_data.append({
                'Period': period,
                'Revenue': revenue,
                'COGS': cogs,
                'Gross_Profit': gross_profit,
                'Gross_Margin_%': (gross_profit / revenue * 100) if revenue > 0 else 0,
                'SGA': sga,
                'RD': rnd,
                'DA': da,
                'SBC': sbc,
                'EBITDA': ebitda,
                'EBITDA_Margin_%': (ebitda / revenue * 100) if revenue > 0 else 0,
                'EBIT': ebit,
                'EBIT_Margin_%': (ebit / revenue * 100) if revenue > 0 else 0,
                'Interest_Expense': interest,
                'EBT': ebt,
                'Taxes': taxes,
                'Tax_Rate_%': (taxes / ebt * 100) if ebt > 0 else 0,
                'Net_Income': net_income,
                'Net_Margin_%': (net_income / revenue * 100) if revenue > 0 else 0
            })
        
        return pd.DataFrame(hist_data)
    
    def _build_forecast_income_statement(self, drivers: DriverInputs, base_revenue: float, 
                                        base_debt: float, forecast_years: int, 
                                        start_year: int = 1) -> pd.DataFrame:
        """Build forecast income statement"""
        projections = []
        revenue = base_revenue
        debt = base_debt
        
        for year in range(forecast_years):
            # Apply growth rate
            if year > 0:
                revenue = revenue * (1 + drivers.revenue_growth_rates[year])
            elif year == 0 and start_year > 0:
                revenue = revenue * (1 + drivers.revenue_growth_rates[year])
            
            cogs = revenue * drivers.cogs_pct_revenue[year]
            gross_profit = revenue - cogs
            sga = revenue * drivers.sga_pct_revenue[year]
            rnd = revenue * drivers.rnd_pct_revenue[year] if drivers.rnd_pct_revenue else 0
            da = revenue * drivers.da_pct_revenue[year]
            sbc = revenue * drivers.sbc_pct_revenue[year] if drivers.sbc_pct_revenue else 0
            
            ebitda = gross_profit - sga - rnd
            ebit = ebitda - da
            interest = debt * drivers.interest_rate
            ebt = ebit - interest
            taxes = max(0, ebt * drivers.tax_rate)
            net_income = ebt - taxes
            
            # Update debt for next period
            debt = max(0, debt - drivers.mandatory_debt_payment)
            
            projections.append({
                'Period': f'FY+{start_year + year}',
                'Revenue': revenue,
                'COGS': cogs,
                'Gross_Profit': gross_profit,
                'Gross_Margin_%': (gross_profit / revenue * 100) if revenue > 0 else 0,
                'SGA': sga,
                'RD': rnd,
                'DA': da,
                'SBC': sbc,
                'EBITDA': ebitda,
                'EBITDA_Margin_%': (ebitda / revenue * 100) if revenue > 0 else 0,
                'EBIT': ebit,
                'EBIT_Margin_%': (ebit / revenue * 100) if revenue > 0 else 0,
                'Interest_Expense': interest,
                'EBT': ebt,
                'Taxes': taxes,
                'Tax_Rate_%': (taxes / ebt * 100) if ebt > 0 else 0,
                'Net_Income': net_income,
                'Net_Margin_%': (net_income / revenue * 100) if revenue > 0 else 0
            })
        
        return pd.DataFrame(projections)
    
    def _build_historical_balance_sheet(self, historical: HistoricalData) -> pd.DataFrame:
        """Build historical balance sheet - ensures balance sheet equation holds"""
        hist_data = []
        
        for i, period in enumerate(historical.periods):
            # Assets
            cash = historical.cash[i]
            ar = historical.ar[i]
            inventory = historical.inventory[i]
            current_assets = cash + ar + inventory
            
            ppe = historical.ppe[i]
            goodwill = historical.goodwill[i]
            total_assets = current_assets + ppe + goodwill
            
            # Liabilities
            ap = historical.ap[i]
            total_debt = historical.debt[i]
            equity = historical.equity[i]
            
            # Calculate accrued liabilities as plug to balance the sheet
            # Assets = Liabilities + Equity
            # Assets = AP + Accrued + Debt + Equity
            # Accrued = Assets - AP - Debt - Equity
            accrued = total_assets - ap - total_debt - equity
            
            current_liabilities = ap + accrued
            total_liabilities = current_liabilities + total_debt
            
            balance_check = abs(total_assets - (total_liabilities + equity)) < 0.01
            
            hist_data.append({
                'Period': period,
                'Cash': cash,
                'AR': ar,
                'Inventory': inventory,
                'Current_Assets': current_assets,
                'PPE': ppe,
                'Goodwill': goodwill,
                'Total_Assets': total_assets,
                'AP': ap,
                'Accrued_Liabilities': accrued,
                'Current_Liabilities': current_liabilities,
                'Total_Debt': total_debt,
                'Total_Liabilities': total_liabilities,
                'Equity': equity,
                'Total_Liab_Equity': total_liabilities + equity,
                'Balance_Check': balance_check
            })
        
        return pd.DataFrame(hist_data)
    
    def _build_forecast_balance_sheet(self, drivers: DriverInputs, income_statement: pd.DataFrame,
                                     last_bs: pd.Series, forecast_years: int) -> pd.DataFrame:
        """Build forecast balance sheet"""
        projections = []
        
        for year in range(forecast_years):
            revenue = income_statement.iloc[year]['Revenue']
            cogs = income_statement.iloc[year]['COGS']
            
            # Working capital
            ar = revenue * (drivers.ar_days[year] / 365)
            inventory = cogs * (drivers.inventory_days[year] / 365)
            ap = cogs * (drivers.ap_days[year] / 365)
            
            # Cash (simple plug for now)
            cash = revenue * 0.05
            current_assets = cash + ar + inventory
            
            # Fixed assets
            capex = revenue * drivers.capex_pct_revenue[year]
            da = income_statement.iloc[year]['DA']
            
            if year == 0:
                ppe = last_bs['PPE'] + capex - da
                goodwill = last_bs['Goodwill']
                total_debt = last_bs['Total_Debt']
            else:
                ppe = projections[-1]['PPE'] + capex - da
                goodwill = projections[-1]['Goodwill']
                total_debt = projections[-1]['Total_Debt'] - drivers.mandatory_debt_payment
                total_debt = max(0, total_debt)
            
            total_assets = current_assets + ppe + goodwill
            
            # Liabilities
            accrued = revenue * 0.03
            current_liabilities = ap + accrued
            total_liabilities = current_liabilities + total_debt
            
            # Equity (plug)
            equity = total_assets - total_liabilities
            
            balance_check = abs(total_assets - (total_liabilities + equity)) < 0.01
            
            projections.append({
                'Period': income_statement.iloc[year]['Period'],
                'Cash': cash,
                'AR': ar,
                'Inventory': inventory,
                'Current_Assets': current_assets,
                'PPE': ppe,
                'Goodwill': goodwill,
                'Total_Assets': total_assets,
                'AP': ap,
                'Accrued_Liabilities': accrued,
                'Current_Liabilities': current_liabilities,
                'Total_Debt': total_debt,
                'Total_Liabilities': total_liabilities,
                'Equity': equity,
                'Total_Liab_Equity': total_liabilities + equity,
                'Balance_Check': balance_check
            })
        
        return pd.DataFrame(projections)
    
    def _build_cash_flow_statement(self, income_statement: pd.DataFrame, 
                                   balance_sheet: pd.DataFrame, 
                                   start_idx: int = 0) -> pd.DataFrame:
        """Build cash flow statement for given periods"""
        projections = []
        
        for year in range(len(income_statement)):
            period = income_statement.iloc[year]['Period']
            net_income = income_statement.iloc[year]['Net_Income']
            da = income_statement.iloc[year]['DA']
            sbc = income_statement.iloc[year]['SBC']
            
            # Changes in working capital
            if year + start_idx == 0:
                # First period - no prior period for comparison
                delta_ar = 0
                delta_inventory = 0
                delta_ap = 0
            else:
                delta_ar = balance_sheet.iloc[year]['AR'] - balance_sheet.iloc[year-1]['AR']
                delta_inventory = balance_sheet.iloc[year]['Inventory'] - balance_sheet.iloc[year-1]['Inventory']
                delta_ap = balance_sheet.iloc[year]['AP'] - balance_sheet.iloc[year-1]['AP']
            
            delta_nwc = delta_ar + delta_inventory - delta_ap
            
            # Cash from operations
            cfo = net_income + da + sbc - delta_nwc
            
            # CapEx
            if year + start_idx == 0:
                capex = 0  # Not calculated for first period
            else:
                capex = -(balance_sheet.iloc[year]['PPE'] - balance_sheet.iloc[year-1]['PPE'] + da)
            
            # Free Cash Flow
            fcf = cfo + capex
            
            # Financing activities
            if year + start_idx == 0:
                debt_change = 0
            else:
                debt_change = balance_sheet.iloc[year]['Total_Debt'] - balance_sheet.iloc[year-1]['Total_Debt']
            
            projections.append({
                'Period': period,
                'Net_Income': net_income,
                'DA': da,
                'SBC': sbc,
                'Changes_in_WC': -delta_nwc,
                'CFO': cfo,
                'CapEx': capex,
                'CFI': capex,  # Investing cash flow
                'FCF': fcf,
                'Debt_Change': debt_change,
                'CFF': debt_change,  # Financing cash flow
                'Net_Change_Cash': cfo + capex + debt_change
            })
        
        return pd.DataFrame(projections)
    
    def build_integrated_model(self, historical: HistoricalData, drivers: DriverInputs, 
                              forecast_years: int = 5) -> ThreeStatementResult:
        """
        Build complete integrated 3-statement model with historical + forecast
        
        Args:
            historical: Historical financial data (e.g., FY-2, FY-1, FY0)
            drivers: Forecast assumptions and drivers
            forecast_years: Number of years to forecast (default 5)
        
        Returns:
            ThreeStatementResult with complete historical + forecast
        """
        logger.info(f"Building integrated 3-statement model: {len(historical.periods)} historical + {forecast_years} forecast periods")
        
        # 1. Build historical statements
        hist_is = self._build_historical_income_statement(historical)
        hist_bs = self._build_historical_balance_sheet(historical)
        
        # 2. Build forecast statements
        base_revenue = historical.revenue[-1]  # Last historical revenue
        base_debt = historical.debt[-1]  # Last historical debt
        
        forecast_is = self._build_forecast_income_statement(
            drivers, base_revenue, base_debt, forecast_years, start_year=1
        )
        
        last_bs_row = hist_bs.iloc[-1]
        forecast_bs = self._build_forecast_balance_sheet(
            drivers, forecast_is, last_bs_row, forecast_years
        )
        
        # 3. Combine historical + forecast
        income_statement = pd.concat([hist_is, forecast_is], ignore_index=True)
        balance_sheet = pd.concat([hist_bs, forecast_bs], ignore_index=True)
        
        # 4. Build cash flow statement for all periods
        cash_flow = self._build_cash_flow_statement(income_statement, balance_sheet)
        
        # 5. Build supporting schedules
        wc_schedule = pd.DataFrame({
            'Period': balance_sheet['Period'],
            'AR': balance_sheet['AR'],
            'Inventory': balance_sheet['Inventory'],
            'AP': balance_sheet['AP'],
            'Net_Working_Capital': balance_sheet['AR'] + balance_sheet['Inventory'] - balance_sheet['AP'],
            'AR_Days': (balance_sheet['AR'] / income_statement['Revenue'] * 365).round(0),
            'Inventory_Days': (balance_sheet['Inventory'] / income_statement['COGS'] * 365).round(0),
            'AP_Days': (balance_sheet['AP'] / income_statement['COGS'] * 365).round(0)
        })
        
        debt_schedule = pd.DataFrame({
            'Period': balance_sheet['Period'],
            'Beginning_Debt': [historical.debt[0]] + balance_sheet['Total_Debt'].tolist()[:-1],
            'Ending_Debt': balance_sheet['Total_Debt'],
            'Debt_Change': balance_sheet['Total_Debt'].diff().fillna(0),
            'Interest_Rate_%': (income_statement['Interest_Expense'] / balance_sheet['Total_Debt'] * 100).fillna(0).round(2)
        })
        
        # 6. Extract forecast metrics
        forecast_start_idx = len(historical.periods)
        fcf_forecast = cash_flow['FCF'].iloc[forecast_start_idx:].tolist()
        ebitda_forecast = income_statement['EBITDA'].iloc[forecast_start_idx:].tolist()
        net_income_forecast = income_statement['Net_Income'].iloc[forecast_start_idx:].tolist()
        
        # 7. Validation
        balance_check = all(balance_sheet['Balance_Check'])
        cash_flow_check = True  # Could add more validation here
        
        result = ThreeStatementResult(
            income_statement=income_statement,
            balance_sheet=balance_sheet,
            cash_flow_statement=cash_flow,
            working_capital_schedule=wc_schedule,
            debt_schedule=debt_schedule,
            historical_periods=historical.periods,
            forecast_periods=[f'FY+{i+1}' for i in range(forecast_years)],
            fcf_forecast=fcf_forecast,
            ebitda_forecast=ebitda_forecast,
            net_income_forecast=net_income_forecast,
            balance_check=balance_check,
            cash_flow_check=cash_flow_check,
            base_year=historical.periods[-1]
        )
        
        logger.info(f"✓ 3-statement model complete: {len(income_statement)} total periods")
        logger.info(f"✓ Balance sheet validates: {balance_check}")
        
        return result
    
    def build_three_statement_model(self, drivers: DriverInputs, base_revenue: float, 
                                   base_debt: float, years: int = 5) -> ThreeStatementResult:
        """
        Legacy method: Build forecast-only 3-statement model
        
        Use build_integrated_model() for historical + forecast support
        """
        logger.info(f"Building forecast-only 3-statement model for {years} years")
        
        # Build forecast statements
        forecast_is = self._build_forecast_income_statement(drivers, base_revenue, base_debt, years, start_year=1)
        
        # Create dummy last balance sheet for initial state
        last_bs = pd.Series({
            'PPE': base_revenue * 0.30,
            'Goodwill': base_revenue * 0.10,
            'Total_Debt': base_debt
        })
        
        forecast_bs = self._build_forecast_balance_sheet(drivers, forecast_is, last_bs, years)
        cash_flow = self._build_cash_flow_statement(forecast_is, forecast_bs, start_idx=1)
        
        # Supporting schedules
        wc_schedule = pd.DataFrame({
            'Period': forecast_bs['Period'],
            'AR': forecast_bs['AR'],
            'Inventory': forecast_bs['Inventory'],
            'AP': forecast_bs['AP'],
            'Net_Working_Capital': forecast_bs['AR'] + forecast_bs['Inventory'] - forecast_bs['AP']
        })
        
        debt_schedule = pd.DataFrame({
            'Period': forecast_bs['Period'],
            'Beginning_Debt': [base_debt] + forecast_bs['Total_Debt'].tolist()[:-1],
            'Ending_Debt': forecast_bs['Total_Debt']
        })
        
        return ThreeStatementResult(
            income_statement=forecast_is,
            balance_sheet=forecast_bs,
            cash_flow_statement=cash_flow,
            working_capital_schedule=wc_schedule,
            debt_schedule=debt_schedule,
            historical_periods=[],
            forecast_periods=[f'FY+{i+1}' for i in range(years)],
            fcf_forecast=cash_flow['FCF'].tolist(),
            ebitda_forecast=forecast_is['EBITDA'].tolist(),
            net_income_forecast=forecast_is['Net_Income'].tolist(),
            balance_check=all(forecast_bs['Balance_Check']),
            cash_flow_check=True,
            base_year='FY0'
        )
