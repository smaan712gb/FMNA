# Complete Data Source Mapping

## API Requirements

### ✅ FREE APIs (No Paid Key Required)
- **SEC EDGAR API**: 100% FREE
  - Only requires User-Agent with email
  - Rate limit: 10 requests/second
  - Provides: 10-K, 10-Q, 8-K, MD&A, footnotes, risk factors

### 💰 Paid API (Key Required)
- **FMP API**: Requires API key (you have: `vcS4GLjpRr6YPgpYrwzM6BwZJHAcl3M0`)
  - Your plan includes: financials, peers, market data
  - Rate limit: 300 requests/minute

---

## Data Source Mapping by Engine

### 1. 3-Statement Model (`engines/three_statement_model.py`)

**Data Needed**:
- Revenue trees & drivers
- Margin ladders
- SBC (Stock-Based Compensation) policy
- Lease normalization
- Interest/tax schedules

**Data Sources**:
| Data Element | Source | API | Method |
|--------------|--------|-----|--------|
| Historical Revenue | FMP | Paid | `get_income_statement()` |
| Revenue by Segment | SEC 10-K | **FREE** | Item 8 footnotes |
| COGS/Operating Expenses | FMP | Paid | `get_income_statement()` |
| SBC Details | SEC 10-K | **FREE** | Item 8 Note on compensation |
| Lease Obligations | SEC 10-K | **FREE** | Item 8 Note on leases |
| Tax Rate/Schedules | FMP + SEC | Both | FMP ratios + 10-K footnotes |
| Interest Schedule | FMP + SEC | Both | Debt structure from both |

**Status**: ✅ **Partially Integrated**
- FMP data: ✅ Available via orchestrator
- SEC footnotes: ⚠️ Need to add to orchestrator

---

### 2. DCF Model (`engines/dcf_engine.py`)

**Data Needed**:
- FCFF (Free Cash Flow to Firm)
- WACC components (peer beta, risk-free rate, ERP)
- Terminal Value (Gordon Growth, Exit Multiple)
- Monte Carlo inputs (ERP/beta distributions)

**Data Sources**:
| Data Element | Source | API | Method |
|--------------|--------|-----|--------|
| Historical Cash Flow | FMP | Paid | `get_cash_flow_statement()` |
| Revenue/EBITDA Projections | SEC 10-K | **FREE** | MD&A section |
| Beta (Company) | FMP | Paid | `get_key_metrics()` |
| Beta (Peers) | FMP | Paid | `get_peers_with_complete_data()` |
| Risk-Free Rate | External/Fed | **FREE** | Treasury yield (can hardcode or fetch) |
| Market Risk Premium | Research/Assumption | N/A | Typically 5-7% (industry standard) |
| Debt/Equity Structure | FMP | Paid | `get_balance_sheet()` |
| Cost of Debt | FMP + SEC | Both | Interest from statements |

**Status**: ✅ **Fully Integrated via Orchestrator**
- All FMP data available
- Can add SEC MD&A for management guidance

---

### 3. CCA Model (`engines/cca_engine.py`)

**Data Needed**:
- Peer selection criteria
- Winsorized multiples
- Regression-adjusted multiples (growth/ROIC controls)

**Data Sources**:
| Data Element | Source | API | Method |
|--------------|--------|-----|--------|
| Peer List | FMP | Paid | `get_stock_peers()` ✅ **FIXED** |
| Peer Financials | FMP | Paid | `get_peers_with_complete_data()` |
| Peer Growth Rates | FMP | Paid | Key metrics |
| Peer ROIC | FMP | Paid | Financial ratios |
| Target Multiples | Calculated | N/A | From FMP data |

**Status**: ✅ **100% Integrated via Orchestrator**
- Peers: ✅ Fixed with bulk caching
- All peer data validated

---

### 4. Precedent Transactions (`engines/merger_model.py`)

**Data Needed**:
- Control premium statistics
- Normalize for cycle/structure

**Data Sources**:
| Data Element | Source | API | Method |
|--------------|--------|-----|--------|
| Transaction Details | SEC 8-K/DEFM14A | **FREE** | Merger proxies |
| Deal Multiples | FMP Historical | Paid | (May not have all) |
| Control Premiums | SEC Filings | **FREE** | Proxy premium disclosures |
| Synergy Estimates | SEC DEFM14A | **FREE** | Management projections |

