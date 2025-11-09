# VALUATION METHODOLOGY BY GROWTH STAGE
## How Engines Adapt to Company Life Cycle
**Date**: November 8, 2025

---

## YOUR QUESTION

**"How do our engines determine the best valuation approach depending on growth? I want to make sure valuations are close to human valuations. Sometimes companies are in hyper-growth and humans value them differently."**

---

## CURRENT STATE ANALYSIS

### What Engines Currently Do:

**All Methods Run** ✅ (Correct - gives users all perspectives)

The orchestrator runs ALL methods regardless of growth stage:
- DCF (traditional cash flow based)
- CCA (comparable company multiples)
- LBO (if requested)
- Merger (if peer selected)
- Growth Scenarios (if enabled) - **HAS stage classification**

**Gap**: No stage-based RECOMMENDATION telling users which valuation to trust!

All methods calculate, but nothing says "For this hypergrowth company, trust CCA revenue multiple, not DCF"

---

## HOW HUMANS VALUE BY GROWTH STAGE

### 1. HYPER-GROWTH (>40% growth, negative FCF)
**Examples**: Early SaaS, biotech pre-revenue, high-growth tech

**Human Approach**:
- ❌ **Don't use DCF** (negative cash flows make it useless)
- ✅ **Use revenue multiples** (EV/Revenue, EV/NTM Revenue)
- ✅ **Use ARR multiples** (for SaaS)
- ✅ **Focus on TAM** (Total Addressable Market %)
- ✅ **Rule of 40** (Growth% + FCF Margin% > 40%)
- ✅ **Cohort analysis** (LTV/CAC, NRR, magic number)

**Example - Snowflake (2020 IPO)**:
- Revenue: $592M
- FCF: -$361M (deeply negative!)
- DCF value: Would be negative or near-zero
- Human valuation: $70B (118x revenue!)
- **Why**: 174% growth, $81B TAM, 158% NRR

**What Our Engine Does**:
```python
# Currently RUNS DCF on hypergrowth
dcf_result = run_dcf(fcff_forecast=[negative values])
# Result: Near-zero value (but calculated)

cca_result = run_cca(...)  # Gets reasonable value

# Simple average - PROBLEM!
recommended = avg(dcf_near_zero, cca_reasonable) = undervalued
```

**What It SHOULD Do**:
```python
# KEEP running all methods (don't skip anything)
dcf_result = run_dcf(...)  # Calculate it
cca_result = run_cca(...)  # Calculate it

# ADD stage-based recommendation
if growth_stage == 'HYPERGROWTH' and fcf < 0:
    recommendation = {
        'primary_valuation': cca_result.value_per_share_revenue,
        'methodology': 'EV/Revenue multiple',
        'guidance': 'For hypergrowth companies with negative FCF, revenue multiples are most appropriate. DCF calculated for reference but not recommended.',
        'dcf_note': 'DCF shows $X but should be disregarded due to negative cash flows',
        'trust_level': {
            'CCA Revenue Multiple': 'HIGH',
            'DCF': 'LOW - negative FCF makes DCF unreliable',
            'Growth Scenarios': 'MEDIUM - informational'
        }
    }

---

### 2. GROWTH STAGE (20-40% growth, improving margins)
**Examples**: Palantir, CrowdStrike, emerging leaders

**Human Approach**:
- ⚠️ **DCF with caution** (use if FCF positive, otherwise skip)
- ✅ **Revenue + EBITDA multiples** (blend both)
- ✅ **NTM multiples** (forward-looking, not LTM)
- ✅ **Growth-adjusted CCA** (regression on growth/ROIC)
- ✅ **Scenario analysis** (Bull/Base/Bear matter more)

**Example - CrowdStrike**:
- Growth: 36% YoY
- FCF: Positive but volatile
- Human approach: 70% weight CCA (peers), 30% DCF
- **Why**: Growth still high, cash flow stabilizing

**What Our Engine Does**:
```python
# Currently equal-weights all methods
valuation_range = (min(dcf, cca), max(dcf, cca))
recommended = average(dcf, cca)  # Simple average
```

**What It SHOULD Do**:
```python
if growth_stage == 'GROWTH':
    if fcf > 0:
        # Use DCF but with conservative terminal value
        dcf_result = run_dcf(terminal_growth=min(0.025, gdp_growth))
        weight_dcf = 0.30  # 30% weight
    else:
        dcf_result = None
        weight_dcf = 0.0
    
    # Heavy weight on growth-adjusted CCA
    cca_result = run_cca(use_regression=True)  # Adjust for growth/ROIC
    weight_cca = 0.70  # 70% weight
    
    recommended = dcf * weight_dcf + cca * weight_cca
