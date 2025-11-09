"""
Financial Modeling Prep (FMP) API Client
Handles data ingestion from FMP API with rate limiting and error handling
"""

import time
import csv
from io import StringIO
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from decimal import Decimal
import requests
from loguru import logger
from ratelimit import limits, sleep_and_retry
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.settings import get_settings
from config.schemas import (
    CompanyMaster, FinancialFact, MarketData, 
    Transaction, FrequencyType, CurrencyType
)


class FMPClient:
    """Client for Financial Modeling Prep API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize FMP client with API key and rate limiting"""
        settings = get_settings()
        self.api_key = api_key or settings.fmp_api_key
        self.base_url = settings.fmp_base_url
        self.rate_limit = settings.fmp_rate_limit
        
        # Configure session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Peers cache (bulk data is updated every few hours, so cache it)
        self._peers_cache: Dict[str, List[str]] = {}
        self._peers_cache_timestamp: Optional[datetime] = None
        self._peers_cache_ttl: int = 3600  # Cache for 1 hour
        
        logger.info(f"FMP Client initialized with rate limit: {self.rate_limit}/min")
    
    @sleep_and_retry
    @limits(calls=300, period=60)  # 300 calls per minute
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make rate-limited request to FMP API
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            JSON response data
        """
        if params is None:
            params = {}
        
        params['apikey'] = self.api_key
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API error messages
            if isinstance(data, dict) and "Error Message" in data:
                logger.error(f"FMP API Error: {data['Error Message']}")
                return {}
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {endpoint}: {str(e)}")
            raise
    
    def get_company_profile(self, symbol: str) -> Optional[CompanyMaster]:
        """
        Get company profile information
        
        Args:
            symbol: Company ticker symbol
            
        Returns:
            CompanyMaster object or None
        """
        endpoint = f"profile/{symbol}"
        data = self._make_request(endpoint)
        
        if not data or not isinstance(data, list) or len(data) == 0:
            logger.warning(f"No profile data found for {symbol}")
            return None
        
        profile = data[0]
        
        try:
            return CompanyMaster(
                cik=profile.get('cik', ''),
                fmp_symbol=symbol,
                legal_name=profile.get('companyName', ''),
                domicile=profile.get('country', 'US'),
                currency=CurrencyType(profile.get('currency', 'USD')),
                sector=profile.get('sector'),
                industry=profile.get('industry'),
                fiscal_year_end=str(profile.get('fiscalYearEnd', '12-31')) if profile.get('fiscalYearEnd') else None
            )
        except Exception as e:
            logger.error(f"Error parsing company profile for {symbol}: {str(e)}")
            return None
    
    def get_income_statement(
        self, 
        symbol: str, 
        period: str = "annual",
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get income statement data
        
        Args:
            symbol: Company ticker symbol
            period: 'annual', 'quarter', or 'ttm' (trailing twelve months)
            limit: Number of periods to retrieve
            
        Returns:
            List of income statement records
        """
        # FMP provides direct TTM endpoint
        if period == "ttm":
            endpoint = f"income-statement/{symbol}"
            params = {"period": "quarter", "limit": 1}  # Get latest quarter
            data = self._make_request(endpoint, params)
            
            # Also fetch TTM data from key-metrics-ttm endpoint
            ttm_endpoint = f"key-metrics-ttm/{symbol}"
            ttm_data = self._make_request(ttm_endpoint)
            
            if data and isinstance(data, list) and len(data) > 0:
                # FMP returns TTM data in the quarterly endpoint
                return data
            return []
        
        endpoint = f"income-statement/{symbol}"
        params = {"period": period, "limit": limit}
        
        data = self._make_request(endpoint, params)
        
        if not data or not isinstance(data, list):
            logger.warning(f"No income statement data found for {symbol}")
            return []
        
        return data
    
    def get_balance_sheet(
        self, 
        symbol: str, 
        period: str = "annual",
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get balance sheet data
        
        Args:
            symbol: Company ticker symbol
            period: 'annual' or 'quarter'
            limit: Number of periods to retrieve
            
        Returns:
            List of balance sheet records
        """
        endpoint = f"balance-sheet-statement/{symbol}"
        params = {"period": period, "limit": limit}
        
        data = self._make_request(endpoint, params)
        
        if not data or not isinstance(data, list):
            logger.warning(f"No balance sheet data found for {symbol}")
            return []
        
        return data
    
    def get_cash_flow_statement(
        self, 
        symbol: str, 
        period: str = "annual",
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get cash flow statement data
        
        Args:
            symbol: Company ticker symbol
            period: 'annual' or 'quarter'
            limit: Number of periods to retrieve
            
        Returns:
            List of cash flow records
        """
        endpoint = f"cash-flow-statement/{symbol}"
        params = {"period": period, "limit": limit}
        
        data = self._make_request(endpoint, params)
        
        if not data or not isinstance(data, list):
            logger.warning(f"No cash flow data found for {symbol}")
            return []
        
        return data
    
    def get_key_metrics(
        self, 
        symbol: str, 
        period: str = "annual",
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get key financial metrics and ratios
        
        Args:
            symbol: Company ticker symbol
            period: 'annual' or 'quarter'
            limit: Number of periods to retrieve
            
        Returns:
            List of key metrics
        """
        endpoint = f"key-metrics/{symbol}"
        params = {"period": period, "limit": limit}
        
        data = self._make_request(endpoint, params)
        
        if not data or not isinstance(data, list):
            logger.warning(f"No key metrics found for {symbol}")
            return []
        
        return data
    
    def get_financial_ratios(
        self, 
        symbol: str, 
        period: str = "annual",
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get financial ratios
        
        Args:
            symbol: Company ticker symbol
            period: 'annual' or 'quarter'
            limit: Number of periods to retrieve
            
        Returns:
            List of financial ratios
        """
        endpoint = f"ratios/{symbol}"
        params = {"period": period, "limit": limit}
        
        data = self._make_request(endpoint, params)
        
        if not data or not isinstance(data, list):
            logger.warning(f"No ratios found for {symbol}")
            return []
        
        return data
    
    def get_historical_price(
        self, 
        symbol: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[MarketData]:
        """
        Get historical daily prices
        
        Args:
            symbol: Company ticker symbol
            from_date: Start date
            to_date: End date
            
        Returns:
            List of MarketData objects
        """
        endpoint = f"historical-price-full/{symbol}"
        params = {}
        
        if from_date:
            params['from'] = from_date.isoformat()
        if to_date:
            params['to'] = to_date.isoformat()
        
        data = self._make_request(endpoint, params)
        
        if not data or 'historical' not in data:
            logger.warning(f"No historical price data found for {symbol}")
            return []
        
        market_data_list = []
        for record in data['historical']:
            try:
                market_data_list.append(MarketData(
                    symbol=symbol,
                    date=datetime.strptime(record['date'], '%Y-%m-%d').date(),
                    open=Decimal(str(record.get('open', 0))),
                    high=Decimal(str(record.get('high', 0))),
                    low=Decimal(str(record.get('low', 0))),
                    close=Decimal(str(record.get('close', 0))),
                    volume=record.get('volume'),
                    market_cap=Decimal(str(record.get('marketCap', 0))) if record.get('marketCap') else None
                ))
            except Exception as e:
                logger.error(f"Error parsing market data for {symbol} on {record.get('date')}: {str(e)}")
                continue
        
        return market_data_list
    
    def get_enterprise_value(
        self, 
        symbol: str, 
        period: str = "annual",
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get enterprise value data
        
        Args:
            symbol: Company ticker symbol
            period: 'annual' or 'quarter'
            limit: Number of periods to retrieve
            
        Returns:
            List of enterprise value records
        """
        endpoint = f"enterprise-values/{symbol}"
        params = {"period": period, "limit": limit}
        
        data = self._make_request(endpoint, params)
        
        if not data or not isinstance(data, list):
            logger.warning(f"No enterprise value data found for {symbol}")
            return []
        
        return data
    
    def get_analyst_estimates(
        self, 
        symbol: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get analyst estimates
        
        Args:
            symbol: Company ticker symbol
            limit: Number of periods to retrieve
            
        Returns:
            List of analyst estimates
        """
        endpoint = f"analyst-estimates/{symbol}"
        params = {"limit": limit}
        
        data = self._make_request(endpoint, params)
        
        if not data or not isinstance(data, list):
            logger.warning(f"No analyst estimates found for {symbol}")
            return []
        
        return data
    
    def get_earnings_calendar(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get earnings calendar
        
        Args:
            from_date: Start date
            to_date: End date
            
        Returns:
            List of earnings calendar events
        """
        endpoint = "earning_calendar"
        params = {}
        
        if from_date:
            params['from'] = from_date.isoformat()
        if to_date:
            params['to'] = to_date.isoformat()
        
        data = self._make_request(endpoint, params)
        
        if not data or not isinstance(data, list):
            logger.warning("No earnings calendar data found")
            return []
        
        return data
    
    def get_sector_performance(self) -> List[Dict[str, Any]]:
        """
        Get sector performance data
        
        Returns:
            List of sector performance records
        """
        endpoint = "sectors-performance"
        data = self._make_request(endpoint)
        
        if not data or not isinstance(data, list):
            logger.warning("No sector performance data found")
            return []
        
        return data
    
    def get_industry_pe(self, industry: str) -> Optional[Dict[str, Any]]:
        """
        Get industry P/E ratio
        
        Args:
            industry: Industry name
            
        Returns:
            Industry P/E data
        """
        endpoint = f"industry_price_earning_ratio"
        params = {"industry": industry}
        
        data = self._make_request(endpoint, params)
        
        if not data or not isinstance(data, list) or len(data) == 0:
            logger.warning(f"No P/E data found for industry: {industry}")
            return None
        
        return data[0]
    
    def search_companies(
        self,
        query: str,
        limit: int = 10,
        exchange: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for companies
        
        Args:
            query: Search query string
            limit: Maximum number of results
            exchange: Exchange filter (e.g., 'NASDAQ', 'NYSE')
            
        Returns:
            List of matching companies
        """
        endpoint = "search"
        params = {"query": query, "limit": limit}
        
        if exchange:
            params['exchange'] = exchange
        
        data = self._make_request(endpoint, params)
        
        if not data or not isinstance(data, list):
            logger.warning(f"No companies found for query: {query}")
            return []
        
        return data
    
    def get_stock_screener(
        self,
        market_cap_more_than: Optional[int] = None,
        market_cap_lower_than: Optional[int] = None,
        price_more_than: Optional[float] = None,
        price_lower_than: Optional[float] = None,
        beta_more_than: Optional[float] = None,
        beta_lower_than: Optional[float] = None,
        volume_more_than: Optional[int] = None,
        volume_lower_than: Optional[int] = None,
        sector: Optional[str] = None,
        industry: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Screen stocks based on criteria
        
        Args:
            Various screening parameters
            
        Returns:
            List of matching stocks
        """
        endpoint = "stock-screener"
        params = {"limit": limit}
        
        if market_cap_more_than:
            params['marketCapMoreThan'] = market_cap_more_than
        if market_cap_lower_than:
            params['marketCapLowerThan'] = market_cap_lower_than
        if price_more_than:
            params['priceMoreThan'] = price_more_than
        if price_lower_than:
            params['priceLowerThan'] = price_lower_than
        if beta_more_than:
            params['betaMoreThan'] = beta_more_than
        if beta_lower_than:
            params['betaLowerThan'] = beta_lower_than
        if volume_more_than:
            params['volumeMoreThan'] = volume_more_than
        if volume_lower_than:
            params['volumeLowerThan'] = volume_lower_than
        if sector:
            params['sector'] = sector
        if industry:
            params['industry'] = industry
        
        data = self._make_request(endpoint, params)
        
        if not data or not isinstance(data, list):
            logger.warning("No stocks found matching criteria")
            return []
        
        return data
    
    def get_real_time_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get real-time quote data including current price, market cap, shares
        
        Args:
            symbol: Company ticker symbol
            
        Returns:
            Real-time quote data
        """
        endpoint = f"quote/{symbol}"
        data = self._make_request(endpoint)
        
        if not data or not isinstance(data, list) or len(data) == 0:
            logger.warning(f"No real-time quote found for {symbol}")
            return None
        
        return data[0]
    
    def get_shares_outstanding(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get shares outstanding (basic and diluted)
        
        Args:
            symbol: Company ticker symbol
            
        Returns:
            Shares data with outstanding and float
        """
        # Use key metrics endpoint which includes shares data
        endpoint = f"key-metrics/{symbol}"
        params = {"limit": 1}
        
        data = self._make_request(endpoint, params)
        
        if not data or not isinstance(data, list) or len(data) == 0:
            logger.warning(f"No shares data found for {symbol}")
            return None
        
        metrics = data[0]
        return {
            'symbol': symbol,
            'shares_outstanding': metrics.get('weightedAverageShsOut'),
            'shares_outstanding_diluted': metrics.get('weightedAverageShsOutDil'),
            'date': metrics.get('date')
        }
    
    def get_current_market_cap(self, symbol: str) -> Optional[Decimal]:
        """
        Get current market capitalization
        
        Args:
            symbol: Company ticker symbol
            
        Returns:
            Market cap as Decimal
        """
        quote = self.get_real_time_quote(symbol)
        if quote and quote.get('marketCap'):
            return Decimal(str(quote['marketCap']))
        return None
    
    def get_current_price(self, symbol: str) -> Optional[Decimal]:
        """
        Get current stock price
        
        Args:
            symbol: Company ticker symbol
            
        Returns:
            Current price as Decimal
        """
        quote = self.get_real_time_quote(symbol)
        if quote and quote.get('price'):
            return Decimal(str(quote['price']))
        return None
    
    def get_market_data_snapshot(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive real-time market data snapshot
        
        Args:
            symbol: Company ticker symbol
            
        Returns:
            Dictionary with all current market data
        """
        logger.info(f"Fetching market data snapshot for {symbol}")
        
        quote = self.get_real_time_quote(symbol)
        shares = self.get_shares_outstanding(symbol)
        
        if not quote:
            logger.warning(f"Could not retrieve market data for {symbol}")
            return {}
        
        snapshot = {
            'symbol': symbol,
            'timestamp': datetime.utcnow().isoformat(),
            'price': Decimal(str(quote.get('price', 0))),
            'change': quote.get('change'),
            'change_percent': quote.get('changesPercentage'),
            'day_low': quote.get('dayLow'),
            'day_high': quote.get('dayHigh'),
            'year_low': quote.get('yearLow'),
            'year_high': quote.get('yearHigh'),
            'market_cap': Decimal(str(quote.get('marketCap', 0))),
            'volume': quote.get('volume'),
            'avg_volume': quote.get('avgVolume'),
            'open': quote.get('open'),
            'previous_close': quote.get('previousClose'),
            'eps': quote.get('eps'),
            'pe': quote.get('pe'),
            'shares_outstanding': shares.get('shares_outstanding') if shares else None,
            'shares_outstanding_diluted': shares.get('shares_outstanding_diluted') if shares else None
        }
        
        return snapshot
    
    def get_income_statement_ttm(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get TTM (Trailing Twelve Months) income statement from FMP
        
        Args:
            symbol: Company ticker symbol
            
        Returns:
            List with single TTM income statement
        """
        # FMP provides as-reported data; we sum last 4 quarters for TTM
        endpoint = f"income-statement-as-reported/{symbol}"
        params = {"period": "quarter", "limit": 4}
        
        data = self._make_request(endpoint, params)
        
        if not data or not isinstance(data, list) or len(data) < 4:
            logger.warning(f"Insufficient quarterly data for TTM calculation for {symbol}")
            # Fallback to regular quarterly endpoint
            return self.get_income_statement(symbol, "quarter", 1)
        
        return data
    
    def get_key_metrics_ttm(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get TTM key metrics directly from FMP
        
        Args:
            symbol: Company ticker symbol
            
        Returns:
            List with TTM key metrics
        """
        endpoint = f"key-metrics-ttm/{symbol}"
        data = self._make_request(endpoint)
        
        if not data or not isinstance(data, list):
            logger.warning(f"No TTM key metrics found for {symbol}")
            return []
        
        return data
    
    def get_ratios_ttm(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get TTM financial ratios directly from FMP
        
        Args:
            symbol: Company ticker symbol
            
        Returns:
            List with TTM ratios
        """
        endpoint = f"ratios-ttm/{symbol}"
        data = self._make_request(endpoint)
        
        if not data or not isinstance(data, list):
            logger.warning(f"No TTM ratios found for {symbol}")
            return []
        
        return data
    
    def get_cash_flow_ttm(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get TTM cash flow statement directly from FMP
        
        Args:
            symbol: Company ticker symbol
            
        Returns:
            List with TTM cash flow
        """
        endpoint = f"cash-flow-statement-as-reported/{symbol}"
        params = {"period": "quarter", "limit": 4}
        
        data = self._make_request(endpoint, params)
        
        if not data or not isinstance(data, list) or len(data) < 4:
            logger.warning(f"Insufficient quarterly data for TTM cash flow for {symbol}")
            return self.get_cash_flow_statement(symbol, "quarter", 1)
        
        return data
    
    def get_all_financial_data(
        self,
        symbol: str,
        period: str = "quarter",
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Get all financial statements for a company
        
        Args:
            symbol: Company ticker symbol
            period: 'annual', 'quarter', or 'ttm' (trailing twelve months)
            limit: Number of periods to retrieve
            
        Returns:
            Dictionary with all financial data
        """
        current_date = datetime.utcnow()
        logger.info(f"Fetching all financial data for {symbol} (period={period}, date={current_date.date()})")
        
        # Use TTM endpoints when period is 'ttm'
        if period == "ttm":
            return {
                'profile': self.get_company_profile(symbol),
                'income_statement': self.get_income_statement_ttm(symbol),
                'balance_sheet': self.get_balance_sheet(symbol, "quarter", 1),  # Most recent quarter
                'cash_flow': self.get_cash_flow_ttm(symbol),
                'key_metrics': self.get_key_metrics_ttm(symbol),
                'ratios': self.get_ratios_ttm(symbol),
                'enterprise_value': self.get_enterprise_value(symbol, "quarter", 1),
                'market_snapshot': self.get_market_data_snapshot(symbol),
                'data_period': 'ttm',
                'data_date': current_date.isoformat()
            }
        
        # Regular annual or quarterly data
        return {
            'profile': self.get_company_profile(symbol),
            'income_statement': self.get_income_statement(symbol, period, limit),
            'balance_sheet': self.get_balance_sheet(symbol, period, limit),
            'cash_flow': self.get_cash_flow_statement(symbol, period, limit),
            'key_metrics': self.get_key_metrics(symbol, period, limit),
            'ratios': self.get_financial_ratios(symbol, period, limit),
            'enterprise_value': self.get_enterprise_value(symbol, period, limit),
            'market_snapshot': self.get_market_data_snapshot(symbol),
            'data_period': period,
            'data_date': current_date.isoformat()
        }
    
    def _fetch_peers_bulk_data(self, force_refresh: bool = False) -> Dict[str, List[str]]:
        """
        Fetch ALL peers data from the bulk CSV endpoint and cache it.
        This endpoint returns data for all ~80,000 stocks at once.
        
        Args:
            force_refresh: Force refresh even if cache is valid
            
        Returns:
            Dictionary mapping symbol -> list of peer symbols
        """
        # Check cache validity
        if not force_refresh and self._peers_cache and self._peers_cache_timestamp:
            age = (datetime.utcnow() - self._peers_cache_timestamp).total_seconds()
            if age < self._peers_cache_ttl:
                logger.debug(f"Using cached peers data (age: {age:.0f}s)")
                return self._peers_cache
        
        logger.info("Fetching peers bulk data (CSV) from FMP API...")
        
        # Use v4 bulk endpoint (no symbol parameter - returns ALL data)
        url = f"https://financialmodelingprep.com/api/v4/stock_peers_bulk"
        params = {'apikey': self.api_key}
        
        try:
            response = self.session.get(url, params=params, timeout=60)
            response.raise_for_status()
            
            # Check if it's CSV (should be)
            content_type = response.headers.get('Content-Type', '')
            if 'csv' not in content_type.lower() and 'text' not in content_type.lower():
                logger.warning(f"Unexpected content type: {content_type}")
            
            # Parse CSV response
            csv_data = StringIO(response.text)
            reader = csv.DictReader(csv_data)
            
            peers_dict = {}
            for row in reader:
                symbol = row.get('symbol', '').strip('"').strip()
                peers_str = row.get('peers', '').strip('"').strip()
                
                if symbol and peers_str:
                    # Parse comma-separated peer list
                    peer_list = [p.strip() for p in peers_str.split(',') if p.strip()]
                    peers_dict[symbol] = peer_list
            
            # Update cache
            self._peers_cache = peers_dict
            self._peers_cache_timestamp = datetime.utcnow()
            
            logger.success(
                f"✓ Loaded peers data for {len(peers_dict):,} symbols "
                f"({len(response.text):,} bytes)"
            )
            
            return peers_dict
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch peers bulk data: {str(e)}")
            
            # If cache exists (even if stale), use it
            if self._peers_cache:
                logger.warning("Using stale cache due to API error")
                return self._peers_cache
            
            return {}
    
    def get_stock_peers(self, symbol: str, force_refresh: bool = False) -> List[str]:
        """
        Get peer/comparable companies for a stock from bulk data cache.
        
        The FMP v4/stock_peers_bulk endpoint returns CSV data for ALL stocks (~80K+).
        We fetch it once, cache it, and extract peers for the requested symbol.
        
        Args:
            symbol: Company ticker symbol
            force_refresh: Force refresh the entire bulk cache (rate limited to 10s)
            
        Returns:
            List of peer ticker symbols
        """
        # Fetch/refresh bulk data
        peers_dict = self._fetch_peers_bulk_data(force_refresh=force_refresh)
        
        # Lookup symbol in cache
        symbol_upper = symbol.upper()
        peers_list = peers_dict.get(symbol_upper, [])
        
        if peers_list:
            logger.info(f"Found {len(peers_list)} peers for {symbol}: {', '.join(peers_list[:10])}")
        else:
            logger.warning(f"No peers found for {symbol} in bulk data")
        
        return peers_list
    
    def get_peers_with_complete_data(
        self,
        symbol: str,
        max_peers: int = 10,
        minimum_required: int = 5,
        period: str = "annual",
        strict_mode: bool = True
    ) -> List[Dict[str, Any]]:
        """
        STRICT TWO-STEP PEER FETCHING - NO FALLBACKS
        
        Step 1: Get peer list from FMP API
        Step 2: Validate EVERY field for each peer (fail if insufficient)
        
        Args:
            symbol: Target company ticker
            max_peers: Maximum number of peers to return
            minimum_required: Minimum peers needed (raises error if not met)
            period: 'annual' or 'quarter'
            strict_mode: If True, raises exception on insufficient peers
            
        Returns:
            List of peer dictionaries with COMPLETE data
            
        Raises:
            ValueError: If insufficient peers with complete data (in strict mode)
        """
        logger.info(f"🔍 STRICT PEER FETCHING for {symbol} (min required: {minimum_required})")
        
        # STEP 1: Get peer list from FMP API
        peers = self.get_stock_peers(symbol)
        if not peers:
            error_msg = (
                f"NO PEERS FOUND for {symbol} from FMP API.\n\n"
                f"RESOLUTION:\n"
                f"1. Verify {symbol} is a valid ticker\n"
                f"2. Check if FMP has peer data for this symbol\n"
                f"3. Consider using sector-based peer selection as alternative\n"
                f"4. This platform does NOT use fallback methods in strict mode"
            )
            logger.error(error_msg)
            if strict_mode:
                raise ValueError(error_msg)
            return []
        
        logger.info(f"  Step 1: Found {len(peers)} potential peers: {', '.join(peers[:10])}")
        
        # STEP 2: Fetch and validate EACH peer with ZERO tolerance
        complete_peers = []
        validation_results = {
            'total_checked': 0,
            'passed': 0,
            'failed': 0,
            'failures': []
        }
        
        for peer_symbol in peers[:max_peers + 10]:  # Check more than needed
            if len(complete_peers) >= max_peers:
                logger.info(f"  Reached maximum {max_peers} peers, stopping")
                break
            
            validation_results['total_checked'] += 1
            
            try:
                # Get all data for peer
                peer_data = self.get_all_financial_data(peer_symbol, period=period, limit=1)
                
                # STRICT validation - ALL fields required
                validation_result =  self._validate_peer_data_strict(peer_data, peer_symbol)
                
                if validation_result['is_valid']:
                    complete_peers.append({
                        'symbol': peer_symbol,
                        **peer_data
                    })
                    validation_results['passed'] += 1
                    logger.debug(f"  ✓ {peer_symbol}: COMPLETE ({validation_results['passed']}/{minimum_required})")
                else:
                    validation_results['failed'] += 1
                    validation_results['failures'].append({
                        'symbol': peer_symbol,
                        'missing_fields': validation_result['missing_fields']
                    })
                    logger.debug(f"  ✗ {peer_symbol}: INCOMPLETE - {', '.join(validation_result['missing_fields'])}")
                    
            except Exception as e:
                validation_results['failed'] += 1
                validation_results['failures'].append({
                    'symbol': peer_symbol,
                    'error': str(e)
                })
                logger.debug(f"  ✗ {peer_symbol}: ERROR - {str(e)}")
                continue
        
        # Check if we have minimum required peers
        peers_found = len(complete_peers)
        
        if peers_found < minimum_required:
            error_msg = (
                f"INSUFFICIENT PEER DATA: Only {peers_found}/{minimum_required} peers with complete data.\n\n"
                f"VALIDATION SUMMARY:\n"
                f"  Total Checked: {validation_results['total_checked']}\n"
                f"  Passed:        {validation_results['passed']} ✓\n"
                f"  Failed:        {validation_results['failed']} ✗\n"
                f"  Success Rate:  {validation_results['passed']/validation_results['total_checked']*100:.1f}%\n\n"
                f"FAILED PEERS DETAIL:\n"
            )
            
            for i, failure in enumerate(validation_results['failures'][:5], 1):
                symbol = failure['symbol']
                if 'missing_fields' in failure:
                    error_msg += f"  {i}. {symbol}: Missing {', '.join(failure['missing_fields'])}\n"
                else:
                    error_msg += f"  {i}. {symbol}: {failure.get('error', 'Unknown error')}\n"
            
            if len(validation_results['failures']) > 5:
                error_msg += f"  ...and {len(validation_results['failures']) - 5} more\n"
            
            error_msg += (
                f"\nRESOLUTION:\n"
                f"1. Expand peer universe (check more symbols)\n"
                f"2. Verify FMP data completeness for this sector\n"
                f"3. Consider alternative data sources\n"
                f"4. This platform does NOT use incomplete data or fallbacks\n"
                f"5. Analysis REQUIRES complete, validated peer data"
            )
            
            logger.error(error_msg)
            
            if strict_mode:
                raise ValueError(error_msg)
        else:
            logger.success(
                f"✓ PEER VALIDATION COMPLETE: {peers_found} peers with COMPLETE data "
                f"(checked {validation_results['total_checked']}, "
                f"success rate: {validation_results['passed']/validation_results['total_checked']*100:.1f}%)"
            )
        
        return complete_peers
    
    def _validate_peer_data_strict(self, data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """
        STRICT peer data validation - ALL required fields must be present
        
        Args:
            data: Peer financial data dictionary
            symbol: Peer symbol for error reporting
            
        Returns:
            Dictionary with validation results and missing fields
        """
        missing_fields = []
        
        # Required: Income Statement
        if not data.get('income_statement') or len(data['income_statement']) == 0:
            missing_fields.append('income_statement')
            return {'is_valid': False, 'missing_fields': missing_fields}
        
        inc_stmt = data['income_statement'][0]
        
        # Critical income statement fields
        required_inc_fields = {
            'revenue': 'Revenue',
            'costOfRevenue': 'Cost of Revenue',
            'grossProfit': 'Gross Profit',
            'operatingExpenses': 'Operating Expenses',
            'ebitda': 'EBITDA',
            'operatingIncome': 'Operating Income (EBIT)',
            'netIncome': 'Net Income'
        }
        
        for field, description in required_inc_fields.items():
            if not inc_stmt.get(field) or inc_stmt.get(field) == 0:
                missing_fields.append(f'income_statement.{field}')
        
        # Required: Balance Sheet
        if not data.get('balance_sheet') or len(data['balance_sheet']) == 0:
            missing_fields.append('balance_sheet')
        else:
            bal_sheet = data['balance_sheet'][0]
            required_bal_fields = {
                'totalAssets': 'Total Assets',
                'totalLiabilities': 'Total Liabilities',
                'totalStockholdersEquity': 'Stockholders Equity',
                'cashAndCashEquivalents': 'Cash',
                'totalDebt': 'Total Debt'
            }
            
            for field, description in required_bal_fields.items():
                if not bal_sheet.get(field):
                    missing_fields.append(f'balance_sheet.{field}')
        
        # Required: Cash Flow
        if not data.get('cash_flow') or len(data['cash_flow']) == 0:
            missing_fields.append('cash_flow')
        else:
            cf = data['cash_flow'][0]
            if not cf.get('operatingCashFlow'):
                missing_fields.append('cash_flow.operatingCashFlow')
        
        # Required: Market Snapshot
        if not data.get('market_snapshot'):
            missing_fields.append('market_snapshot')
        else:
            market = data['market_snapshot']
            # Only market_cap and price are critical (shares can be calculated)
            required_market_fields = {
                'market_cap': 'Market Cap',
                'price': 'Stock Price'
            }
            
            for field, description in required_market_fields.items():
                value = market.get(field)
                if value is None or (isinstance(value, (int, float)) and value == 0):
                    missing_fields.append(f'market_snapshot.{field}')
        
        # Required: Key Metrics (for ratios and growth)
        if not data.get('key_metrics') or len(data['key_metrics']) == 0:
            missing_fields.append('key_metrics')
        else:
            metrics = data['key_metrics'][0]
            # Growth metrics should exist (can be negative but not None)
            if metrics.get('revenuePerShare') is None:
                missing_fields.append('key_metrics.revenuePerShare')
        
        # Required: Enterprise Value
        if not data.get('enterprise_value') or len(data['enterprise_value']) == 0:
            missing_fields.append('enterprise_value')
        else:
            ev = data['enterprise_value'][0]
            if not ev.get('enterpriseValue') or ev.get('enterpriseValue') == 0:
                missing_fields.append('enterprise_value.enterpriseValue')
        
        is_valid = len(missing_fields) == 0
        
        return {
            'is_valid': is_valid,
            'missing_fields': missing_fields
        }
    
    def _find_industry_peers(self, industry: str, limit: int = 10) -> List[str]:
        """
        Find peers by industry using stock screener
        
        Args:
            industry: Industry name
            limit: Maximum number to return
            
        Returns:
            List of ticker symbols
        """
        try:
            peers = self.get_stock_screener(
                industry=industry,
                market_cap_more_than=100_000_000,  # Min $100M market cap
                limit=limit
            )
            return [p['symbol'] for p in peers if p.get('symbol')]
        except:
            return []
