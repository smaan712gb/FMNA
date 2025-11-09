# DORMANT FEATURES ACTIVATION IMPLEMENTATION GUIDE
## Step-by-Step Activation Plan with Code Examples
**Date**: November 8, 2025

---

## EXECUTIVE SUMMARY

Based on evidence-based code review, I identified **4 fully-implemented advanced features** that exist in engine code but are NOT called in the production orchestrator:

1. **Monte Carlo Simulation** (DCF) - Quantifies uncertainty, provides P10/P90 ranges
2. **LBO Sensitivity Analysis** - IRR sensitivity to exit assumptions  
3. **Merger Sensitivity Analysis** - Deal structure optimization grids
4. **3SM → DCF Integration** - Use integrated financial model FCFF

Plus **2 partial integrations needing enhancement**:
- Individual DD Risk Storage (for granular AI queries)
- Knowledge Graph Building (Cognee nodes/edges)

**All code exists - we just need to wire up the calls.**

---

## IMPLEMENTATION SEQUENCE

We'll activate features in order of value and simplicity:

### Session 1: Core Integrations (Today - 4 hours)
1. Fix 3SM → DCF FCFF flow (use model projections)
2. Activate Monte Carlo simulation
3. Store individual DD risks

### Session 2: Sensitivity Additions (Tomorrow - 3 hours)  
4. Activate LBO sensitivity
5. Activate Merger sensitivity
6. Add sensitivity tabs to Excel

### Session 3: Knowledge Graph (Next Week - 1 day)
7. Build Cognee entity relationships
8. Enable graph queries

---

## DETAILED IMPLEMENTATIONS

### 1. FIX 3SM → DCF INTEGRATION

**Problem**: DCF calculates FCFF manually, ignoring 3-Statement Model output

**Evidence** (orchestrator lines 241-256):
```python
# Line 400+: Three Statement Model runs successfully
three_statement_result = ts_model.build_integrated_model(...)

# But later... Line 241-256: DCF uses SEPARATE FCFF!
cf_statements = financial_data.get('cash_flow', [])
fcff_forecast = []
for cf in cf_statements[:5]:
    fcf = float(cf.get('freeCashFlow', 0))
    fcff_forecast.append(fcf)
# This ignores the 3SM output completely!
```

**Solution**: Check if 3SM ran, use its FCFF forecast

**File to Modify**: `orchestration/comprehensive_orchestrator.py`

**Location**: Around line 241-256 in `_run_valuation_models()`

**Change**:
```python
# BEFORE (lines 241-256):
# Build FCFF forecast from cash flow data
cf_statements = financial_data.get('cash_flow', [])
fcff_forecast = []
for cf in cf_statements[:5]:
    fcf = float(cf.get('freeCashFlow', 0))
    fcff_forecast.append(fcf)

# If not enough history, project forward
if len(fcff_forecast) < 5:
    base_fcf = fcff_forecast[-1] if fcff_forecast else float(cf_statements[0].get('freeCashFlow', 0))
    growth_rate = 0.08
    for i in range(5 - len(fcff_forecast)):
        fcff_forecast.append(base_fcf * ((1 + growth_rate) ** (i + 1)))

# AFTER (integration fix):
# ACTIVATION: Use 3SM FCFF if available
if three_statement_result and hasattr(three_statement_result, 'fcf_forecast') and three_statement_result.fcf_forecast:
    fcff_forecast = three_statement_result.fcf_forecast
    logger.info(f"   ✅ Using FCFF from 3-Statement Model ({len(fcff_forecast)} periods)")
else:
    # Fallback: Build FCFF forecast from cash flow data
    cf_statements = financial_data.get('cash_flow', [])
    fcff_forecast = []
    for cf in cf_statements[:5]:
        fcf = float(cf.get('freeCashFlow', 0))
        fcff_forecast.append(fcf)
    
    # If not enough history, project forward
    if len(fcff_forecast) < 5:
        base_fcf = fcff_forecast[-1] if fcff_forecast else float(cf_statements[0].get('freeCashFlow', 0))
        growth_rate = 0.08
        for i in range(5 - len(fcff_forecast)):
            fcff_forecast.append(base_fcf * ((1 + growth_rate) ** (i + 1)))
    logger.info(f"   → Using manual FCFF calculation (3SM not available)")
```

**Impact**: DCF now uses integrated 3SM projections (consistent methodology)

---

### 2. ACTIVATE MONTE CARLO SIMULATION