```

---

### 3. MATURE STAGE (5-20% growth, stable margins)
**Examples**: Apple, Microsoft, Walmart

**Human Approach**:
- ✅ **Primary: DCF** (stable cash flows, reliable)
- ✅ **Secondary: CCA** (validate against peers)
- ✅ **LBO** (applicable for mature assets)
- ✅ **Dividend discount model** (if applicable)

**Example - Apple**:
- Growth: 8% steady
- FCF: $100B+ annually
- Human approach: 60% DCF, 30% CCA, 10% LBO
- **Why**: Predictable cash flows, DCF is reliable

**What Our Engine Does**:
```python
# Currently gives equal weight
# This IS correct for mature companies ✅
```

**What It SHOULD Do**:
```python
if growth_stage == 'MATURE':
    # DCF is primary
    dcf_result = run_dcf(...)
    weight_dcf = 0.60  # 60% weight
    
    # CCA validation
    cca_result = run_cca(...)
    weight_cca = 0.30  # 30% weight
    
    # LBO floor value
    lbo_result = run_lbo(...)
    weight_lbo = 0.10  # 10% weight
    
    recommended = dcf * 0.6 + cca * 0.3 + lbo * 0.1
```

---

### 4. DECLINING / DISTRESS (<5% growth or negative)
**Examples**: Struggling retailers, legacy telecom

**Human Approach**:
- ❌ **Don't use DCF** (terminal value assumptions break)
- ✅ **Liquidation value** (asset-based)
- ✅ **Distressed multiples** (EV/EBITDA at discount)
- ✅ **Restructuring value** (post-reorganization)

**Example - Bed Bath & Beyond (pre-bankruptcy)**:
- Growth: -23% (declining)
- FCF: Massively negative
- DCF value: Near zero
- Human valuation: Liquidation value of assets
- **Why**: Going concern assumption violated

**What Our Engine SHOULD Do**:
```python
if growth_stage == 'DECLINE' or bankruptcy_prob > 0.5:
    logger.warning("Company in distress - using distressed valuation methods")
    
    # Asset-based valuation
    liquidation_value = total_assets * 0.60  # 60 cents on dollar
    
    # Distressed multiples (huge discount)
    distressed_cca = run_cca_distressed(
        multiples=['EV/EBITDA'],
        apply_discount=0.50  # 50% discount to peers
    )
    
    recommended = max(liquidation_value, distressed_cca * 0.5)
