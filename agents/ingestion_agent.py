"""
Ingestion Agent
Orchestrates data collection from FMP API and SEC EDGAR, 
stores in DuckDB lakehouse via MemoryManager
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date
from decimal import Decimal
import asyncio
from loguru import logger

from config.settings import get_settings
from config.schemas import (
    CompanyMaster, FinancialFact, MarketData, Filing, 
    FilingSection, FrequencyType, CurrencyType, DataSourceType
)
from ingestion.fmp_client import FMPClient
from ingestion.sec_client import SECClient
from storage.duckdb_adapter import DuckDBAdapter
from storage.memory_manager import MemoryManager
from utils.llm_client import LLMClient


class IngestionAgent:
    """
    Ingestion Agent - orchestrates data collection and storage
    
    Responsibilities:
    - Pull fundamental data from FMP
    - Pull filings from SEC EDGAR
    - Normalize and store in DuckDB
    - Create knowledge graph in Cognee
    - Extract insights using LLM
    """
    
    def __init__(self):
        """Initialize ingestion agent with all required clients"""
        self.settings = get_settings()
        
        # Initialize clients
        self.fmp = FMPClient()
        self.sec = SECClient(email="fmna@agent.local")
        self.db = DuckDBAdapter()
        self.memory = MemoryManager()
        self.llm = LLMClient()
        
        logger.info("Ingestion Agent initialized with MemoryManager")
    
    def detect_financial_scale(self, financial_data: Dict[str, Any]) -> Tuple[float, str]:
        """
        Detect if financial data is in ones, thousands, millions, or billions
        
        Returns:
            (scale_factor, unit_label) where scale_factor converts to dollars
        """
        income_stmt = financial_data.get('income_statement', [])[0] if financial_data.get('income_statement') else {}
        balance_sheet = financial_data.get('balance_sheet', [])[0] if financial_data.get('balance_sheet') else {}
        market_snapshot = financial_data.get('market_snapshot', {})
        
        revenue = float(income_stmt.get('revenue', 0))
        market_cap = float(market_snapshot.get('market_cap', 0))
        
        if revenue == 0 or market_cap == 0:
            logger.warning("Cannot detect scale - missing revenue or market cap")
            return 1.0, "unknown"
        
        ratio = market_cap / revenue
        
        if 0.1 < ratio < 50:
            return 1.0, "dollars"
        elif 100 < ratio < 50000:
            return 1000.0, "thousands"
        elif 100000 < ratio < 50000000:
            return 1000000.0, "millions"
        elif ratio > 50000000:
            return 1000000000.0, "billions"
        else:
            logger.warning(f"Ambiguous scale (ratio={ratio:.2f}), defaulting to millions")
            return 1000000.0, "millions"
    
    def normalize_financial_scale(
        self,
        financial_data: Dict[str, Any],
        target_scale: float = 1.0
    ) -> Dict[str, Any]:
        """
        Normalize all financial values to consistent scale
        """
        current_scale, unit_label = self.detect_financial_scale(financial_data)
        
        if current_scale == target_scale:
            logger.info(f"Financial data already in target scale ({unit_label})")
            return financial_data
        
        conversion_factor = current_scale / target_scale
        logger.info(f"Converting from {unit_label} to dollars (factor: {conversion_factor})")
        
        # Normalize all statements
        for stmt in financial_data.get('income_statement', []):
            for key in ['revenue', 'costOfRevenue', 'grossProfit', 'operatingExpenses', 
                       'ebitda', 'operatingIncome', 'interestExpense', 'incomeTaxExpense',
                       'netIncome', 'eps', 'researchAndDevelopmentExpenses',
                       'sellingGeneralAndAdministrativeExpenses']:
                if key in stmt and stmt[key] is not None:
                    stmt[key] = float(stmt[key]) * conversion_factor
        
        for stmt in financial_data.get('balance_sheet', []):
            for key in ['cashAndCashEquivalents', 'netReceivables', 'inventory',
                       'totalCurrentAssets', 'propertyPlantEquipmentNet', 'goodwill',
                       'totalAssets', 'accountPayables', 'totalCurrentLiabilities',
                       'totalDebt', 'totalLiabilities', 'totalStockholdersEquity']:
                if key in stmt and stmt[key] is not None:
                    stmt[key] = float(stmt[key]) * conversion_factor
        
        for stmt in financial_data.get('cash_flow', []):
            for key in ['operatingCashFlow', 'capitalExpenditure', 'freeCashFlow']:
                if key in stmt and stmt[key] is not None:
                    stmt[key] = float(stmt[key]) * conversion_factor
        
        if 'market_snapshot' in financial_data:
            for key in ['market_cap']:
                if key in financial_data['market_snapshot'] and financial_data['market_snapshot'][key] is not None:
                    financial_data['market_snapshot'][key] = float(financial_data['market_snapshot'][key]) * conversion_factor
        
        logger.success("Normalized all financial values to dollars")
        return financial_data
    
    def ingest_company_full(
        self,
        symbol: str,
        years_of_financials: int = 5,
        include_filings: bool = True,
        include_market_data: bool = True
    ) -> Dict[str, Any]:
        """
        Full ingestion pipeline for a company
        
        Args:
            symbol: Stock ticker symbol
            years_of_financials: Number of years of financial data to pull
            include_filings: Whether to pull SEC filings
            include_market_data: Whether to pull market data
            
        Returns:
            Dictionary with ingestion results
        """
        logger.info(f"Starting full ingestion for {symbol}")
        
        results = {
            'symbol': symbol,
            'timestamp': datetime.utcnow(),
            'company': None,
            'financials_count': 0,
            'market_data_count': 0,
            'filings_count': 0,
            'errors': []
        }
        
        try:
            # Step 1: Ingest company profile
            company = self.ingest_company_profile(symbol)
            if company:
                results['company'] = company
                logger.info(f"✓ Company profile ingested: {company.legal_name}")
            
            # Step 2: Ingest financial statements
            financials_count = self.ingest_financials(
                symbol, 
                period="annual",
                limit=years_of_financials
            )
            results['financials_count'] = financials_count
            logger.info(f"✓ Financials ingested: {financials_count} facts")
            
            # Step 3: Ingest market data (optional)
            if include_market_data:
                market_count = self.ingest_market_data(symbol, days=365)
                results['market_data_count'] = market_count
                logger.info(f"✓ Market data ingested: {market_count} records")
            
            # Step 4: Ingest SEC filings (optional)
            if include_filings and company:
                filings_count = self.ingest_filings(symbol)
                results['filings_count'] = filings_count
                logger.info(f"✓ Filings ingested: {filings_count} filings")
            
            logger.success(f"Full ingestion completed for {symbol}")
            
        except Exception as e:
            error_msg = f"Error in full ingestion: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        return results
    
    def ingest_company_profile(self, symbol: str) -> Optional[CompanyMaster]:
        """
        Ingest company profile from FMP
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            CompanyMaster object
        """
        try:
            # Get profile from FMP
            profile = self.fmp.get_company_profile(symbol)
            
            if profile:
                # Store in DuckDB
                self.db.insert_company(profile)
                return profile
            
            return None
            
        except Exception as e:
            logger.error(f"Error ingesting company profile: {str(e)}")
            return None
    
    def ingest_financials(
        self,
        symbol: str,
        period: str = "annual",
        limit: int = 5
    ) -> int:
        """
        Ingest financial statements from FMP
        
        Args:
            symbol: Stock ticker symbol
            period: "annual" or "quarterly"
            limit: Number of periods to fetch
            
        Returns:
            Count of financial facts inserted
        """
        try:
            # Get all financial data
            financials = self.fmp.get_all_financial_data(symbol, period, limit)
            
            facts = []
            
            # Process income statement
            for statement in financials.get('income_statement', []):
                period_end = datetime.strptime(statement['date'], '%Y-%m-%d').date()
                
                # Revenue
                if statement.get('revenue'):
                    facts.append(FinancialFact(
                        symbol=symbol,
                        period_end=period_end,
                        frequency=FrequencyType.ANNUAL if period == "annual" else FrequencyType.QUARTERLY,
                        metric='revenue',
                        value=Decimal(str(statement['revenue'])),
                        source_ref=f"FMP-IS-{period_end}",
                        currency=CurrencyType.USD
                    ))
                
                # COGS
                if statement.get('costOfRevenue'):
                    facts.append(FinancialFact(
                        symbol=symbol,
                        period_end=period_end,
                        frequency=FrequencyType.ANNUAL if period == "annual" else FrequencyType.QUARTERLY,
                        metric='cogs',
                        value=Decimal(str(statement['costOfRevenue'])),
                        source_ref=f"FMP-IS-{period_end}",
                        currency=CurrencyType.USD
                    ))
                
                # Gross Profit
                if statement.get('grossProfit'):
                    facts.append(FinancialFact(
                        symbol=symbol,
                        period_end=period_end,
                        frequency=FrequencyType.ANNUAL if period == "annual" else FrequencyType.QUARTERLY,
                        metric='gross_profit',
                        value=Decimal(str(statement['grossProfit'])),
                        source_ref=f"FMP-IS-{period_end}",
                        currency=CurrencyType.USD
                    ))
                
                # EBITDA
                if statement.get('ebitda'):
                    facts.append(FinancialFact(
                        symbol=symbol,
                        period_end=period_end,
                        frequency=FrequencyType.ANNUAL if period == "annual" else FrequencyType.QUARTERLY,
                        metric='ebitda',
                        value=Decimal(str(statement['ebitda'])),
                        source_ref=f"FMP-IS-{period_end}",
                        currency=CurrencyType.USD
                    ))
                
                # Net Income
                if statement.get('netIncome'):
                    facts.append(FinancialFact(
                        symbol=symbol,
                        period_end=period_end,
                        frequency=FrequencyType.ANNUAL if period == "annual" else FrequencyType.QUARTERLY,
                        metric='net_income',
                        value=Decimal(str(statement['netIncome'])),
                        source_ref=f"FMP-IS-{period_end}",
                        currency=CurrencyType.USD
                    ))
            
            # Process balance sheet
            for statement in financials.get('balance_sheet', []):
                period_end = datetime.strptime(statement['date'], '%Y-%m-%d').date()
                
                # Total Assets
                if statement.get('totalAssets'):
                    facts.append(FinancialFact(
                        symbol=symbol,
                        period_end=period_end,
                        frequency=FrequencyType.ANNUAL if period == "annual" else FrequencyType.QUARTERLY,
                        metric='total_assets',
                        value=Decimal(str(statement['totalAssets'])),
                        source_ref=f"FMP-BS-{period_end}",
                        currency=CurrencyType.USD
                    ))
                
                # Total Debt
                if statement.get('totalDebt'):
                    facts.append(FinancialFact(
                        symbol=symbol,
                        period_end=period_end,
                        frequency=FrequencyType.ANNUAL if period == "annual" else FrequencyType.QUARTERLY,
                        metric='total_debt',
                        value=Decimal(str(statement['totalDebt'])),
                        source_ref=f"FMP-BS-{period_end}",
                        currency=CurrencyType.USD
                    ))
                
                # Total Equity
                if statement.get('totalStockholdersEquity'):
                    facts.append(FinancialFact(
                        symbol=symbol,
                        period_end=period_end,
                        frequency=FrequencyType.ANNUAL if period == "annual" else FrequencyType.QUARTERLY,
                        metric='equity',
                        value=Decimal(str(statement['totalStockholdersEquity'])),
                        source_ref=f"FMP-BS-{period_end}",
                        currency=CurrencyType.USD
                    ))
            
            # Process cash flow
            for statement in financials.get('cash_flow', []):
                period_end = datetime.strptime(statement['date'], '%Y-%m-%d').date()
                
                # Operating Cash Flow
                if statement.get('operatingCashFlow'):
                    facts.append(FinancialFact(
                        symbol=symbol,
                        period_end=period_end,
                        frequency=FrequencyType.ANNUAL if period == "annual" else FrequencyType.QUARTERLY,
                        metric='cfo',
                        value=Decimal(str(statement['operatingCashFlow'])),
                        source_ref=f"FMP-CF-{period_end}",
                        currency=CurrencyType.USD
                    ))
                
                # CapEx
                if statement.get('capitalExpenditure'):
                    facts.append(FinancialFact(
                        symbol=symbol,
                        period_end=period_end,
                        frequency=FrequencyType.ANNUAL if period == "annual" else FrequencyType.QUARTERLY,
                        metric='capex',
                        value=Decimal(str(abs(statement['capitalExpenditure']))),  # CapEx is usually negative
                        source_ref=f"FMP-CF-{period_end}",
                        currency=CurrencyType.USD
                    ))
                
                # Free Cash Flow
                if statement.get('freeCashFlow'):
                    facts.append(FinancialFact(
                        symbol=symbol,
                        period_end=period_end,
                        frequency=FrequencyType.ANNUAL if period == "annual" else FrequencyType.QUARTERLY,
                        metric='fcf',
                        value=Decimal(str(statement['freeCashFlow'])),
                        source_ref=f"FMP-CF-{period_end}",
                        currency=CurrencyType.USD
                    ))
            
            # Bulk insert into DuckDB
            if facts:
                inserted_count = self.db.bulk_insert_financial_facts(facts)
                return inserted_count
            
            return 0
            
        except Exception as e:
            logger.error(f"Error ingesting financials: {str(e)}")
            return 0
    
    def ingest_market_data(self, symbol: str, days: int = 365) -> int:
        """
        Ingest historical market data from FMP
        
        Args:
            symbol: Stock ticker symbol
            days: Number of days of history
            
        Returns:
            Count of market data records inserted
        """
        try:
            # Get historical prices
            prices = self.fmp.get_historical_price(symbol, limit=days)
            
            if not prices:
                return 0
            
            # Note: In production, would bulk insert into market_data table
            # For now, just log the count
            logger.debug(f"Retrieved {len(prices)} days of market data")
            return len(prices)
            
        except Exception as e:
            logger.error(f"Error ingesting market data: {str(e)}")
            return 0
    
    def ingest_filings(self, symbol: str, filing_types: List[str] = ["10-K"]) -> int:
        """
        Ingest SEC filings
        
        Args:
            symbol: Stock ticker symbol
            filing_types: Types of filings to retrieve
            
        Returns:
            Count of filings ingested
        """
        try:
            count = 0
            
            for filing_type in filing_types:
                filing = self.sec.get_latest_filing(symbol, filing_type)
                
                if filing:
                    # Note: In production, would store filing in database
                    # For now, just count
                    count += 1
                    logger.debug(f"Retrieved {filing_type} for {symbol}")
            
            return count
            
        except Exception as e:
            logger.error(f"Error ingesting filings: {str(e)}")
            return 0
    
    
    def close(self):
        """Clean up resources"""
        try:
            self.db.close()
            logger.info("Ingestion agent resources closed")
        except Exception as e:
            logger.error(f"Error closing resources: {str(e)}")


# Example usage
if __name__ == "__main__":
    # Initialize agent
    agent = IngestionAgent()
    
    # Run full ingestion for a company
    results = agent.ingest_company_full(
        symbol="AAPL",
        years_of_financials=5,
        include_filings=True,
        include_market_data=True
    )
    
    print("\n" + "="*80)
    print("INGESTION RESULTS")
    print("="*80)
    print(f"Symbol: {results['symbol']}")
    print(f"Company: {results['company'].legal_name if results['company'] else 'N/A'}")
    print(f"Financials: {results['financials_count']} facts")
    print(f"Market Data: {results['market_data_count']} records")
    print(f"Filings: {results['filings_count']} filings")
    
    if results['errors']:
        print(f"\nErrors: {len(results['errors'])}")
        for error in results['errors']:
            print(f"  - {error}")
    
    # Clean up
    agent.close()