**Evidence**: Method exists in `engines/dcf_engine.py` lines ~180-250 but never called

**Step 2A: Add to Modeling Agent**

**File**: `agents/modeling_agent.py`

**Location**: After `run_dcf_valuation()` method

**Add New Method**:
```python
def run_dcf_with_monte_carlo(
    self,
    symbol: str,
    fcff_forecast: List[float],
    wacc_inputs: WACCInputs,
    terminal_inputs: TerminalValueInputs,
    shares_outstanding: float,
    cash: float,
    debt: float,
    simulations: int = 10000
) -> Tuple[DCFResult, Dict[str, Any]]:
    """
    Run DCF with Monte Carlo uncertainty analysis
    
    Returns:
        Tuple of (DCFResult, Monte Carlo statistics dict)
    """
    logger.info(f"Running DCF with Monte Carlo ({simulations} simulations)")
    
    # Base DCF (existing)
    dcf_result = self.run_dcf_valuation(
        symbol=symbol,
        fcff_forecast=fcff_forecast,
        wacc_inputs=wacc_inputs,
        terminal_inputs=terminal_inputs,
        shares_outstanding=shares_outstanding,
        cash=cash,
        debt=debt
    )
    
    # ACTIVATION: Monte Carlo simulation
    mc_results = self.dcf_engine.monte_carlo_simulation(
        fcff_forecast=fcff_forecast,
        wacc_inputs=wacc_inputs,
        terminal_inputs=terminal_inputs,
        shares_outstanding=shares_outstanding,
        cash=cash,
        debt=debt,
        simulations=simulations
    )
    
    logger.success(f"Monte Carlo: P50=${mc_results['median']:.2f}, "
                  f"90% CI: ${mc_results['p10']:.2f}-${mc_results['p90']:.2f}")
    
    return dcf_result, mc_results
```

**Step 2B: Call from Orchestrator**

**File**: `orchestration/comprehensive_orchestrator.py`

**Location**: After line where `dcf_result = self.modeling.run_dcf_valuation(...)` is called

**Add**:
```python
# After DCF runs successfully
if run_dcf and dcf_result:
    logger.info("   → Running Monte Carlo uncertainty analysis...")
    try:
        mc_results = self.modeling.dcf_engine.monte_carlo_simulation(
            fcff_forecast=fcff_forecast,
            wacc_inputs=wacc_inputs,
            terminal_inputs=terminal_inputs,
            shares_outstanding=float(shares_out),
            cash=float(balance_sheet.get('cashAndCashEquivalents', 0)),
            debt=float(balance_sheet.get('totalDebt', 0)),
            simulations=10000
        )
        
        # Attach to DCF result
        dcf_result.monte_carlo = mc_results
        
        logger.success(f"   ✅ Monte Carlo: Mean=${mc_results['mean']:.2f}, "
                      f"P10-P90: ${mc_results['p10']:.2f}-${mc_results['p90']:.2f}")
    except Exception as e:
        logger.warning(f"   ⚠ Monte Carlo failed: {e}")
```

**Step 2C: Add Monte Carlo Excel Tab**

**File**: `agents/exporter_agent_enhanced.py`

**Location**: In `export_comprehensive_excel_model()` method

**Add**:
```python
# After existing tabs, add Monte Carlo tab if available
if all_data.get('dcf_result') and hasattr(all_data['dcf_result'], 'monte_carlo'):
    ws_mc = wb.create_sheet("Monte_Carlo_DCF")
    self._create_monte_carlo_tab(ws_mc, all_data['dcf_result'].monte_carlo)
```