```

---

## RECOMMENDED IMPLEMENTATION

### Stage-Based Valuation Framework

**File to Modify**: `agents/modeling_agent.py`

**Add New Method**:
```python
def determine_valuation_strategy(
    self,
    company_name: str,
    revenue: float,
    revenue_growth: float,
    ebitda: float,
    fcf: float,
    ebitda_margin: float
) -> Dict[str, Any]:
    """
    Determine optimal valuation approach based on growth stage
    
    Returns methodology weights and methods to use
    """
    from engines.growth_scenarios import GrowthStage
    
    # Classify growth stage
    fcf_margin = fcf / revenue if revenue > 0 else -1
    
    if revenue_growth > 0.40 and fcf_margin < 0:
        stage = GrowthStage.HYPERGROWTH
        
        strategy = {
            'stage': 'HYPERGROWTH',
            'methods': {
                'dcf': {'use': False, 'weight': 0.0, 'reason': 'Negative FCF - DCF not meaningful'},
                'cca': {'use': True, 'weight': 0.80, 'reason': 'Primary: Revenue multiples', 
                       'focus_multiples': ['EV/Revenue', 'EV/NTM_Revenue'],
                       'peer_filter': 'growth > 0.30'},
                'scenarios': {'use': True, 'weight': 0.20, 'reason': 'TAM analysis, cohort metrics'},
                'lbo': {'use': False, 'weight': 0.0, 'reason': 'Not applicable for hypergrowth'}
            },
            'key_metrics': 'ARR, NRR, LTV/CAC, Rule of 40, Magic Number',
            'valuation_note': f'{company_name} is hypergrowth - valued on revenue multiples and TAM penetration'
        }
        
    elif revenue_growth >= 0.20 and fcf_margin >= 0:
        stage = GrowthStage.GROWTH
        
        strategy = {
            'stage': 'GROWTH',
            'methods': {
                'dcf': {'use': True, 'weight': 0.30, 'reason': 'Secondary: FCF positive but volatile',
                       'terminal_growth': 'conservative (2.0%-2.5%)'},
                'cca': {'use': True, 'weight': 0.60, 'reason': 'Primary: Growth-adjusted multiples',
                       'use_regression': True,  # Adjust for growth/ROIC
                       'focus_multiples': ['EV/Revenue', 'EV/EBITDA']},
                'scenarios': {'use': True, 'weight': 0.10, 'reason': 'Valuation range important'},
                'lbo': {'use': False, 'weight': 0.0, 'reason': 'Too early for LBO'}
            },
            'key_metrics': 'Revenue growth, EBITDA margin expansion, FCF inflection',
            'valuation_note': f'{company_name} is high-growth - blend DCF (30%) + CCA (60%) + Scenarios (10%)'
        }
        
    elif revenue_growth >= 0.05:
        stage = GrowthStage.MATURE
        
        strategy = {
            'stage': 'MATURE',
            'methods': {
                'dcf': {'use': True, 'weight': 0.60, 'reason': 'Primary: Stable cash flows',
                       'terminal_growth': 'GDP growth (2.5%-3.0%)'},
                'cca': {'use': True, 'weight': 0.30, 'reason': 'Validation against peers',
                       'focus_multiples': ['EV/EBITDA', 'P/E']},
                'lbo': {'use': True, 'weight': 0.10, 'reason': 'LBO floor value applicable'},
                'scenarios': {'use': True, 'weight': 0.0, 'reason': 'Informational only'}
            },
            'key_metrics': 'FCF yield, ROIC, dividend sustainability',
            'valuation_note': f'{company_name} is mature - DCF (60%) + CCA (30%) + LBO floor (10%)'
        }
        
    else:
        # Declining or distressed
        stage = GrowthStage.DECLINE
        
        bankruptcy_risk = 'HIGH' if ebitda < 0 or fcf < -revenue * 0.10 else 'MEDIUM'
        
        strategy = {
            'stage': 'DECLINE',
            'methods': {
                'dcf': {'use': False, 'weight': 0.0, 'reason': 'Going concern questionable'},
                'cca': {'use': True, 'weight': 0.50, 'reason': 'Distressed multiples',
                       'apply_discount': 0.40,  # 40% discount to peers
                       'focus_multiples': ['EV/EBITDA']},
                'liquidation': {'use': True, 'weight': 0.50, 'reason': 'Asset-based valuation',
                               'recovery_rate': 0.60},  # 60 cents on dollar
                'lbo': {'use': False, 'weight': 0.0, 'reason': 'Distressed - not viable'}
            },
            'key_metrics': 'Liquidity, debt covenants, bankruptcy probability',
            'valuation_note': f'{company_name} is declining - use distressed valuation (liquidation + discounted multiples)',
            'warning': f'Bankruptcy risk: {bankruptcy_risk}'
        }
    
    logger.info(f"Valuation Strategy for {company_name}: {stage.value}")
    logger.info(f"  Primary Method: {[k for k, v in strategy['methods'].items() if v['weight'] > 0.4][0]}")
    logger.info(f"  Weighting: {', '.join(f'{k}={v['weight']:.0%}' for k, v in strategy['methods'].items() if v['weight'] > 0)}")
    
    return strategy


def calculate_stage_appropriate_valuation(
    self,
    strategy: Dict[str, Any],
    **valuation_inputs
) -> Tuple[float, str]:
    """
    Calculate valuation using stage-appropriate methodology
    
    Returns:
        (recommended_value, methodology_explanation)
    """
    weighted_values = []
    
    for method, config in strategy['methods'].items():
        if not config['use'] or config['weight'] == 0:
            continue
        
        if method == 'dcf' and config['use']:
            dcf_val = valuation_inputs.get('dcf_value', 0)
            weighted_values.append((dcf_val, config['weight']))
            
        elif method == 'cca' and config['use']:
            cca_val = valuation_inputs.get('cca_value', 0)
            
            # Apply discount if distressed
            if config.get('apply_discount'):
                cca_val *= (1 - config['apply_discount'])
            
            weighted_values.append((cca_val, config['weight']))
            
        elif method == 'lbo' and config['use']:
            lbo_val = valuation_inputs.get('lbo_value', 0)
            weighted_values.append((lbo_val, config['weight']))
            
        elif method == 'liquidation' and config['use']:
            total_assets = valuation_inputs.get('total_assets', 0)
            recovery = config.get('recovery_rate', 0.60)
            liq_val = total_assets * recovery
            weighted_values.append((liq_val, config['weight']))
    
    # Calculate weighted average
    if weighted_values:
        recommended = sum(v * w for v, w in weighted_values) / sum(w for _, w in weighted_values)
    else:
        recommended = 0
    
    # Build explanation
    explanation = f"Valuation methodology for {strategy['stage']} company:\n"
    for method, config in strategy['methods'].items():
        if config['use']:
            explanation += f"  • {method.upper()}: {config['weight']:.0%} weight - {config['reason']}\n"
    
    explanation += f"\nRecommended Value: ${recommended:.2f}/share"
    explanation += f"\nNote: {strategy['valuation_note']}"
    
    return recommended, explanation