**Status**: ⚠️ **Needs SEC Integration**
- Engine exists ✅
- Need to add SEC 8-K/proxy fetching

---

### 5. LBO Model (`engines/lbo_engine.py`)

**Data Needed**:
- Sources/Uses
- Tranche stack (debt structure)
- PIK toggles
- Covenants
- Exit bridge
- IRR/MoIC calculations

**Data Sources**:
| Data Element | Source | API | Method |
|--------------|--------|-----|--------|
| Current Financials | FMP | Paid | All statements |
| Debt Structure | FMP + SEC | Both | Balance sheet + footnotes |
| Covenant Details | SEC 10-K | **FREE** | Note on debt |
| Interest Rates | FMP + Assumptions | Mix | Current rates + market |
| Exit Multiples | FMP Peers | Paid | Peer trading multiples |
| Management Guidance | SEC 10-K | **FREE** | MD&A projections |

**Status**: ✅ **Engine Ready**
- FMP data: ✅ Available
- SEC covenants: ⚠️ Can add

---

### 6. Accretion/Dilution (`engines/merger_model.py`)

**Data Needed**:
- Purchase accounting (PPA)
- Synergies net of costs
- Buyback scenarios
- FX impacts

**Data Sources**:
| Data Element | Source | API | Method |
|--------------|--------|-----|--------|
| Acquirer Financials | FMP | Paid | All statements |
| Target Financials | FMP | Paid | All statements |
| PPA Assumptions | SEC 8-K | **FREE** | Post-merger filings |
| Synergy Estimates | SEC DEFM14A | **FREE** | Merger proxy |
| Transaction Structure | SEC Filings | **FREE** | Merger documents |
| FX Rates | External/Fed | **FREE** | Currency rates |

**Status**: ✅ **Engine Ready**
- Basic merger model exists
- Can enhance with SEC filings

---

### 7. Distress Analysis (`engines/growth_scenarios.py`)

**Data Needed**:
- Altman Z-Score
- Ohlson O-Score
- Coverage ratios
- Liquidity runway
- Bankruptcy waterfall

**Data Sources**:
| Data Element | Source | API | Method |
|--------------|--------|-----|--------|
| Financial Ratios | FMP | Paid | `get_financial_ratios()` |
| Retained Earnings | FMP | Paid | Balance sheet |
| Market Value | FMP | Paid | Current quote |
| Working Capital | FMP | Paid | Balance sheet |
| Debt Structure | FMP + SEC | Both | Statements + footnotes |
| Covenant Status | SEC 10-K | **FREE** | Debt footnotes |

**Status**: ✅ **Implemented**
- Altman Z-Score: ✅ In growth_scenarios.py
- Uses FMP data

---

### 8. Hypergrowth/SaaS (`engines/growth_scenarios.py`)

**Data Needed**:
- Cohort analysis (NRR/GRR)
- CAC → LTV
- Payback periods
- Pricing ladders
- Capacity-constrained ramps

**Data Sources**:
| Data Element | Source | API | Method |
|--------------|--------|-----|--------|
| Revenue by Cohort | SEC 10-K | **FREE** | MD&A + footnotes |
| Customer Metrics | SEC 10-K | **FREE** | MD&A disclosures |
| CAC (Customer Acq Cost) | SEC 10-K/10-Q | **FREE** | S&M expense analysis |
| Churn Rates | SEC Filings | **FREE** | MD&A (if disclosed) |
| ARR/MRR | SEC Filings | **FREE** | MD&A (SaaS companies) |
| Unit Economics | Calculated | N/A | From FMP + SEC data |

**Status**: ⚠️ **Needs SEC MD&A Integration**
- Engine has SaaS metrics structure
- Need to parse MD&A for cohort data

---

## SEC EDGAR Integration Status

### ✅ What SEC Client Can Do (FREE)
```python
class SECClient:
    ✅ get_company_cik(ticker)              # Get CIK number
    ✅ search_filings(cik, filing_type)     # Find filings
    ✅ download_filing(cik, accession)      # Download documents
    ✅ extract_section_item_7(text)         # MD&A
    ✅ extract_section_item_7a(text)        # Market Risk
    ✅ extract_section_item_8(text)         # Financial Statements
    ✅ extract_risk_factors(text)           # Item 1A
    ✅ get_latest_filing(ticker, type)      # Complete filing with sections
    ✅ bulk_download_filings(ticker)        # Multiple filings
```