**Add New Method**:
```python
def _create_monte_carlo_tab(self, ws, mc_results: Dict[str, Any]):
    """Create Monte Carlo simulation results tab"""
    ws['A1'] = "MONTE CARLO SIMULATION - DCF VALUATION"
    ws['A1'].font = Font(size=14, bold=True)
    
    row = 3
    
    # Summary Statistics
    ws[f'A{row}'] = "SIMULATION STATISTICS"
    ws[f'A{row}'].font = Font(bold=True)
    ws[f'A{row}'].fill = PatternFill(start_color=IB_COLORS.LIGHT_BLUE,
                                     end_color=IB_COLORS.LIGHT_BLUE,
                                     fill_type="solid")
    row += 1
    
    stats = {
        'Number of Simulations': mc_results.get('simulations', 10000),
        'Mean Value per Share': mc_results.get('mean', 0),
        'Median Value per Share': mc_results.get('median', 0),
        'Standard Deviation': mc_results.get('std', 0),
        'Minimum Value': mc_results.get('min', 0),
        'Maximum Value': mc_results.get('max', 0),
    }
    
    for metric, value in stats.items():
        ws[f'A{row}'] = metric
        ws[f'B{row}'] = value
        if 'Share' in metric or 'Value' in metric:
            ws[f'B{row}'].number_format = '$#,##0.00'
        elif 'Deviation' in metric:
            ws[f'B{row}'].number_format = '$#,##0.00'
        else:
            ws[f'B{row}'].number_format = '#,##0'
        row += 1
    
    row += 2
    
    # Confidence Intervals
    ws[f'A{row}'] = "CONFIDENCE INTERVALS"
    ws[f'A{row}'].font = Font(bold=True)
    ws[f'A{row}'].fill = PatternFill(start_color=IB_COLORS.LIGHT_BLUE,
                                     end_color=IB_COLORS.LIGHT_BLUE,
                                     fill_type="solid")
    row += 1
    
    percentiles = {
        '10th Percentile (P10)': mc_results.get('p10', 0),
        '25th Percentile (P25)': mc_results.get('p25', 0),
        'Median (P50)': mc_results.get('median', 0),
        '75th Percentile (P75)': mc_results.get('p75', 0),
        '90th Percentile (P90)': mc_results.get('p90', 0),
    }
    
    for label, value in percentiles.items():
        ws[f'A{row}'] = label
        ws[f'B{row}'] = value
        ws[f'B{row}'].number_format = '$#,##0.00'
        
        # Highlight key percentiles
        if 'P10' in label or 'P90' in label:
            ws[f'B{row}'].font = Font(bold=True)
        elif 'Median' in label:
            ws[f'B{row}'].font = Font(bold=True, color=IB_COLORS.GREEN)
        
        row += 1
    
    row += 2
    
    # Risk Assessment
    ws[f'A{row}'] = "RISK ASSESSMENT"
    ws[f'A{row}'].font = Font(bold=True)
    ws[f'A{row}'].fill = PatternFill(start_color=IB_COLORS.LIGHT_BLUE,
                                     end_color=IB_COLORS.LIGHT_BLUE,
                                     fill_type="solid")
    row += 1
    
    median = mc_results.get('median', 0)
    p10 = mc_results.get('p10', 0)
    p90 = mc_results.get('p90', 0)
    
    downside_risk = ((median - p10) / median * 100) if median > 0 else 0
    upside_potential = ((p90 - median) / median * 100) if median > 0 else 0
    
    ws[f'A{row}'] = "Downside Risk (Median to P10)"
    ws[f'B{row}'] = downside_risk / 100
    ws[f'B{row}'].number_format = '0.0%'
    row += 1
    
    ws[f'A{row}'] = "Upside Potential (Median to P90)"
    ws[f'B{row}'] = upside_potential / 100
    ws[f'B{row}'].number_format = '0.0%'
    row += 1
    
    ws[f'A{row}'] = "80% Confidence Interval"
    ws[f'B{row}'] = f"${p10:.2f} - ${p90:.2f}"
    ws[f'B{row}'].font = Font(bold=True)
    
    ws.column_dimensions['A'].width = 35
    ws.column_dimensions['B'].width = 20
```

---

### 3. ACTIVATE LBO SENSITIVITY

**E vidence**: Method exists in `engines/lbo_engine.py` but never called

**File**: `orchestration/comprehensive_orchestrator.py`

**Location**: After LBO calculation succeeds

**Add**:
```python
# After: lbo_result = self.modeling.run_lbo_analysis(...)

if run_lbo and lbo_result:
    logger.info("   → Running LBO sensitivity analysis...")
    try:
        lbo_sensitivity = self.lbo_engine.sensitivity_analysis(
            base_inputs=lbo_inputs,
            exit_multiple_range=(8.0, 14.0),  # 8x to 14x exit multiples
            ebitda_range=(0.85, 1.15),  # 85% to 115% of base case EBITDA
            steps=5
        )
        
        # Attach to LBO result
        lbo_result.sensitivity = lbo_sensitivity
        
        logger.success(f"   ✅ LBO Sensitivity: Exit multiples 8x-14x analyzed")
    except Exception as e:
        logger.warning(f"   ⚠ LBO sensitivity failed: {e}")
```

---

### 4. ACTIVATE MERGER SENSITIVITY