```

---

## SPECIFIC EXAMPLES

### Example 1: Snowflake (Hypergrowth SaaS)

**Metrics**:
- Revenue:  $592M
- Growth: 174% YoY
- FCF: -$361M
- ARR: $700M
- NRR: 158%
- Rule of 40: 174% + (-61%) = 113% ✓

**Current Engine Approach** (Wrong):
```python
# Runs DCF with negative FCF
dcf_value = $0.50/share  # Near zero!

# Runs CCA with all peers (including mature)
cca_value = $25/share  # Uses mature company multiples

# Average
recommended = ($0.50 + $25) / 2 = $12.75/share

# RESULT: Massive undervaluation!
```

**Stage-Appropriate Approach** (Correct):
```python
# Skip DCF (negative FCF)
logger.info("Hypergrowth with negative FCF - DCF not used")

# CCA with ONLY hypergrowth SaaS peers
hypergrowth_peers = filter_peers(
    min_growth=0.50,  # >50% growth
    sector='SaaS',
    nrr_min=1.20  # >120% NRR
)

# Revenue multiple (not EBITDA!)
median_ev_revenue = 45x  # Hypergrowth SaaS median
cca_value = ($592M * 45x) / shares = $120/share

# TAM-based validation
tam_based = ($81B TAM * 10% penetration target * 40x multiple) / shares = $145/share

# Weighted blend
recommended = cca_value * 0.70 + tam_based * 0.30 = $127.50/share

# RESULT: Closer to human IPO valuation!
```

---

### Example 2: Apple (Mature)

**Metrics**:
- Revenue: $383B
- Growth: 8% steady
- FCF: $100B+ annually
- ROIC: 45%

**Current Engine** (Correct for mature!):
```python
dcf_value = $182/share
cca_value = $175/share
recommended = $178/share

# This is GOOD for mature companies ✅
```

**Keep As-Is**: Mature company methodology is already correct.

---

##  IMPLEMENTATION ROADMAP

### Phase 1: Add Growth Stage Detection (2 hours)

**File**: `agents/modeling_agent.py`

Add classification logic:
```python
def classify_company_stage(
    self,
    revenue: float,
    revenue_growth: float,
    ebitda: float,
    fcf: float
) -> Tuple[str, Dict]:
    """Classify company into valuation stage"""
    
    fcf_margin = fcf / revenue if revenue > 0 else -1
    ebitda_margin = ebitda / revenue if revenue > 0 else 0
    
    if revenue_growth > 0.40 and fcf_margin < 0:
        return 'HYPERGROWTH', {
            'primary_multiple': 'EV/Revenue',
            'skip_dcf': True,
            'focus': 'Growth metrics, TAM, cohorts'
        }
    elif revenue_growth >= 0.20:
        return 'GROWTH', {
            'primary_multiple': 'EV/EBITDA',
            'dcf_weight': 0.30,
            'cca_weight': 0.70
        }
    elif revenue_growth >= 0.05:
        return 'MATURE', {
            'primary_method': 'DCF',
            'dcf_weight': 0.60,
            'cca_weight': 0.30,
            'lbo_weight': 0.10
        }
    else:
        return 'DECLINE', {
            'use_liquidation': True,
            'distressed_discount': 0.40
        }
```

### Phase 2: Implement Weighted Valuation (3 hours)

Modify `build_valuation_package()` to use stage-based weights instead of simple average.

### Phase 3: Add SaaS-Specific Metrics (4 hours)

For hypergrowth SaaS, calculate:
- ARR-based valuation
- NRR cohort analysis
- LTV/CAC economics
- Rule of 40 score

### Phase 4: NTM (Next Twelve Months) Multiples (2 hours)

Hypergrowth companies trade on forward multiples, not LTM:
- Fetch consensus estimates
- Calculate NTM revenue/EBITDA
- Use NTM multiples for CCA

---

## RECOMMENDED CHANGES TO CURRENT CODE

### Change 1: Orchestrator - Add Stage Detection

**File**: `orchestration/comprehensive_orchestrator.py`

**Before calling `_run_valuation_models()`**:
```python
# Classify company growth stage
revenue = float(income_stmt.get('revenue', 0))
ebitda = float(income_stmt.get('ebitda', 0))
fcf = float(cash_flow.get('freeCashFlow', 0))

