"""
Normalization Agent
Normalizes financial data: COA mapping, currency conversion, calendarization, restatements
Critical for production-grade M&A platform
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date
from decimal import Decimal
import pandas as pd
from loguru import logger

from config.settings import get_settings
from config.schemas import FinancialFact, CurrencyType, NORMALIZED_METRICS
from storage.duckdb_adapter import DuckDBAdapter


class NormalizationAgent:
    """
    Normalization Agent - normalizes raw financial data
    
    Responsibilities:
    - Chart of Accounts (COA) mapping
    - Currency conversion (FX rates)
    - Fiscal year calendarization
    - Restatement tracking
    - Debt-like items calculation
    """
    
    # COA Mapping Dictionary (GAAP/IFRS → Standard)
    COA_MAPPING = {
        # Income Statement
        'total_revenue': 'revenue',
        'net_revenue': 'revenue',
        'sales': 'revenue',
        'total_sales': 'revenue',
        'revenue': 'revenue',
        
        'cost_of_revenue': 'cogs',
        'cost_of_goods_sold': 'cogs',
        'cost_of_sales': 'cogs',
        'cogs': 'cogs',
        
        'gross_income': 'gross_profit',
        'gross_profit': 'gross_profit',
        
        'operating_expenses': 'opex',
        'total_operating_expenses': 'opex',
        'opex': 'opex',
        
        'selling_general_administrative': 'sga',
        'sga': 'sga',
        'sg&a': 'sga',
        
        'research_development': 'rnd',
        'research_and_development': 'rnd',
        'r&d': 'rnd',
        'rnd': 'rnd',
        
        'ebitda': 'ebitda',
        'adjusted_ebitda': 'ebitda',
        'ebitda_normalized': 'ebitda',
        
        'operating_income': 'ebit',
        'operating_profit': 'ebit',
        'ebit': 'ebit',
        
        'interest_paid': 'interest_expense',
        'interest_cost': 'interest_expense',
        'interest_expense': 'interest_expense',
        
        'pretax_income': 'ebt',
        'income_before_tax': 'ebt',
        'ebt': 'ebt',
        
        'income_tax': 'tax_expense',
        'provision_for_taxes': 'tax_expense',
        'tax_expense': 'tax_expense',
        
        'net_earnings': 'net_income',
        'profit': 'net_income',
        'net_profit': 'net_income',
        'net_income': 'net_income',
        
        # Balance Sheet
        'cash_and_equivalents': 'cash',
        'cash_short_term_investments': 'cash',
        'cash': 'cash',
        
        'accounts_receivable': 'accounts_receivable',
        'receivables': 'accounts_receivable',
        'ar': 'accounts_receivable',
        
        'inventories': 'inventory',
        'inventory': 'inventory',
        
        'total_current_assets': 'current_assets',
        'current_assets': 'current_assets',
        
        'property_plant_equipment': 'ppe',
        'fixed_assets': 'ppe',
        'ppe': 'ppe',
        
        'goodwill_net': 'goodwill',
        'goodwill': 'goodwill',
        
        'intangible_assets': 'intangibles',
        'intangibles': 'intangibles',
        
        'assets': 'total_assets',
        'total_assets': 'total_assets',
        
        'accounts_payable': 'accounts_payable',
        'payables': 'accounts_payable',
        'ap': 'accounts_payable',
        
        'total_current_liabilities': 'current_liabilities',
        'current_liabilities': 'current_liabilities',
        
        'short_term_debt': 'debt_st',
        'current_debt': 'debt_st',
        'debt_st': 'debt_st',
        
        'long_term_debt': 'debt_lt',
        'noncurrent_debt': 'debt_lt',
        'debt_lt': 'debt_lt',
        
        'debt': 'total_debt',
        'total_borrowings': 'total_debt',
        'total_debt': 'total_debt',
        
        'liabilities': 'total_liabilities',
        'total_liabilities': 'total_liabilities',
        
        'shareholders_equity': 'equity',
        'stockholders_equity': 'equity',
        'total_equity': 'equity',
        'equity': 'equity',
        
        # Cash Flow
        'operating_cash_flow': 'cfo',
        'cash_from_operations': 'cfo',
        'cfo': 'cfo',
        
        'capital_expenditures': 'capex',
        'capital_expenditure': 'capex',
        'capex': 'capex',
        
        'investing_cash_flow': 'cfi',
        'cash_from_investing': 'cfi',
        'cfi': 'cfi',
        
        'financing_cash_flow': 'cff',
        'cash_from_financing': 'cff',
        'cff': 'cff',
        
        'free_cash_flow': 'fcf',
        'fcf': 'fcf'
    }
    
    # FX Rates (simplified - in production, use live API)
    FX_RATES = {
        'USD': 1.0,
        'EUR': 1.10,
        'GBP': 1.27,
        'JPY': 0.0067,
        'CNY': 0.14,
        'CAD': 0.74,
        'AUD': 0.65
    }
    
    def __init__(self):
        """Initialize normalization agent"""
        self.settings = get_settings()
        self.db = DuckDBAdapter()
        
        logger.info("Normalization Agent initialized")
    
    def normalize_metric_name(self, raw_metric: str) -> str:
        """
        Map raw metric name to normalized name
        
        Args:
            raw_metric: Raw metric name from source
            
        Returns:
            Normalized metric name
        """
        raw_lower = raw_metric.lower().strip().replace('  ', ' ')
        
        # Direct lookup
        if raw_lower in self.COA_MAPPING:
            return self.COA_MAPPING[raw_lower]
        
        # Fuzzy matching for common variations
        for raw_variant, normalized in self.COA_MAPPING.items():
            if raw_variant in raw_lower or raw_lower in raw_variant:
                logger.debug(f"Fuzzy matched '{raw_metric}' → '{normalized}'")
                return normalized
        
        # No match - return original with warning
        logger.warning(f"No COA mapping for metric: '{raw_metric}'")
        return raw_lower
    
    def convert_currency(
        self,
        amount: float,
        from_currency: str,
        to_currency: str = 'USD',
        as_of_date: Optional[date] = None
    ) -> float:
        """
        Convert amount from one currency to another
        
        Args:
            amount: Amount to convert
            from_currency: Source currency (ISO code)
            to_currency: Target currency (ISO code)
            as_of_date: Historical date (if None, uses current rates)
            
        Returns:
            Converted amount
        """
        if from_currency == to_currency:
            return amount
        
        # Get FX rates (in production, fetch historical rates from API)
        from_rate = self.FX_RATES.get(from_currency, 1.0)
        to_rate = self.FX_RATES.get(to_currency, 1.0)
        
        # Convert: amount → USD → target currency
        usd_amount = amount * from_rate
        converted = usd_amount / to_rate
        
        logger.debug(f"FX: {amount:,.2f} {from_currency} → {converted:,.2f} {to_currency}")
        
        return converted
    
    def calendarize_fiscal_year(
        self,
        fiscal_period_end: date,
        calendar_year_end: int = 12
    ) -> Tuple[date, float]:
        """
        Adjust fiscal year data to calendar year
        
        Args:
            fiscal_period_end: Fiscal year end date
            calendar_year_end: Target calendar month (default 12 for Dec 31)
            
        Returns:
            Tuple of (calendar_period_end, weight_factor)
        """
        fiscal_month = fiscal_period_end.month
        
        if fiscal_month == calendar_year_end:
            # Already aligned
            return fiscal_period_end, 1.0
        
        # Calculate stub period weight
        # Example: Sept 30 FY → need 3 months (Oct-Dec) from next period
        months_to_add = (calendar_year_end - fiscal_month) % 12
        weight = months_to_add / 12.0
        
        # Calendar year end
        calendar_end = date(fiscal_period_end.year, calendar_year_end, 31)
        
        logger.debug(f"Calendarization: {fiscal_period_end} (FY) → {calendar_end} (CY), weight={weight:.2f}")
        
        return calendar_end, weight
    
    def calculate_debt_like_items(
        self,
        financials: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate debt-like items for EV bridge
        
        Args:
            financials: Dictionary of financial metrics
            
        Returns:
            Dictionary of debt-like adjustments
        """
        debt_like = {}
        
        # Operating leases (capitalize at ~8x rent)
        operating_lease_expense = financials.get('operating_lease_expense', 0)
        if operating_lease_expense > 0:
            debt_like['capitalized_operating_leases'] = operating_lease_expense * 8.0
        
        # Deferred revenue haircut (assume 20% margin)
        deferred_revenue = financials.get('deferred_revenue', 0)
        if deferred_revenue > 0:
            debt_like['deferred_revenue_haircut'] = deferred_revenue * 0.20
        
        # Unfunded pension obligations
        pension_liability = financials.get('unfunded_pension', 0)
        if pension_liability > 0:
            debt_like['pension_obligations'] = pension_liability
        
        # Earnout liabilities (if material)
        earnouts = financials.get('earnout_liabilities', 0)
        if earnouts > 0:
            debt_like['earnouts'] = earnouts
        
        # Minority interest
        minority_interest = financials.get('minority_interest', 0)
        if minority_interest > 0:
            debt_like['minority_interest'] = minority_interest
        
        total_debt_like = sum(debt_like.values())
        debt_like['total_debt_like_items'] = total_debt_like
        
        if total_debt_like > 0:
            logger.info(f"Total debt-like items: ${total_debt_like:,.0f}")
        
        return debt_like
    
    def normalize_financials(
        self,
        symbol: str,
        raw_facts: List[Dict[str, Any]],
        target_currency: str = 'USD',
        fiscal_year_end_month: int = 12
    ) -> List[FinancialFact]:
        """
        Full normalization pipeline
        
        Args:
            symbol: Company symbol
            raw_facts: Raw financial facts from source
            target_currency: Target currency for conversion
            fiscal_year_end_month: Target fiscal year end month
            
        Returns:
            List of normalized FinancialFact objects
        """
        logger.info(f"Normalizing {len(raw_facts)} facts for {symbol}")
        
        normalized_facts = []
        
        for raw_fact in raw_facts:
            try:
                # 1. Normalize metric name (COA mapping)
                raw_metric = raw_fact.get('metric', '')
                normalized_metric = self.normalize_metric_name(raw_metric)
                
                # 2. Currency conversion
                raw_value = float(raw_fact.get('value', 0))
                source_currency = raw_fact.get('currency', 'USD')
                normalized_value = self.convert_currency(
                    raw_value,
                    source_currency,
                    target_currency
                )
                
                # 3. Calendarization (if needed)
                period_end = raw_fact.get('period_end')
                if isinstance(period_end, str):
                    period_end = datetime.strptime(period_end, '%Y-%m-%d').date()
                
                calendar_end, weight = self.calendarize_fiscal_year(
                    period_end,
                    fiscal_year_end_month
                )
                
                # Create normalized fact
                normalized_fact = FinancialFact(
                    symbol=symbol,
                    period_end=calendar_end,
                    frequency=raw_fact.get('frequency', 'annual'),
                    metric=normalized_metric,
                    value=Decimal(str(normalized_value)),
                    source_ref=raw_fact.get('source_ref', 'normalized'),
                    as_reported=raw_fact.get('as_reported', True),
                    restated=raw_fact.get('restated', False),
                    currency=target_currency
                )
                
                normalized_facts.append(normalized_fact)
                
            except Exception as e:
                logger.error(f"Error normalizing fact: {str(e)}")
                continue
        
        logger.info(f"Successfully normalized {len(normalized_facts)} facts")
        
        return normalized_facts
    
    def detect_restatements(
        self,
        symbol: str,
        period_end: date,
        metric: str
    ) -> bool:
        """
        Detect if a metric has been restated
        
        Args:
            symbol: Company symbol
            period_end: Period end date
            metric: Metric name
            
        Returns:
            True if restatement detected
        """
        # Query historical values for this metric/period
        query = """
            SELECT value, created_at 
            FROM financial_facts 
            WHERE symbol = ? AND period_end = ? AND metric = ?
            ORDER BY created_at DESC
            LIMIT 2
        """
        
        results = self.db.execute_query(query, [symbol, period_end, metric])
        
        if len(results) >= 2:
            # Compare values
            latest_value = results.iloc[0]['value']
            previous_value = results.iloc[1]['value']
            
            if abs(latest_value - previous_value) / abs(previous_value) > 0.01:  # >1% change
                logger.warning(f"Restatement detected for {symbol} {metric} on {period_end}: "
                             f"{previous_value:,.0f} → {latest_value:,.0f}")
                return True
        
        return False
    
    def build_normalized_financials_table(
        self,
        symbol: str,
        metrics: List[str],
        years: int = 5
    ) -> pd.DataFrame:
        """
        Build clean, normalized financials table
        
        Args:
            symbol: Company symbol
            metrics: List of metrics to include
            years: Number of years of history
            
        Returns:
            DataFrame with normalized financials
        """
        logger.info(f"Building normalized financials table for {symbol}")
        
        # Fetch normalized data
        financials = self.db.get_financials(
            symbol=symbol,
            metrics=metrics,
            frequency='annual'
        )
        
        if financials.empty:
            logger.warning(f"No financial data found for {symbol}")
            return pd.DataFrame()
        
        # Pivot to wide format
        pivoted = self.db.pivot_financials(
            symbol=symbol,
            metrics=metrics,
            frequency='annual'
        )
        
        # Sort by period (most recent first)
        if not pivoted.empty and 'period_end' in pivoted.columns:
            pivoted = pivoted.sort_values('period_end', ascending=False).head(years)
        
        logger.info(f"Built table with {len(pivoted)} periods")
        
        return pivoted
    
    def close(self):
        """Clean up resources"""
        try:
            self.db.close()
            logger.info("Normalization agent resources closed")
        except Exception as e:
            logger.error(f"Error closing resources: {str(e)}")


