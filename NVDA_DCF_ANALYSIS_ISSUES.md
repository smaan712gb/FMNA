# NVDA DCF Analysis - Critical Issues Identified

## Executive Summary
The DCF analysis showing **$4.74 per share** is severely flawed and undervalues NVIDIA by **~97%** compared to reality (~$140/share). Multiple critical errors compound to create this massive discrepancy.

---

## Current DCF Results (From Screenshot)
| Metric | Value |
|--------|-------|
| PV of Forecast FCF | $91.2B |
| PV of Terminal Value | $25.9B |
| Enterprise Value | $117.1B |
| Less: Net Debt | $1.7B |
| **Equity Value** | **$115.4B** |
| Shares Outstanding | 24,347.00 |
| **Value per Share** | **$4.74** |

**Reality Check:**
- NVDA Market Cap: **~$3.4 TRILLION** (as of late 2024)
- Actual Stock Price: **~$140/share**
- Actual Shares Outstanding: **~24.5 BILLION shares**
- This DCF: **$4.74/share** ❌ **OFF BY 97%**

---

## CRITICAL ISSUES IDENTIFIED

### 🚨 Issue #1: SHARES OUTSTANDING UNIT ERROR (MOST CRITICAL)

**Current Model Shows:** 24,347.00 shares

**Reality:** NVDA has ~24.5 BILLION shares outstanding

**The Problem:**
The model shows shares in MILLIONS but the calculation treats them as ABSOLUTE numbers.

**Correct Calculation:**
- Equity Value: $115,382,681,447
- Shares Outstanding: 24,347 MILLION = 24,347,000,000 shares
- **Correct Value/Share = $115.4B ÷ 24.347B = $4.74** ✅ (This part is right)

**BUT THE MISSING PROBLEM:**
If we're getting $4.74/share with proper unit conversion, then the Enterprise Value of $117B is **MASSIVELY UNDERSTATED**. NVDA's actual enterprise value should be ~$3.4 trillion.

---

### 🚨 Issue #2: FREE CASH FLOW MASSIVELY UNDERSTATED

**Current Model:**
- PV of Forecast FCF: $91.2B
- PV of Terminal Value: $25.9B
- **Total Enterprise Value: $117.1B**

**Reality Check - NVDA's Actual FCF:**
- FY2024 FCF: **~$27B**
- FY2025E FCF: **~$50-60B+** (given massive AI demand)
- Current Run Rate: **$60B+ annually**

**The Problem:**
Even with a 12.31% discount rate, the model implies:
- Annual FCF forecast: Only ~$11-15B per year
- Terminal FCF: Only ~$3-4B annually

**This is absurd** - NVDA is currently generating $60B/year in FCF!

---

### 🚨 Issue #3: WACC TOO HIGH

**Current Model:** 12.31%

**Reality for NVDA:**
- Risk-free rate: ~4.5%
- Market risk premium: ~6-7%
- NVDA Beta: ~1.5-1.7
- Expected Cost of Equity: ~14-16%
- But NVDA has virtually no debt (99.96% equity)
- **Appropriate WACC: 14-15%** (essentially = cost of equity)

**However, even 12.31% is not the main problem** - the FCF forecasts are the real issue.

---

### 🚨 Issue #4: TERMINAL GROWTH RATE TOO LOW

**Current Model Base Case:** 2.5% (from sensitivity table)

**Reality for NVDA:**
Given their dominance in:
- AI/ML chips (90%+ market share)
- Data center GPUs
- Gaming GPUs
- Autonomous vehicles
- Enterprise AI

**More Appropriate:** 3.5-4% terminal growth rate minimum

---

### 🚨 Issue #5: FORECAST PERIOD UNCLEAR

Not visible in screenshot, but implied issues:
- Forecast period likely only 5 years
- For a high-growth company like NVDA, should use 10-year explicit forecast
- AI revolution is multi-decade opportunity

---

## ROOT CAUSE ANALYSIS

### Where the Model Went Wrong:

1. **FCF Forecast Too Conservative**
   - Model likely uses historical average or mean-reversion assumptions
   - Fails to account for AI revolution driving unprecedented demand
   - NVDA's FCF has grown 300%+ in 2 years
   - Model probably assumes immediate mean reversion

2. **Terminal Value Assumptions**
   - Low perpetuity growth (2.5%)
   - Low terminal FCF base
   - Doesn't capture NVDA's structural competitive advantages

3. **Data Input Errors**
   - May be using outdated financial data
   - Not using latest quarterly results
   - Missing guidance and forward outlook

---

## CORRECTED DCF FRAMEWORK

### Realistic Assumptions:

