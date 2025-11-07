# FMNA Platform - Setup Guide

## Overview
FMNA is a production-grade M&A analytics platform combining:
- **FMP API** for real-time market data and financials
- **SEC EDGAR** for regulatory filings (10-K, 10-Q, 8-K, 4, S-4, etc.)
- **DeepSeek LLM** for reasoning and analysis
- **Document Upload** for PDF, Excel, Word, PowerPoint
- **Cognee** for knowledge graph storage
- **LangChain/LangGraph** for agent orchestration
- **Pydantic** for data validation

## Installation

### 1. Activate Conda Environment
```bash
conda activate fmna
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy the `.env.example` file to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Required API keys:
- **FMP_API_KEY**: Get from https://financialmodelingprep.com/developer/docs
- **DEEPSEEK_API_KEY**: Get from https://platform.deepseek.com
- **SEC_API_KEY**: Optional, for enhanced SEC API access
- **POSTGRES_PASSWORD**: Set a secure password for PostgreSQL
- **SECRET_KEY**: Generate a secure key for encryption
- **JWT_SECRET**: Generate a secure key for JWT tokens

### 4. Create Required Directories
The application will auto-create directories, but you can manually create them:

```bash
mkdir -p data/raw data/processed data/models data/uploads
mkdir -p outputs logs
```

## Features Implemented

### ✅ Data Ingestion System

#### 1. FMP API Integration (`ingestion/fmp_client.py`)
Comprehensive financial data from Financial Modeling Prep:
- **Company profiles** (CIK, sector, industry)
- **Financial statements** (Income, Balance Sheet, Cash Flow)
- **Real-time market data**:
  - Current stock price
  - Market capitalization
  - Shares outstanding (basic and diluted)
  - Trading volume
  - Day/year high/low
  - P/E ratio
- **Key metrics and ratios**
- **Enterprise value**
- **Historical prices**
- **Analyst estimates**
- **Earnings calendar**
- **Sector/industry screening**

**Usage Example:**
```python
from ingestion import FMPClient

fmp = FMPClient()

# Get real-time market data
market_data = fmp.get_market_data_snapshot('AAPL')
print(f"Price: ${market_data['price']}")
print(f"Market Cap: ${market_data['market_cap']}")
print(f"Shares Outstanding: {market_data['shares_outstanding']}")

# Get comprehensive financial data
financials = fmp.get_all_financial_data('AAPL', period='annual', limit=3)
```

#### 2. SEC EDGAR Integration (`ingestion/sec_client.py`)
**Date-Aware Filing Retrieval** with support for all major filing types:
- **10-K** - Annual Reports
- **10-Q** - Quarterly Reports
- **8-K** - Current Reports (material events)
- **4** - Insider Trading
- **S-1, S-3, S-4** - Registration Statements
- **DEF 14A, DEFM14A** - Proxy Statements
- **13D, 13G** - Beneficial Ownership Reports
- **3, 5** - Initial/Annual Beneficial Ownership

**Key Features:**
- Automatic CIK lookup from ticker symbol
- Date filtering for recent filings
- Section extraction (Item 7 MD&A, Item 7A Market Risk, Item 8 Financials, Item 1A Risk Factors)
- Rate limiting (10 requests/second per SEC guidelines)
- HTML to text conversion

**Usage Example:**
```python
from ingestion import SECClient, FILING_TYPES

sec = SECClient(email="your-email@company.com")

# Get latest 10-K
filing = sec.get_latest_filing('AAPL', filing_type='10-K')
print(f"Filing Date: {filing.filing_date}")
print(f"Sections: {filing.items_extracted}")

# Bulk download multiple filing types
filings = sec.bulk_download_filings(
    'AAPL',
    filing_types=['10-K', '10-Q', '8-K', '4'],
    num_filings=3
)
```

#### 3. Document Upload Processor (`ingestion/document_processor.py`)
**User Upload Support** for multiple formats:
- **PDF** - Text and table extraction
- **Excel** (.xlsx, .xls, .xlsm) - Multi-sheet data extraction
- **Word** (.docx) - Paragraphs and tables
- **PowerPoint** (.pptx) - Slide content and tables
- **CSV** - Structured data import
- **Text/Markdown** - Plain text documents

**Features:**
- Automatic file type detection
- Metadata extraction
- Table structure preservation
- LLM-powered financial data extraction
- Document versioning and tracking

**Usage Example:**
```python
from ingestion import DocumentProcessor

processor = DocumentProcessor()

# Upload and process a document
with open('financial_model.xlsx', 'rb') as f:
    doc = processor.process_upload(f.read(), 'financial_model.xlsx')

print(f"Extracted {len(doc.tables)} tables")
print(f"Content length: {len(doc.content)} chars")