# Example usage
if __name__ == "__main__":
    # Initialize agent
    agent = NormalizationAgent()
    
    print("\n" + "="*70)
    print("NORMALIZATION AGENT - DATA NORMALIZATION")
    print("="*70)
    
    # Test COA mapping
    print("\n[1/4] Testing COA mapping...")
    test_metrics = [
        'total_revenue',
        'cost_of_goods_sold',
        'operating_income',
        'shareholders_equity',
        'free_cash_flow'
    ]
    
    for metric in test_metrics:
        normalized = agent.normalize_metric_name(metric)
        print(f"  {metric} → {normalized}")
    
    # Test currency conversion
    print("\n[2/4] Testing currency conversion...")
    conversions = [
        (1_000_000, 'EUR', 'USD'),
        (100_000_000, 'JPY', 'USD'),
        (500_000, 'GBP', 'USD')
    ]
    
    for amount, from_curr, to_curr in conversions:
        converted = agent.convert_currency(amount, from_curr, to_curr)
        print(f"  {amount:,.0f} {from_curr} = {converted:,.0f} {to_curr}")
    
    # Test calendarization
    print("\n[3/4] Testing calendarization...")
    from datetime import date
    fiscal_dates = [
        date(2023, 9, 30),  # Apple's FY
        date(2023, 6, 30),  # Microsoft's FY
        date(2023, 12, 31)  # Already aligned
    ]
    
    for fiscal_date in fiscal_dates:
        calendar_date, weight = agent.calendarize_fiscal_year(fiscal_date, 12)
        print(f"  {fiscal_date} (FY) → {calendar_date} (CY), weight={weight:.2f}")
    
    # Test debt-like calculation
    print("\n[4/4] Testing debt-like items...")
    sample_financials = {
        'operating_lease_expense': 10_000_000,
        'deferred_revenue': 50_000_000,
        'unfunded_pension': 25_000_000,
        'minority_interest': 5_000_000
    }
    
    debt_like = agent.calculate_debt_like_items(sample_financials)
    print("  Debt-like items:")
    for item, value in debt_like.items():
        print(f"    {item}: ${value:,.0f}")
    
    print("\n" + "="*70)
    print("NORMALIZATION DEMO COMPLETE")
    print("="*70)
    
    agent.close()
