# Growth Scenarios Engine - Complete Features

**Status**: ✅ EXISTS - Part of Engine #6 (Growth Scenarios)
**Default**: ⏸️ DISABLED (for performance)

## What's Included in Growth Scenarios Engine

The Growth Scenarios engine (`engines/growth_scenarios.py`) provides TWO major capabilities in ONE engine:

### 1. Growth Stage Modeling
Models company trajectory across lifecycle stages:
- **Hypergrowth** (>20% growth)
- **Growth** (10-20% growth)  
- **Steady** (5-10% growth)
- **Mature** (0-5% growth)
- **Decline** (0-5% growth)
- **DISTRESS** (Negative growth, covenant stress)

### 2. Distress & Bankruptcy Analysis ✅ 

**Included Features**:
- ✅ **Altman Z-Score**: Bankruptcy prediction model
  - Z > 2.99: Safe zone (5% bankruptcy risk)
  - 1.81 < Z < 2.99: Gray zone (30% bankruptcy risk)
  - Z < 1.81: Distress zone (80% bankruptcy risk)

- ✅ **Ohlson O-Score**: Bankruptcy probability
  - O > 0.5: High bankruptcy risk
  - Used for bankruptcy probability estimation

- ✅ **DistressMetrics** dataclass:
  ```python
  @dataclass
  class DistressMetrics:
      altman_z_score: float
      ohlson_o_score: float
      interest_coverage: float
      current_ratio: float
      quick_ratio: float
      cash_burn_months: float
      debt_to_equity: float
      debt_to_ebitda: float
  ```

- ✅ **Bankruptcy Probability**: Calculated from Z-Score
- ✅ **Coverage Ratios**: Interest coverage, debt service coverage
- ✅ **Liquidity Metrics**: Cash runway, burn rate
- ✅ **Covenant Stress**: Debt covenant compliance

## How to Enable

### Option 1: Frontend (Recommended)
1. Open frontend: `python frontend_app.py`
2. Check the **"Growth Scenarios"** checkbox
3. Run analysis
4. You'll get all 6 engines INCLUDING distress/bankruptcy analysis

### Option 2: Programmatic
```python
from orchestration.comprehensive_orchestrator import ComprehensiveOrchestrator
import asyncio

async def run_with_distress_analysis():
    orch = ComprehensiveOrchestrator()
    result = await orch.run_comprehensive_analysis(
        symbol="NVDA",
        run_growth_scenarios=True,  # ← This enables distress analysis too
        run_full_dd=True
    )
    
    # Check results
    if result.valuation.growth_scenarios:
        gs = result.valuation.growth_scenarios
        if gs.distress_metrics:
            print(f"Altman Z-Score: {gs.distress_metrics.altman_z_score:.2f}")
            print(f"Bankruptcy Probability: {gs.bankruptcy_probability:.1%}")
            print(f"Cash Burn Months: {gs.distress_metrics.cash_burn_months:.1f}")

asyncio.run(run_with_distress_analysis())
```

## Why It's Disabled by Default

Performance optimization:
- Growth Scenarios + Distress Analysis is computationally intensive
- Requires complex financial statement projections
- Most analyses don't need bankruptcy/distress scenarios
- Can be enabled when needed for distressed situations

## Engine Count Clarification

**You have 6 engines total**, not 7:

1. **DCF** - Discounted Cash Flow
2. **CCA** - Comparable Companies Analysis
3. **LBO** - Leveraged Buyout
4. **Merger** - M&A Accretion/Dilution
5. **3FS** - Three-Statement Integration
6. **Growth Scenarios** - Includes:
   - Growth stage modeling
   - Distress/bankruptcy analysis
   - Altman Z-Score
   - Ohlson O-Score
   - Coverage ratios
   - Liquidity runway
   - Bankruptcy waterfalls

## Current Status

When you run analysis with default settings:
- **5 engines active**: DCF, CCA, LBO, Merger, 3FS
- **1 engine disabled**: Growth Scenarios (which includes distress analysis)

When you enable "Growth Scenarios" checkbox:
- **6 engines active**: All 5 + Growth Scenarios
- **Distress analysis included**: Altman Z, O-Score, bankruptcy probability, coverage ratios, cash runway

## Conclusion

The Distress/Bankruptcy analysis features you mentioned are NOT missing - they're part of the Growth Scenarios engine. Simply enable the Growth Scenarios checkbox in the frontend, and you'll get all 6 engines including the full distress analysis suite.
