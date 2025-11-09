"""
Last Twelve Months (LTM) Calculator
Normalizes quarterly financial data to trailing twelve months for comparability
"""

from typing import List, Dict, Any, Optional
from loguru import logger
from datetime import datetime


class LTMCalculator:
    """
    Calculate Last Twelve Months (LTM) metrics from quarterly data
    
    LTM provides more current financial metrics than annual data by:
    - Using the 4 most recent quarters
    - Summing income statement/cash flow items (flow metrics)
    - Using most recent balance sheet (point-in-time metrics)
    - Enabling apples-to-apples comparison regardless of fiscal year
    """
    
    @staticmethod
    def calculate_ltm_income_statement(
        quarterly_statements: List[Dict[str, Any]],
        num_quarters: int = 4
    ) -> Dict[str, Any]:
        """
        Calculate LTM income statement from quarterly data
        
        Args:
            quarterly_statements: List of quarterly income statements (most recent first)
            num_quarters: Number of quarters to sum (typically 4 for LTM)
            
        Returns:
            LTM income statement dictionary
        """
        if not quarterly_statements or len(quarterly_statements) < num_quarters:
            logger.warning(f"Insufficient quarterly data for LTM calculation. Need {num_quarters}, got {len(quarterly_statements)}")
            return {}
        
        # Take the most recent N quarters
        quarters_to_sum = quarterly_statements[:num_quarters]
        
        # Fields to sum (flow metrics)
        flow_fields = [
            'revenue', 'costOfRevenue', 'grossProfit', 
            'grossProfitRatio', 'researchAndDevelopmentExpenses',
            'generalAndAdministrativeExpenses', 'sellingAndMarketingExpenses',
            'sellingGeneralAndAdministrativeExpenses', 'otherExpenses',
            'operatingExpenses', 'costAndExpenses', 'interestExpense',
            'interestIncome', 'depreciationAndAmortization', 'ebitda',
            'ebitdaratio', 'operatingIncome', 'operatingIncomeRatio',
            'totalOtherIncomeExpensesNet', 'incomeBeforeTax',
            'incomeBeforeTaxRatio', 'incomeTaxExpense', 'netIncome',
            'netIncomeRatio', 'eps', 'epsdiluted', 
            'weightedAverageShsOut', 'weightedAverageShsOutDil'
        ]
        
        ltm_statement = {
            'date': quarters_to_sum[0].get('date'),  # Most recent quarter date
            'period': 'LTM',
            'calendarYear': quarters_to_sum[0].get('calendarYear'),
            'reportedCurrency': quarters_to_sum[0].get('reportedCurrency', 'USD'),
            'cik': quarters_to_sum[0].get('cik'),
            'fillingDate': quarters_to_sum[0].get('fillingDate'),
            'acceptedDate': quarters_to_sum[0].get('acceptedDate'),
            'link': quarters_to_sum[0].get('link'),
            'finalLink': quarters_to_sum[0].get('finalLink')
        }
        
        # Sum flow metrics across quarters
        for field in flow_fields:
            ltm_value = 0
            for quarter in quarters_to_sum:
                value = quarter.get(field)
                if value is not None:
                    try:
                        ltm_value += float(value)
                    except (ValueError, TypeError):
                        continue
            
            ltm_statement[field] = ltm_value if ltm_value != 0 else None
        
        # Recalculate ratios based on LTM values
        if ltm_statement.get('revenue') and ltm_statement.get('revenue') != 0:
            if ltm_statement.get('grossProfit') is not None:
                ltm_statement['grossProfitRatio'] = ltm_statement['grossProfit'] / ltm_statement['revenue']
            if ltm_statement.get('ebitda') is not None:
                ltm_statement['ebitdaratio'] = ltm_statement['ebitda'] / ltm_statement['revenue']
            if ltm_statement.get('operatingIncome') is not None:
                ltm_statement['operatingIncomeRatio'] = ltm_statement['operatingIncome'] / ltm_statement['revenue']
            if ltm_statement.get('incomeBeforeTax') is not None:
                ltm_statement['incomeBeforeTaxRatio'] = ltm_statement['incomeBeforeTax'] / ltm_statement['revenue']
            if ltm_statement.get('netIncome') is not None:
                ltm_statement['netIncomeRatio'] = ltm_statement['netIncome'] / ltm_statement['revenue']
        
        # Recalculate EPS using average shares outstanding
        if ltm_statement.get('netIncome') and ltm_statement.get('weightedAverageShsOut'):
            ltm_statement['eps'] = ltm_statement['netIncome'] / ltm_statement['weightedAverageShsOut']
        if ltm_statement.get('netIncome') and ltm_statement.get('weightedAverageShsOutDil'):
            ltm_statement['epsdiluted'] = ltm_statement['netIncome'] / ltm_statement['weightedAverageShsOutDil']
        
        logger.debug(f"LTM Income Statement calculated from {num_quarters} quarters")
        return ltm_statement
    
    @staticmethod
    def calculate_ltm_cash_flow(
        quarterly_statements: List[Dict[str, Any]],
        num_quarters: int = 4
    ) -> Dict[str, Any]:
        """
        Calculate LTM cash flow statement from quarterly data
        
        Args:
            quarterly_statements: List of quarterly cash flow statements (most recent first)
            num_quarters: Number of quarters to sum (typically 4 for LTM)
            
        Returns:
            LTM cash flow statement dictionary
        """
        if not quarterly_statements or len(quarterly_statements) < num_quarters:
            logger.warning(f"Insufficient quarterly data for LTM cash flow calculation. Need {num_quarters}, got {len(quarterly_statements)}")
            return {}
        
        quarters_to_sum = quarterly_statements[:num_quarters]
        
        # Fields to sum (all cash flow items are flow metrics)
        flow_fields = [
            'netIncome', 'depreciationAndAmortization', 'deferredIncomeTax',
            'stockBasedCompensation', 'changeInWorkingCapital',
            'accountsReceivables', 'inventory', 'accountsPayables',
            'otherWorkingCapital', 'otherNonCashItems',
            'netCashProvidedByOperatingActivities',
            'investmentsInPropertyPlantAndEquipment', 'acquisitionsNet',
            'purchasesOfInvestments', 'salesMaturitiesOfInvestments',
            'otherInvestingActivites', 'netCashUsedForInvestingActivites',
            'debtRepayment', 'commonStockIssued', 'commonStockRepurchased',
            'dividendsPaid', 'otherFinancingActivites',
            'netCashUsedProvidedByFinancingActivities',
            'effectOfForexChangesOnCash', 'netChangeInCash',
            'cashAtEndOfPeriod', 'cashAtBeginningOfPeriod',
            'operatingCashFlow', 'capitalExpenditure', 'freeCashFlow'
        ]
        
        ltm_statement = {
            'date': quarters_to_sum[0].get('date'),
            'period': 'LTM',
            'reportedCurrency': quarters_to_sum[0].get('reportedCurrency', 'USD'),
            'cik': quarters_to_sum[0].get('cik'),
            'fillingDate': quarters_to_sum[0].get('fillingDate'),
            'acceptedDate': quarters_to_sum[0].get('acceptedDate'),
            'link': quarters_to_sum[0].get('link'),
            'finalLink': quarters_to_sum[0].get('finalLink')
        }
        
        # Sum flow metrics
        for field in flow_fields:
            # Skip beginning/end cash (not additive)
            if field in ['cashAtEndOfPeriod', 'cashAtBeginningOfPeriod']:
                ltm_statement[field] = quarters_to_sum[0].get(field)
                continue
            
            ltm_value = 0
            for quarter in quarters_to_sum:
                value = quarter.get(field)
                if value is not None:
                    try:
                        ltm_value += float(value)
                    except (ValueError, TypeError):
                        continue
            
            ltm_statement[field] = ltm_value if ltm_value != 0 else None
        
        logger.debug(f"LTM Cash Flow Statement calculated from {num_quarters} quarters")
        return ltm_statement
    
    @staticmethod
    def get_latest_balance_sheet(
        quarterly_statements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get most recent balance sheet (balance sheet is point-in-time, not summed)
        
        Args:
            quarterly_statements: List of quarterly balance sheets (most recent first)
            
        Returns:
            Most recent balance sheet with period marked as LTM
        """
        if not quarterly_statements:
            logger.warning("No quarterly balance sheet data available")
            return {}
        
        latest_bs = quarterly_statements[0].copy()
        latest_bs['period'] = 'LTM'  # Mark as LTM for consistency
        latest_bs['note'] = 'Point-in-time snapshot (most recent quarter)'
        
        logger.debug("Using most recent balance sheet for LTM analysis")
        return latest_bs
    
    @staticmethod
    def calculate_ltm_metrics(
        quarterly_income: List[Dict[str, Any]],
        quarterly_balance: List[Dict[str, Any]],
        quarterly_cashflow: List[Dict[str, Any]],
        num_quarters: int = 4
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive LTM metrics from quarterly data
        
        Args:
            quarterly_income: List of quarterly income statements
            quarterly_balance: List of quarterly balance sheets
            quarterly_cashflow: List of quarterly cash flow statements
            num_quarters: Number of quarters for LTM (typically 4)
            
        Returns:
            Dictionary with LTM financial statements
        """
        logger.info(f"Calculating LTM metrics from {num_quarters} quarters of data")
        
        ltm_data = {
            'income_statement': LTMCalculator.calculate_ltm_income_statement(
                quarterly_income, num_quarters
            ),
            'balance_sheet': LTMCalculator.get_latest_balance_sheet(
                quarterly_balance
            ),
            'cash_flow': LTMCalculator.calculate_ltm_cash_flow(
                quarterly_cashflow, num_quarters
            ),
            'metadata': {
                'calculation_method': 'Last Twelve Months (LTM)',
                'quarters_used': num_quarters,
                'calculation_date': datetime.utcnow().isoformat(),
                'data_freshness': 'Q' + str(quarterly_income[0].get('period', '')) if quarterly_income else 'Unknown'
            }
        }
        
        # Validate LTM data quality
        validation = LTMCalculator._validate_ltm_data(ltm_data)
        ltm_data['validation'] = validation
        
        if validation['is_valid']:
            logger.success(f"✓ LTM calculation complete and validated")
        else:
            logger.warning(f"⚠ LTM calculation complete but validation issues: {validation['warnings']}")
        
        return ltm_data
    
    @staticmethod
    def _validate_ltm_data(ltm_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate LTM calculation results
        
        Args:
            ltm_data: LTM financial data
            
        Returns:
            Validation results dictionary
        """
        warnings = []
        
        # Check income statement
        income = ltm_data.get('income_statement', {})
        if not income:
            warnings.append("Missing LTM income statement")
        elif not income.get('revenue'):
            warnings.append("Missing LTM revenue")
        elif not income.get('netIncome'):
            warnings.append("Missing LTM net income")
        
        # Check balance sheet
        balance = ltm_data.get('balance_sheet', {})
        if not balance:
            warnings.append("Missing balance sheet")
        elif not balance.get('totalAssets'):
            warnings.append("Missing total assets")
        
        # Check cash flow
        cashflow = ltm_data.get('cash_flow', {})
        if not cashflow:
            warnings.append("Missing LTM cash flow")
        elif not cashflow.get('operatingCashFlow'):
            warnings.append("Missing LTM operating cash flow")
        
        return {
            'is_valid': len(warnings) == 0,
            'warnings': warnings,
            'validation_date': datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def compare_annual_vs_ltm(
        annual_data: Dict[str, Any],
        ltm_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare annual data vs LTM to show data freshness benefit
        
        Args:
            annual_data: Annual financial data
            ltm_data: LTM financial data
            
        Returns:
            Comparison results
        """
        comparison = {
            'annual_date': annual_data.get('income_statement', [{}])[0].get('date') if annual_data.get('income_statement') else None,
            'ltm_date': ltm_data.get('income_statement', {}).get('date'),
            'data_freshness_advantage_days': None,
            'metrics_comparison': {}
        }
        
        # Calculate freshness advantage
        if comparison['annual_date'] and comparison['ltm_date']:
            try:
                annual_dt = datetime.strptime(comparison['annual_date'], '%Y-%m-%d')
                ltm_dt = datetime.strptime(comparison['ltm_date'], '%Y-%m-%d')
                days_diff = (ltm_dt - annual_dt).days
                comparison['data_freshness_advantage_days'] = days_diff
            except:
                pass
        
        # Compare key metrics
        annual_income = annual_data.get('income_statement', [{}])[0] if annual_data.get('income_statement') else {}
        ltm_income = ltm_data.get('income_statement', {})
        
        metrics_to_compare = ['revenue', 'netIncome', 'ebitda', 'operatingIncome']
        
        for metric in metrics_to_compare:
            annual_val = annual_income.get(metric)
            ltm_val = ltm_income.get(metric)
            
            if annual_val and ltm_val:
                try:
                    pct_diff = ((float(ltm_val) - float(annual_val)) / float(annual_val)) * 100
                    comparison['metrics_comparison'][metric] = {
                        'annual': float(annual_val),
                        'ltm': float(ltm_val),
                        'difference_pct': pct_diff
                    }
                except:
                    pass
        
        return comparison