# Extract structured financial data using LLM
financial_data = processor.extract_financial_data(doc)
```

### ✅ LLM Integration (`utils/llm_client.py`)
**DeepSeek LLM** integration for reasoning and analysis:
- MD&A analysis and insights extraction
- Legal clause extraction and risk assessment
- Financial anomaly explanation
- Peer company rationale generation
- Investment Committee memo writing
- Red flags and due diligence summaries
- Task planning and execution
- Knowledge graph summaries

**Usage Example:**
```python
from utils import LLMClient

llm = LLMClient()

# Analyze MD&A section
analysis = llm.analyze_mda(mda_text)

# Extract legal clauses
clauses = llm.extract_clauses(
    contract_text,
    clause_types=['change-of-control', 'indemnity', 'termination']
)

# Generate IC memo section
memo = llm.write_ic_memo_section(
    section='Executive Summary',
    data=financial_data,
    citations=sources
)
```

### ✅ Data Schemas (`config/schemas.py`)
**Pydantic Models** for type safety and validation:
- `CompanyMaster` - Company dimension data
- `FinancialFact` - Financial statement facts
- `MarketData` - Market data time series
- `Transaction` - M&A transaction records
- `PeerSet` - Peer company relationships
- `Filing` - SEC filing metadata
- `RiskCard` - Due diligence risk assessments
- `ValuationScenario` - Valuation model outputs
- `Clause` - Legal clause records
- `ModelLineage` - Data lineage tracking
- `CogneeNode` / `CogneeEdge` - Knowledge graph elements

### ✅ Configuration Management (`config/settings.py`)
**Environment-based configuration** using pydantic-settings:
- API credentials
- Database connections
- Storage paths
- LLM settings
- Rate limiting
- Security keys

## Running the Platform

### Demo Mode
Test all integrations:
```bash
python main.py --demo --symbol AAPL
```

This will:
1. Fetch company data from FMP API
2. Download latest 10-K from SEC EDGAR
3. Analyze filings with DeepSeek LLM
4. Display real-time market data

### Basic Usage
```bash
python main.py
```

## Project Structure
```
fmna/
├── agents/              # Agent implementations (future)
├── config/              # Configuration and schemas
│   ├── __init__.py
│   ├── schemas.py       # Pydantic data models
│   └── settings.py      # Environment settings
├── data/                # Data storage
│   ├── raw/             # Raw API responses
│   ├── processed/       # Normalized data
│   ├── models/          # Financial models
│   └── uploads/         # User uploaded documents
├── engines/             # Modeling engines (future)
├── ingestion/           # Data ingestion modules
│   ├── __init__.py
│   ├── fmp_client.py    # FMP API client
│   ├── sec_client.py    # SEC EDGAR client
│   └── document_processor.py  # Document upload handler
├── outputs/             # Generated reports
├── storage/             # Database layer (future)
├── tests/               # Test suite
├── utils/               # Utility functions
│   ├── __init__.py
│   └── llm_client.py    # DeepSeek LLM client
├── .env.example         # Environment template
├── .gitignore           # Git ignore rules
├── main.py              # Main entry point
├── README.md            # Project overview
├── requirements.txt     # Python dependencies
└── SETUP_GUIDE.md       # This file
```

## Next Steps

### Phase 2: Agent Orchestration (LangGraph)
- [ ] Create LangGraph orchestrator
- [ ] Implement ingestion agent
- [ ] Implement normalization agent
- [ ] Implement modeling agent
- [ ] Implement DD agents suite

### Phase 3: Modeling Engines
- [ ] 3-statement financial model
- [ ] DCF valuation engine
- [ ] Comparable company analysis (CCA)
- [ ] Precedent transactions
- [ ] LBO modeling
- [ ] Accretion/dilution analysis

### Phase 4: Cognee Knowledge Graph
- [ ] Set up Cognee integration
- [ ] Define graph schema
- [ ] Implement memory storage
- [ ] Build relationship mapping
- [ ] Enable semantic search

### Phase 5: Advanced Features
- [ ] Distress analysis (Altman Z, O-score)
- [ ] Hypergrowth metrics (SaaS cohorts, NRR)
- [ ] Excel model generator
- [ ] PDF report generator
- [ ] Modern web frontend (React/Next.js)

## Troubleshooting

### Missing API Keys
If you see errors about missing API keys:
1. Check your `.env` file exists
2. Verify all required keys are set
3. Restart the application

### Rate Limiting
- FMP: 300 requests/minute
- SEC: 10 requests/second
- Clients handle this automatically with sleep/retry logic

### Document Processing Issues
Ensure required libraries are installed:
```bash
pip install PyPDF2 pdfminer.six python-pptx python-docx openpyxl
```

## Support
For issues or questions, check:
- Project README.md
- API documentation links in client files
- Log files in `logs/` directory

## Security Notes
- Never commit `.env` file to version control
- Keep API keys secure
- Use strong passwords for database connections
- Rotate secrets regularly
- Enable 2FA on API provider accounts