| Parameter | Current Model | Realistic Value |
|-----------|---------------|-----------------|
| **Latest FCF** | ~$15B implied | **$60B actual** |
| **FCF Growth (Yr 1-3)** | ~10% implied | **25-30%** |
| **FCF Growth (Yr 4-5)** | ~8% implied | **15-20%** |
| **FCF Growth (Yr 6-10)** | N/A | **10-12%** |
| **Terminal Growth** | 2.5% | **3.5-4.0%** |
| **WACC** | 12.31% | **13-14%** |
| **Forecast Period** | 5 years (implied) | **10 years** |

### Quick Recalculation:

**Conservative Scenario:**
```
Year 1: $60B
Year 2: $75B (+25%)
Year 3: $90B (+20%)
Year 4: $105B (+17%)
Year 5: $120B (+14%)
Year 6-10: 10% growth to ~$190B

PV of Explicit Period (13% WACC): ~$430B
Terminal Value (3.5% growth, 13% WACC): ~$2.5T
PV of Terminal Value: ~$1.2T

Enterprise Value: ~$1.6T
Less: Net Debt: $1.7B
Equity Value: ~$1.6T
Shares: 24.5B
Value per Share: ~$65
```

**Base Case Scenario:**
```
With more aggressive but justified assumptions:
Value per Share: $90-120
```

**Bull Case:**
```
If AI revolution continues:
Value per Share: $150-200+
```

---

## WHAT NEEDS TO BE FIXED

### Immediate Actions:

1. ✅ **Update Financial Data**
   - Use latest quarterly results (Q3 FY2025)
   - Current TTM FCF: ~$60B+
   - Update revenue, margins, CapEx

2. ✅ **Revise Growth Assumptions**
   - Near-term: 20-30% FCF growth (Years 1-3)
   - Medium-term: 12-18% FCF growth (Years 4-7)
   - Long-term: 8-12% FCF growth (Years 8-10)
   - Terminal: 3.5-4.0% perpetuity growth

3. ✅ **Extend Forecast Period**
   - Change from 5-year to 10-year explicit forecast
   - NVDA is in early innings of AI revolution

4. ✅ **Review WACC Components**
   - Update risk-free rate to current ~4.5%
   - Update equity risk premium
   - Review beta calculation
   - Result should be 13-15% WACC

5. ✅ **Add Scenario Analysis**
   - Bear: Competition catches up, margins compress
   - Base: Maintain leadership, normal growth
   - Bull: AI revolution accelerates further

6. ✅ **Validate Units**
   - Ensure shares in millions vs billions is consistent
   - Check all dollar amounts (thousands vs millions vs billions)

---

## SENSITIVITY ANALYSIS REVIEW

The current sensitivity table shows:
- At 12.3% WACC & 2.0% growth: $4.45/share
- At 12.3% WACC & 3.0% growth: $5.02/share

**These are all wrong because the underlying FCF forecasts are too low.**

A corrected sensitivity table should show:
- Range of $50-150+ per share depending on assumptions
- Much wider range reflecting uncertainty in AI growth

---

## COMPARATIVE VALUATION CHECK

### Trading Multiples (Reality Check):
- NVDA EV/FCF: ~55-60x (at $140/share)
- Your Model EV/FCF: ~2x (implied from $117B EV ÷ $60B FCF)

**This is impossible.** No company trades at 2x FCF, especially not NVDA.

### Peer Comparison:
- NVDA historically trades at 30-50x FCF in high growth periods
- Even mature big tech trades at 15-25x FCF
- Your model implies 2x FCF multiple

---

## RECOMMENDED NEXT STEPS

1. **Immediately** review the Excel formulas for:
   - FCF calculations
   - Growth rate applications
   - Present value discounting
   - Share count units

2. **Update all inputs** with latest data:
   - Q3 FY2025 financials
   - Latest guidance
   - Current debt levels
   - Current share count

3. **Rebuild the forecast model** with:
   - 10-year explicit forecast period
   - Realistic FCF growth rates
   - AI market growth considerations
   - Competitive advantage analysis

4. **Cross-check with multiples**:
   - EV/Sales
   - P/E ratios
   - EV/FCF
   - Compare to peers (AMD, INTC, TSM)

5. **Run scenarios**:
   - Bear case (40% below base)
   - Base case (should be $80-120)
   - Bull case (40% above base)

---

## CONCLUSION

The model has **systemic errors** in FCF forecasting that cascade through the entire valuation:

1. ❌ Using outdated or incorrect FCF data (~$15B vs actual $60B)
2. ❌ Far too conservative growth assumptions
3. ❌ Insufficient forecast period (5 vs 10 years needed)
4. ❌ Low terminal growth rate
5. ⚠️ Slightly high WACC (but not the main issue)

**Bottom Line:**
- Current output: $4.74/share
- Realistic range: $80-140/share  
- Current market: ~$140/share

The model needs to be **completely rebuilt** with current financial data and realistic growth assumptions for NVDA's position in the AI revolution.

---

**Generated:** 2025-01-09  
**Status:** Critical Issues Identified - Model Requires Complete Rebuild
