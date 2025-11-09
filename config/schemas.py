"""
Data Contracts & Schemas for FMNA Platform
Defines the core data structures for the M&A analytics platform
"""

from datetime import datetime
from datetime import date as date_type
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


class FrequencyType(str, Enum):
    """Financial reporting frequency"""
    ANNUAL = "annual"
    QUARTERLY = "quarterly"
    TTM = "ttm"
    MONTHLY = "monthly"


class CurrencyType(str, Enum):
    """Supported currencies"""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CNY = "CNY"
    CAD = "CAD"
    AUD = "AUD"


class DataSourceType(str, Enum):
    """Data source identifiers"""
    FMP = "fmp"
    EDGAR = "edgar"
    SEC_API = "sec_api"
    MANUAL = "manual"
    CALCULATED = "calculated"


class CompanyMaster(BaseModel):
    """Company dimension table - master company data"""
    cik: str = Field(..., description="SEC Central Index Key")
    fmp_symbol: Optional[str] = Field(None, description="FMP ticker symbol")
    legal_name: str = Field(..., description="Legal entity name")
    domicile: str = Field(..., description="Country of incorporation")
    currency: CurrencyType = Field(..., description="Reporting currency")
    sector: Optional[str] = Field(None, description="Industry sector")
    industry: Optional[str] = Field(None, description="Industry classification")
    fiscal_year_end: Optional[str] = Field(None, description="Fiscal year end month")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class FinancialFact(BaseModel):
    """Financial statement facts table"""
    symbol: str = Field(..., description="Company ticker symbol")
    period_end: date_type = Field(..., description="Period end date")
    frequency: FrequencyType = Field(..., description="Reporting frequency")
    metric: str = Field(..., description="Metric name (normalized)")
    value: Decimal = Field(..., description="Metric value")
    source_ref: str = Field(..., description="Source document reference")
    as_reported: bool = Field(True, description="True if as-reported, False if restated")
    restated: bool = Field(False, description="True if this is a restatement")
    currency: CurrencyType = Field(..., description="Value currency")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SegmentFact(BaseModel):
    """Segment-level financial data"""
    symbol: str = Field(..., description="Company ticker symbol")
    period_end: date_type = Field(..., description="Period end date")
    segment_name: str = Field(..., description="Segment or business unit name")
    geography: Optional[str] = Field(None, description="Geographic region")
    revenue: Optional[Decimal] = Field(None, description="Segment revenue")
    ebit: Optional[Decimal] = Field(None, description="Segment EBIT")
    ebitda: Optional[Decimal] = Field(None, description="Segment EBITDA")
    capex: Optional[Decimal] = Field(None, description="Segment CapEx")
    assets: Optional[Decimal] = Field(None, description="Segment assets")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MarketData(BaseModel):
    """Daily market data and valuation metrics"""
    symbol: str = Field(..., description="Company ticker symbol")
    trade_date: date_type = Field(..., description="Trading date")
    open: Optional[Decimal] = Field(None, description="Opening price")
    high: Optional[Decimal] = Field(None, description="High price")
    low: Optional[Decimal] = Field(None, description="Low price")
    close: Decimal = Field(..., description="Closing price")
    volume: Optional[int] = Field(None, description="Trading volume")
    market_cap: Optional[Decimal] = Field(None, description="Market capitalization")
    enterprise_value: Optional[Decimal] = Field(None, description="Enterprise value")
    shares_outstanding: Optional[Decimal] = Field(None, description="Shares outstanding")
    shares_diluted: Optional[Decimal] = Field(None, description="Diluted shares")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Transaction(BaseModel):
    """M&A transaction / precedent transaction data"""
    transaction_id: str = Field(..., description="Unique transaction identifier")
    acquirer_symbol: Optional[str] = Field(None, description="Acquirer ticker")
    acquirer_name: str = Field(..., description="Acquirer name")
    target_symbol: Optional[str] = Field(None, description="Target ticker")
    target_name: str = Field(..., description="Target name")
    announce_date: date_type = Field(..., description="Announcement date")
    close_date: Optional[date_type] = Field(None, description="Transaction close date")
    deal_value: Optional[Decimal] = Field(None, description="Total deal value")
    enterprise_value: Optional[Decimal] = Field(None, description="Enterprise value")
    equity_value: Optional[Decimal] = Field(None, description="Equity value")
    ev_revenue: Optional[Decimal] = Field(None, description="EV/Revenue multiple")
    ev_ebitda: Optional[Decimal] = Field(None, description="EV/EBITDA multiple")
    ev_ebit: Optional[Decimal] = Field(None, description="EV/EBIT multiple")
    pe_ratio: Optional[Decimal] = Field(None, description="P/E ratio")
    premium_1d: Optional[Decimal] = Field(None, description="1-day premium %")
    premium_1w: Optional[Decimal] = Field(None, description="1-week premium %")
    premium_4w: Optional[Decimal] = Field(None, description="4-week premium %")
    deal_type: Optional[str] = Field(None, description="Type of transaction")
    rationale: Optional[str] = Field(None, description="Strategic rationale")
    synergies: Optional[Decimal] = Field(None, description="Expected synergies")
    payment_method: Optional[str] = Field(None, description="Cash, stock, or mixed")
    status: str = Field(..., description="Pending, completed, terminated")
    notes: Optional[str] = Field(None, description="Additional notes")
    source_ref: str = Field(..., description="Data source reference")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PeerSet(BaseModel):
    """Peer company relationships"""
    symbol: str = Field(..., description="Company ticker symbol")
    peer_symbol: str = Field(..., description="Peer company ticker")
    method: str = Field(..., description="Selection method: sector, nearest-neighbor, manual")
    distance: Optional[float] = Field(None, description="Distance metric for nearest-neighbor")
    included: bool = Field(True, description="Whether peer is included in analysis")
    weight: Optional[float] = Field(None, description="Weighting in peer group")
    rationale: Optional[str] = Field(None, description="Inclusion/exclusion reasoning")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Filing(BaseModel):
    """SEC filing metadata"""
    filing_id: str = Field(..., description="Unique filing identifier")
    cik: str = Field(..., description="Company CIK")
    symbol: Optional[str] = Field(None, description="Ticker symbol")
    filing_type: str = Field(..., description="10-K, 10-Q, 8-K, etc.")
    filing_date: date_type = Field(..., description="Filing date")
    period_end: date_type = Field(..., description="Period end date")
    accession_number: str = Field(..., description="SEC accession number")
    url: str = Field(..., description="Filing URL")
    full_text: Optional[str] = Field(None, description="Full filing text")
    items_extracted: Optional[List[str]] = Field(None, description="Extracted items (e.g., Item 7, 7A)")
    processed: bool = Field(False, description="Whether filing has been processed")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FilingSection(BaseModel):
    """Extracted sections from SEC filings"""
    section_id: str = Field(..., description="Unique section identifier")
    filing_id: str = Field(..., description="Parent filing ID")
    item_number: str = Field(..., description="Item number (e.g., 7, 7A)")
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content/text")
    start_page: Optional[int] = Field(None, description="Starting page number")
    end_page: Optional[int] = Field(None, description="Ending page number")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RiskCard(BaseModel):
    """Risk assessment card from due diligence"""
    risk_id: str = Field(..., description="Unique risk identifier")
    symbol: str = Field(..., description="Company ticker symbol")
    category: str = Field(..., description="Financial, Legal, Commercial, Tech, ESG, etc.")
    subcategory: Optional[str] = Field(None, description="Risk subcategory")
    severity: str = Field(..., description="Low, Medium, High, Critical")
    title: str = Field(..., description="Risk title")
    description: str = Field(..., description="Detailed risk description")
    impact: Optional[Decimal] = Field(None, description="Financial impact estimate")
    probability: Optional[float] = Field(None, description="Probability (0-1)")
    mitigation: Optional[str] = Field(None, description="Mitigation strategies")
    source_ref: Optional[str] = Field(None, description="Source document reference")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ValuationScenario(BaseModel):
    """Valuation scenario configuration"""
    scenario_id: str = Field(..., description="Unique scenario identifier")
    symbol: str = Field(..., description="Company ticker symbol")
    scenario_name: str = Field(..., description="Base, Bull, Bear, etc.")
    method: str = Field(..., description="DCF, CCA, Precedent, LBO, etc.")
    assumptions: Dict[str, Any] = Field(..., description="Key assumptions")
    valuation: Decimal = Field(..., description="Calculated valuation")
    equity_value: Optional[Decimal] = Field(None, description="Equity value")
    value_per_share: Optional[Decimal] = Field(None, description="Value per share")
    irr: Optional[float] = Field(None, description="IRR for LBO scenarios")
    moic: Optional[float] = Field(None, description="MoIC for LBO scenarios")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Clause(BaseModel):
    """Legal clause extracted from contracts/filings"""
    clause_id: str = Field(..., description="Unique clause identifier")
    filing_id: str = Field(..., description="Source filing ID")
    clause_type: str = Field(..., description="Change-of-control, indemnity, etc.")
    title: str = Field(..., description="Clause title")
    text: str = Field(..., description="Clause text")
    risk_rating: Optional[str] = Field(None, description="Low, Medium, High")
    page_span: Optional[str] = Field(None, description="Page numbers")
    analysis: Optional[str] = Field(None, description="LLM analysis of clause")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ModelLineage(BaseModel):
    """Data lineage tracking for Palantir-style governance"""
    lineage_id: str = Field(..., description="Unique lineage identifier")
    dataset_name: str = Field(..., description="Dataset or model name")
    version: str = Field(..., description="Version identifier")
    parent_ids: List[str] = Field(default_factory=list, description="Parent dataset IDs")
    transformation: str = Field(..., description="Transformation description")
    code_ref: Optional[str] = Field(None, description="Code reference")
    user: str = Field(..., description="User who created this version")
    hash: str = Field(..., description="Dataset hash for integrity")
    approved: bool = Field(False, description="Approval status")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CogneeNode(BaseModel):
    """Node structure for Cognee knowledge graph"""
    node_id: str = Field(..., description="Unique node identifier")
    node_type: str = Field(..., description="Filing, Table, Clause, Peer, Deal, etc.")
    properties: Dict[str, Any] = Field(..., description="Node properties")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CogneeEdge(BaseModel):
    """Edge structure for Cognee knowledge graph"""
    edge_id: str = Field(..., description="Unique edge identifier")
    source_node_id: str = Field(..., description="Source node ID")
    target_node_id: str = Field(..., description="Target node ID")
    relationship_type: str = Field(..., description="supports, contradicts, derived-from, etc.")
    properties: Optional[Dict[str, Any]] = Field(None, description="Edge properties")
    weight: Optional[float] = Field(None, description="Relationship strength")
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Normalized metric names for Chart of Accounts mapping
NORMALIZED_METRICS = {
    # Income Statement
    "revenue": ["total_revenue", "net_revenue", "sales", "total_sales"],
    "cogs": ["cost_of_revenue", "cost_of_goods_sold", "cost_of_sales"],
    "gross_profit": ["gross_income"],
    "opex": ["operating_expenses", "total_operating_expenses"],
    "sg&a": ["sga", "selling_general_administrative"],
    "r&d": ["research_development", "research_and_development"],
    "ebitda": ["adjusted_ebitda", "ebitda_normalized"],
    "ebit": ["operating_income", "operating_profit"],
    "interest_expense": ["interest_paid", "interest_cost"],
    "ebt": ["pretax_income", "income_before_tax"],
    "tax_expense": ["income_tax", "provision_for_taxes"],
    "net_income": ["net_earnings", "profit", "net_profit"],
    
    # Balance Sheet
    "cash": ["cash_and_equivalents", "cash_short_term_investments"],
    "ar": ["accounts_receivable", "receivables"],
    "inventory": ["inventories"],
    "current_assets": ["total_current_assets"],
    "ppe": ["property_plant_equipment", "fixed_assets"],
    "goodwill": ["goodwill_net"],
    "intangibles": ["intangible_assets"],
    "total_assets": ["assets"],
    "ap": ["accounts_payable", "payables"],
    "current_liabilities": ["total_current_liabilities"],
    "debt_st": ["short_term_debt", "current_debt"],
    "debt_lt": ["long_term_debt", "noncurrent_debt"],
    "total_debt": ["debt", "total_borrowings"],
    "total_liabilities": ["liabilities"],
    "equity": ["shareholders_equity", "stockholders_equity", "total_equity"],
    
    # Cash Flow Statement
    "cfo": ["operating_cash_flow", "cash_from_operations"],
    "capex": ["capital_expenditures", "capital_expenditure"],
    "cfi": ["investing_cash_flow", "cash_from_investing"],
    "cff": ["financing_cash_flow", "cash_from_financing"],
    "fcf": ["free_cash_flow"],
}
