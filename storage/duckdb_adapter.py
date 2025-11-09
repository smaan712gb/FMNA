"""
DuckDB Lakehouse Adapter
High-performance analytical database for FMNA platform
Uses Parquet files for efficient storage and querying
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import duckdb
import pandas as pd
import polars as pl
from loguru import logger

from config.settings import get_settings
from config.schemas import (
    CompanyMaster, FinancialFact, SegmentFact, 
    MarketData, Transaction, PeerSet
)


class DuckDBAdapter:
    """Adapter for DuckDB lakehouse operations"""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize DuckDB adapter
        
        Args:
            db_path: Path to DuckDB database file (uses in-memory if None)
        """
        settings = get_settings()
        
        if db_path is None:
            self.db_path = settings.data_dir / "fmna.duckdb"
        else:
            self.db_path = Path(db_path)
        
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to DuckDB
        self.conn = duckdb.connect(str(self.db_path))
        
        # Enable parallel processing
        self.conn.execute("PRAGMA threads=4")
        self.conn.execute("PRAGMA memory_limit='4GB'")
        
        logger.info(f"DuckDB adapter initialized: {self.db_path}")
        
        # Initialize schema
        self._init_schema()
    
    def _init_schema(self):
        """Create database schema (tables)"""
        
        # Company Master
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS company_master (
                cik VARCHAR PRIMARY KEY,
                fmp_symbol VARCHAR,
                legal_name VARCHAR NOT NULL,
                domicile VARCHAR,
                currency VARCHAR,
                sector VARCHAR,
                industry VARCHAR,
                fiscal_year_end VARCHAR,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        
        # Financial Facts
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS financial_facts (
                id INTEGER PRIMARY KEY,
                symbol VARCHAR NOT NULL,
                period_end DATE NOT NULL,
                frequency VARCHAR NOT NULL,
                metric VARCHAR NOT NULL,
                value DECIMAL(20, 2),
                source_ref VARCHAR,
                as_reported BOOLEAN DEFAULT true,
                restated BOOLEAN DEFAULT false,
                currency VARCHAR,
                created_at TIMESTAMP
            )
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_fin_facts_symbol 
            ON financial_facts(symbol)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_fin_facts_period 
            ON financial_facts(period_end)
        """)
        
        # Segment Facts
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS segment_facts (
                id INTEGER PRIMARY KEY,
                symbol VARCHAR NOT NULL,
                period_end DATE NOT NULL,
                segment_name VARCHAR NOT NULL,
                geography VARCHAR,
                revenue DECIMAL(20, 2),
                ebit DECIMAL(20, 2),
                ebitda DECIMAL(20, 2),
                capex DECIMAL(20, 2),
                assets DECIMAL(20, 2),
                created_at TIMESTAMP
            )
        """)
        
        # Market Data
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY,
                symbol VARCHAR NOT NULL,
                trade_date DATE NOT NULL,
                open DECIMAL(20, 4),
                high DECIMAL(20, 4),
                low DECIMAL(20, 4),
                close DECIMAL(20, 4) NOT NULL,
                volume BIGINT,
                market_cap DECIMAL(20, 2),
                enterprise_value DECIMAL(20, 2),
                shares_outstanding DECIMAL(20, 2),
                shares_diluted DECIMAL(20, 2),
                created_at TIMESTAMP,
                UNIQUE(symbol, trade_date)
            )
        """)
        
        # Transactions
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id VARCHAR PRIMARY KEY,
                acquirer_symbol VARCHAR,
                acquirer_name VARCHAR NOT NULL,
                target_symbol VARCHAR,
                target_name VARCHAR NOT NULL,
                announce_date DATE NOT NULL,
                close_date DATE,
                deal_value DECIMAL(20, 2),
                enterprise_value DECIMAL(20, 2),
                equity_value DECIMAL(20, 2),
                ev_revenue DECIMAL(10, 2),
                ev_ebitda DECIMAL(10, 2),
                ev_ebit DECIMAL(10, 2),
                pe_ratio DECIMAL(10, 2),
                premium_1d DECIMAL(10, 2),
                premium_1w DECIMAL(10, 2),
                premium_4w DECIMAL(10, 2),
                deal_type VARCHAR,
                rationale TEXT,
                synergies DECIMAL(20, 2),
                payment_method VARCHAR,
                status VARCHAR NOT NULL,
                notes TEXT,
                source_ref VARCHAR,
                created_at TIMESTAMP
            )
        """)
        
        # Peer Sets
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS peer_sets (
                id INTEGER PRIMARY KEY,
                symbol VARCHAR NOT NULL,
                peer_symbol VARCHAR NOT NULL,
                method VARCHAR NOT NULL,
                distance DOUBLE,
                included BOOLEAN DEFAULT true,
                weight DOUBLE,
                rationale TEXT,
                created_at TIMESTAMP,
                UNIQUE(symbol, peer_symbol)
            )
        """)
        
        logger.info("DuckDB schema initialized")
    
    def insert_company(self, company: CompanyMaster) -> bool:
        """Insert or update company master record"""
        try:
            self.conn.execute("""
                INSERT OR REPLACE INTO company_master 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                company.cik,
                company.fmp_symbol,
                company.legal_name,
                company.domicile,
                company.currency.value if hasattr(company.currency, 'value') else company.currency,
                company.sector,
                company.industry,
                company.fiscal_year_end,
                company.created_at,
                company.updated_at
            ])
            logger.debug(f"Inserted company: {company.legal_name} ({company.cik})")
            return True
        except Exception as e:
            logger.error(f"Error inserting company: {str(e)}")
            return False
    
    def bulk_insert_financial_facts(self, facts: List[FinancialFact]) -> int:
        """Bulk insert financial facts using Parquet for speed"""
        try:
            # Convert to pandas DataFrame
            data = []
            for fact in facts:
                data.append({
                    'symbol': fact.symbol,
                    'period_end': fact.period_end,
                    'frequency': fact.frequency.value if hasattr(fact.frequency, 'value') else fact.frequency,
                    'metric': fact.metric,
                    'value': float(fact.value),
                    'source_ref': fact.source_ref,
                    'as_reported': fact.as_reported,
                    'restated': fact.restated,
                    'currency': fact.currency.value if hasattr(fact.currency, 'value') else fact.currency,
                    'created_at': fact.created_at
                })
            
            df = pd.DataFrame(data)
            
            # Use DuckDB's efficient bulk insert
            self.conn.execute("""
                INSERT INTO financial_facts 
                SELECT NULL as id, * FROM df
            """)
            
            logger.info(f"Bulk inserted {len(facts)} financial facts")
            return len(facts)
            
        except Exception as e:
            logger.error(f"Error bulk inserting financial facts: {str(e)}")
            return 0
    
    def get_financials(
        self,
        symbol: str,
        metrics: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        frequency: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Query financial facts with filters
        
        Args:
            symbol: Company ticker symbol
            metrics: List of metric names to retrieve
            start_date: Start date filter
            end_date: End date filter
            frequency: Frequency filter (annual, quarterly, ttm)
            
        Returns:
            DataFrame with financial data
        """
        query = "SELECT * FROM financial_facts WHERE symbol = ?"
        params = [symbol]
        
        if metrics:
            placeholders = ', '.join(['?' for _ in metrics])
            query += f" AND metric IN ({placeholders})"
            params.extend(metrics)
        
        if start_date:
            query += " AND period_end >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND period_end <= ?"
            params.append(end_date)
        
        if frequency:
            query += " AND frequency = ?"
            params.append(frequency)
        
        query += " ORDER BY period_end DESC, metric"
        
        return self.conn.execute(query, params).df()
    
    def get_peers(
        self,
        symbol: str,
        included_only: bool = True,
        method: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get peer companies for a given symbol
        
        Args:
            symbol: Company ticker symbol
            included_only: Only return included peers
            method: Filter by selection method
            
        Returns:
            DataFrame with peer data
        """
        query = "SELECT * FROM peer_sets WHERE symbol = ?"
        params = [symbol]
        
        if included_only:
            query += " AND included = true"
        
        if method:
            query += " AND method = ?"
            params.append(method)
        
        query += " ORDER BY weight DESC"
        
        return self.conn.execute(query, params).df()
    
    def get_transactions(
        self,
        target_sector: Optional[str] = None,
        min_ev: Optional[float] = None,
        max_ev: Optional[float] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Query M&A transactions with filters
        
        Args:
            target_sector: Filter by target sector
            min_ev: Minimum enterprise value
            max_ev: Maximum enterprise value
            start_date: Minimum announcement date
            end_date: Maximum announcement date
            status: Transaction status
            
        Returns:
            DataFrame with transaction data
        """
        query = "SELECT * FROM transactions WHERE 1=1"
        params = []
        
        if target_sector:
            query += """ 
                AND target_symbol IN (
                    SELECT fmp_symbol FROM company_master WHERE sector = ?
                )
            """
            params.append(target_sector)
        
        if min_ev is not None:
            query += " AND enterprise_value >= ?"
            params.append(min_ev)
        
        if max_ev is not None:
            query += " AND enterprise_value <= ?"
            params.append(max_ev)
        
        if start_date:
            query += " AND announce_date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND announce_date <= ?"
            params.append(end_date)
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY announce_date DESC"
        
        return self.conn.execute(query, params).df()
    
    def pivot_financials(
        self,
        symbol: str,
        metrics: List[str],
        frequency: str = "annual"
    ) -> pd.DataFrame:
        """
        Pivot financial data to wide format (metrics as columns, periods as rows)
        
        Args:
            symbol: Company ticker symbol
            metrics: List of metrics to pivot
            frequency: Data frequency
            
        Returns:
            Pivoted DataFrame
        """
        placeholders = ', '.join(['?' for _ in metrics])
        
        query = f"""
            SELECT 
                period_end,
                metric,
                value
            FROM financial_facts
            WHERE symbol = ?
                AND frequency = ?
                AND metric IN ({placeholders})
            ORDER BY period_end DESC
        """
        
        params = [symbol, frequency] + metrics
        df = self.conn.execute(query, params).df()
        
        # Pivot to wide format
        if not df.empty:
            df = df.pivot(index='period_end', columns='metric', values='value')
            df = df.reset_index()
        
        return df
    
    def export_to_parquet(
        self,
        table_name: str,
        output_path: Path,
        filters: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Export table to Parquet file
        
        Args:
            table_name: Name of table to export
            output_path: Output Parquet file path
            filters: Optional filters (WHERE clause)
            
        Returns:
            Success status
        """
        try:
            query = f"COPY (SELECT * FROM {table_name}"
            
            if filters:
                where_clauses = []
                params = []
                for key, value in filters.items():
                    where_clauses.append(f"{key} = ?")
                    params.append(value)
                
                query += " WHERE " + " AND ".join(where_clauses)
                query += f") TO '{output_path}' (FORMAT PARQUET)"
                
                self.conn.execute(query, params)
            else:
                query += f") TO '{output_path}' (FORMAT PARQUET)"
                self.conn.execute(query)
            
            logger.info(f"Exported {table_name} to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to Parquet: {str(e)}")
            return False
    
    def load_from_parquet(
        self,
        table_name: str,
        parquet_path: Path,
        append: bool = True
    ) -> bool:
        """
        Load data from Parquet file into table
        
        Args:
            table_name: Target table name
            parquet_path: Parquet file path
            append: If True, append; if False, replace
            
        Returns:
            Success status
        """
        try:
            if not append:
                self.conn.execute(f"DELETE FROM {table_name}")
            
            self.conn.execute(f"""
                INSERT INTO {table_name}
                SELECT * FROM read_parquet('{parquet_path}')
            """)
            
            logger.info(f"Loaded data from {parquet_path} into {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading from Parquet: {str(e)}")
            return False
    
    def execute_query(self, query: str, params: Optional[List] = None) -> pd.DataFrame:
        """
        Execute arbitrary SQL query
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            DataFrame with results
        """
        try:
            if params:
                return self.conn.execute(query, params).df()
            else:
                return self.conn.execute(query).df()
        except Exception as e:
            logger.error(f"Query execution error: {str(e)}")
            return pd.DataFrame()
    
    def close(self):
        """Close database connection"""
        self.conn.close()
        logger.info("DuckDB connection closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Example usage
if __name__ == "__main__":
    from datetime import date
    from decimal import Decimal
    
    # Initialize adapter
    db = DuckDBAdapter()
    
    # Insert sample company
    company = CompanyMaster(
        cik="0000320193",
        fmp_symbol="AAPL",
        legal_name="Apple Inc.",
        domicile="USA",
        currency="USD",
        sector="Technology",
        industry="Consumer Electronics"
    )
    db.insert_company(company)
    
    # Insert sample financial facts
    facts = [
        FinancialFact(
            symbol="AAPL",
            period_end=date(2023, 9, 30),
            frequency="annual",
            metric="revenue",
            value=Decimal("383285000000"),
            source_ref="10-K-2023",
            currency="USD"
        ),
        FinancialFact(
            symbol="AAPL",
            period_end=date(2023, 9, 30),
            frequency="annual",
            metric="net_income",
            value=Decimal("96995000000"),
            source_ref="10-K-2023",
            currency="USD"
        )
    ]
    db.bulk_insert_financial_facts(facts)
    
    # Query financials
    financials = db.get_financials("AAPL")
    print(financials)
    
    db.close()