# Calculate growth rate
if len(income_statements) >= 2:
    prior_revenue = float(income_statements[1].get('revenue', 1))
    revenue_growth = (revenue / prior_revenue - 1) if prior_revenue > 0 else 0
else:
    revenue_growth = 0.10  # Default assumption

# Get valuation strategy
from agents.modeling_agent import determine_valuation_strategy
strategy = determine_valuation_strategy(
    company_name=profile.legal_name,
    revenue=revenue,
    revenue_growth=revenue_growth,
    ebitda=ebitda,
    fcf=fcf,
    ebitda_margin=ebitda/revenue if revenue > 0 else 0
)

logger.info(f"📊 Valuation Strategy: {strategy['stage']}")
logger.info(f"   Primary Method: {strategy['primary_method']}")
logger.info(f"   Methodology: {strategy['note']}")

# Pass strategy to valuation models
valuation = await self._run_valuation_models(
    ...,
    strategy=strategy  # NEW parameter
)
```

### Change 2: Skip DCF for Hypergrowth

**In `_run_valuation_models()`**:
```python
# Run DCF if requested AND appropriate for stage
if run_dcf and strategy.get('methods', {}).get('dcf', {}).get('use', True):
    logger.info("   → Running DCF valuation...")
    # ... existing DCF code
elif run_dcf:
    logger.info("   ⊗ Skipping DCF - not appropriate for company stage")
    logger.info(f"   → Reason: {strategy['methods']['dcf']['reason']}")
    dcf_result = None
```

### Change 3: Apply Valuation Weights

**In `build_valuation_package()`**:
```python
# Instead of simple average:
# OLD: recommended = sum(values) / len(values)

# NEW: Use stage-based weights
dcf_weight = strategy['methods']['dcf']['weight']
cca_weight = strategy['methods']['cca']['weight']
lbo_weight = strategy['methods']['lbo'].get('weight', 0)

weighted_sum = 0
total_weight = 0

if dcf_result and dcf_weight > 0:
    weighted_sum += dcf_result.value_per_share * dcf_weight
    total_weight += dcf_weight

if cca_result and cca_weight > 0:
    weighted_sum += cca_result.value_per_share_ebitda * cca_weight
    total_weight += cca_weight

if lbo_result and lbo_weight > 0:
    lbo_value = (lbo_result.min_value_per_share + lbo_result.max_value_per_share) / 2
    weighted_sum += lbo_value * lbo_weight
    total_weight += lbo_weight

recommended = weighted_sum / total_weight if total_weight > 0 else 0
```

---

## CURRENT GAPS VS HUMAN APPROACH

| Growth Stage | Current Engine | Human Analysts | Gap to Close |
|-------------|---------------|----------------|--------------|
| Hypergrowth | Uses DCF (wrong!) | Revenue multiples, TAM | ❌ Add stage detection |
| Growth | Equal weights | CCA heavy (70%) | ⚠️ Add weighting |
| Mature | Equal weights | DCF heavy (60%) | ⚠️ Add weighting |
| Decline | Same methods | Liquidation value | ❌ Add distressed logic |

---

## PRIORITY RECOMMENDATION

**CRITICAL** (Implement First - 1 day):
1. Add growth stage classification
2. Skip DCF for hypergrowth/negative FCF
3. Apply stage-based weights (not simple average)

**HIGH** (Next Week - 2 days):
4. Add SaaS-specific metrics (ARR, NRR, LTV/CAC)
5. Filter CCA peers by growth stage
6. Add NTM multiples for high-growth

**MEDIUM** (Future - 1 week):
7. TAM-based valuation for hypergrowth
8. Liquidation analysis for distress
9. Restructuring valuation scenarios

---

## CONCLUSION

**Current State**: ⚠️ One-size-fits-all approach

**Problem**: Hypergrowth companies massively undervalued (DCF with negative FCF gives near-zero)

**Solution**: Stage-based methodology selection
- Hypergrowth: Revenue multiples + TAM (skip DCF)
- Growth: CCA 70% + DCF 30%
- Mature: DCF 60% + CCA 30% + LBO 10%
- Decline: Liquidation value + distressed multiples

**Impact**: Valuations will match human analyst methodology and be stage-appropriate.

**Critical Fix**: Don't run DCF on companies with negative FCF!

---

*Valuation Methodology Analysis Complete*  
*Current approach identified*  
*Growth-stage framework designed*  
*Implementation roadmap provided*
