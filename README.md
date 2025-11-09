# FMNA - Financial M&A Analytics Platform

A production-grade, open-source M&A platform that combines:
- **Cognee** as memory/graph backbone
- **FMP API** for fundamentals/comps/transactions
- **SEC EDGAR** for MD&A + footnotes mining
- **DeepSeek-V3** for LLM reasoning
- Scales from hypergrowth → distress/bankruptcy scenarios

## Architecture

### Core Pillars
1. **Memory & Knowledge Graph**: Cognee (vector + graph memory)
2. **Market & Fundamentals**: Financial Modeling Prep (FMP) API
3. **Filings & MD&A**: SEC EDGAR/SEC-API
4. **LLM**: DeepSeek-V3 for reasoning and analysis
5. **Operating System Ambition**: Palantir-like data integration

### Agent Suite
- **Ingestion Agent**: FMP + EDGAR pulls
- **Normalization Agent**: COA mapping, currency, calendarization
- **Modeling Agent**: 3-statement, DCF, CCA, Precedent, LBO
- **DD Agents**: Financial QoE, Commercial, Legal/Tax, HR, Tech, ESG
- **Comps/Precedents Agent**: Peer screening + transaction normalization
- **Distress/Hype Agent**: Bankruptcy vs hypergrowth scenarios
- **Assurance Agent**: Footnote tracing, tie-outs, citations
- **Exporter Agent**: Excel models, IC memos, reports

## Setup

### Environment Setup
```bash
# Create conda environment
conda create -n fmna python=3.11 -y
conda activate fmna

# Install dependencies
pip install -r requirements.txt
```

### Configuration
Create `.env` file with:
```
FMP_API_KEY=your_fmp_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
SEC_API_KEY=your_sec_api_key (optional)
```

## Project Structure

```
fmna/
├── agents/           # Agent implementations
├── config/           # Configuration files
├── data/            # Data storage
│   ├── raw/         # Raw data from APIs
│   ├── processed/   # Normalized data
│   └── models/      # Financial models
├── engines/         # Modeling engines
├── ingestion/       # Data ingestion modules
├── storage/         # Database and graph storage
├── outputs/         # Generated reports and models
├── tests/           # Test suite
└── utils/           # Utility functions
```

## License

MIT

## Roadmap

Phase 1: Core ingestion + modeling engines
Phase 2: Agent orchestration + Cognee integration
Phase 3: Advanced DD + distress scenarios
Phase 4: Palantir-class lineage + ontology