### ⚠️ What's Not Yet in Orchestrator
- MD&A for management projections
- Footnotes for detailed accounting policies
- Risk factors for DD agents
- Proxy statements for governance

---

## Implementation Priority

### ✅ COMPLETE - FMP Integration
- [x] Financial statements (IS, BS, CF)
- [x] Key metrics and ratios
- [x] Peer data (with bulk caching)
- [x] Market data (prices, shares, market cap)
- [x] Enterprise value

### 🔧 TO ADD - SEC Integration in Orchestrator

**High Priority** (Needed for completeness):
1. **MD&A Section** - Management projections, guidance
   - Used by: DCF, LBO, Growth Scenarios
   - Fetch from: 10-K Item 7
   
2. **Financial Statement Footnotes** - Detailed policies
   - Used by: 3-Statement, DD Agents
   - Fetch from: 10-K Item 8
   
3. **Risk Factors** - Item 1A
   - Used by: DD Agents (QoE, Commercial, Risk)
   - Fetch from: 10-K Item 1A

**Medium Priority** (Nice to have):
4. **Proxy Statements** - Governance, compensation
   - Used by: ESG Agent, DD Agents
   - Fetch from: DEF 14A
   
5. **8-K Filings** - Material events
   - Used by: DD Agents, Event analysis
   - Fetch from: 8-K

---

## Data Flow Architecture

### Current (Post-Implementation)
```
┌─────────────────────────────────────────────┐
│  ComprehensiveOrchestrator                  │
└───────┬─────────────────────────────────────┘
        │
        ├─→ FMP API (Paid Key) ✅
        │   ├─→ Financial Statements
        │   ├─→ Peers (bulk cached)
        │   ├─→ Market Data
        │   └─→ Metrics/Ratios
        │
        └─→ SEC EDGAR (FREE) ⚠️ PARTIAL
            ├─→ Can fetch filings ✅
            ├─→ Can extract sections ✅
            └─→ NOT integrated in orchestrator yet ⚠️
```

### Target (Full Integration)
```
┌─────────────────────────────────────────────┐
│  ComprehensiveOrchestrator                  │
└───────┬─────────────────────────────────────┘
        │
        ├─→ FMP API (Paid) ✅
        │   └─→ Quantitative Data
        │
        └─→ SEC EDGAR (FREE) ✅
            ├─→ MD&A (management narrative)
            ├─→ Footnotes (accounting details)
            ├─→ Risk Factors
            └─→ Proxies (governance)
```

---

## Summary

### API Keys Needed:
- ✅ **FMP**: You have `vcS4GLjpRr6YPgpYrwzM6BwZJHAcl3M0`
- ✅ **SEC**: **NO KEY NEEDED** - Completely FREE

### Current Status:
- ✅ **FMP Integration**: 100% Complete
- ✅ **Peers Fix**: Complete with bulk caching
- ✅ **Orchestrator**: Working with FMP data
- ⚠️ **SEC Integration**: Client ready, not in orchestrator yet

### What Each Engine Gets:

| Engine | FMP Data | SEC Data Needed | Status |
|--------|----------|-----------------|--------|
| 3-Statement | ✅ Financials | Footnotes, SBC details | 🔧 Add SEC |
| DCF | ✅ Cash flows, Beta | MD&A projections | 🔧 Add SEC |
| CCA | ✅ Peers, Multiples | None (optional) | ✅ Complete |
| Precedent | ⚠️ Limited | 8-K, DEFM14A | 🔧 Add SEC |
| LBO | ✅ Financials | Covenants, guidance | 🔧 Add SEC |
| Accretion/Dilution | ✅ Financials | PPA from 8-K | 🔧 Add SEC |
| Distress | ✅ Ratios | Covenant details | 🔧 Add SEC |
| Hypergrowth/SaaS | ✅ Financials | MD&A cohorts, metrics | 🔧 Add SEC |

### Next Step:
1. Update orchestrator to fetch SEC filings (FREE)
2. Pass MD&A to DCF/LBO engines
3. Pass footnotes to 3-Statement/DD agents
4. Pass risk factors to DD agents

---

**Key Takeaway**: 
- SEC EDGAR API is **COMPLETELY FREE** ✅
- No paid API key needed for SEC
- Your FMP key covers quantitative data
- SEC provides qualitative/narrative data
- Platform designed to use BOTH sources

**Cost**: $0 for SEC + your existing FMP subscription