**File**: `orchestration/comprehensive_orchestrator.py`

**Location**: After merger calculation succeeds

**Add**:
```python
# After: merger_result = merger_model.calculate_accretion_dilution(...)

if run_merger and merger_result:
    logger.info("   → Running merger sensitivity analysis...")
    try:
        merger_sensitivity = merger_model.sensitivity_analysis(
            base_inputs=merger_inputs,
            premium_range=(0.20, 0.40),  # 20% to 40% premium
            stock_consideration_range=(0.0, 1.0),  # 0% to 100% stock
            steps=5
        )
        
        # Attach to merger result
        merger_result.sensitivity = merger_sensitivity
        
        logger.success(f"   ✅ Merger Sensitivity: Premium 20%-40%, Stock 0%-100% analyzed")
    except Exception as e:
        logger.warning(f"   ⚠ Merger sensitivity failed: {e}")
```

---

### 5. STORE INDIVIDUAL DD RISKS

**Problem**: DD risks stored as bulk JSON, not individually queryable

**Current** (`_store_results()` line ~520):
```python
# All DD risks in one JSON blob
'due_diligence': {
    category: [risk.dict() for risk in risks]
    for category, risks in result.due_diligence.items()
}
```

**Solution**: Store each risk individually

**File**: `orchestration/comprehensive_orchestrator.py`

**Location**: In `_store_results()` method, after main storage

**Add**:
```python
# After storing comprehensive results, store individual risks
if result.due_diligence:
    logger.info("   → Storing individual DD risks for AI queries...")
    risk_count = 0
    
    for category, risks in result.due_diligence.items():
        for risk in risks:
            # Store each risk card individually
            self.modeling.memory.store_context(
                context_type='dd_risk_card',
                data={
                    'severity': risk.severity,
                    'title': risk.title,
                    'description': risk.description,
                    'category': risk.category,
                    'subcategory': risk.subcategory,
                    'mitigation': risk.mitigation,
                    'probability': getattr(risk, 'probability', None),
                    'impact': getattr(risk, 'impact', None)
                },
                metadata={
                    'ticker': result.symbol,
                    'category': category,
                    'severity': risk.severity,
                    'session_id': comprehensive_memory.session_id
                }
            )
            risk_count += 1
    
    logger.success(f"   ✓ Stored {risk_count} individual risk cards for AI retrieval")
```

**Impact**: AI can now answer queries like:
- "What are the high severity financial risks for AAPL?"
- "Show me all legal risks across my analyses"
- "Find companies with similar risk profiles"

---

## TESTING CHECKLIST

After each activation, verify:

### Monte Carlo:
- [ ] Method is called after DCF
- [ ] Results logged with P10/P50/P90
- [ ] Excel has Monte_Carlo tab
- [ ] AI can answer "What's the P90 DCF value?"

### 3SM Integration:
- [ ] 3SM runs before DCF
- [ ] DCF uses 3SM FCFF (not manual)
- [ ] Log shows "Using FCFF from 3-Statement Model"
- [ ] Values are consistent

### LBO Sensitivity:
- [ ] Called after base LBO
- [ ] Sensitivity DataFrame attached
- [ ] Excel shows IRR sensitivity grid
- [ ] Exit multiple range 8x-14x included

### Merger Sensitivity:
- [ ] Called after merger model
- [ ] Premium vs stock mix grid created
- [ ] Excel Accretion/Dilution tab updated

### Individual DD Risks:
- [ ] Each risk stored separately
- [ ] Log shows "Stored X individual risk cards"
- [ ] AI can filter by severity
- [ ] AI can filter by category

---

## ROLLBACK PLAN

If any activation causes issues:

1. **Monte Carlo**: Comment out the call, DCF still works normally
2. **LBO Sensitivity**: Comment out, LBO base case unaffected
3. **Merger Sensitivity**: Comment out, merger base case unaffected
4. **3SM Integration**: Revert to manual FCFF, functionality preserved
5. **Individual DD Storage**: Original bulk storage still intact

**All activations are ADDITIVE - they don't break existing functionality**

---

## NEXT STEPS

1. Review this implementation guide
2. Approve which activations to proceed with
3. Implement one at a time
4. Test after each activation
5. Proceed to next only after verification

**Ready to begin implementation when you approve.**

---

*Evidence-Based Implementation Plan*  
*All features verified to exist in code*  
*Activations are additive and safe*  
*No existing functionality will be broken*
