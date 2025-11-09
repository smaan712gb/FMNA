"""
Quick Integration Script - Add AI Valuation to Existing Results
This script shows the minimal changes needed to add AI valuation to orchestrator
"""

# The key changes needed in comprehensive_orchestrator.py:

# 1. Import (DONE ✓):
# from engines.ai_valuation_engine import AIValuationEngine, CompanyProfile

# 2. Initialize in __init__ (DONE ✓):
# self.ai_valuation = AIValuationEngine()

# 3. After Step 1 (data ingestion), add AI classification:
"""
# STEP 2: AI COMPANY CLASSIFICATION
logger.info("🤖 AI Company Classification...")

# Calculate revenue growth
income_statements = financial_data.get('income_statement', [])
revenue_growth = 0.0
if len(income_statements) >= 2:
    current_rev = float(income_statements[0].get('revenue', 0))
    prior_rev = float(income_statements[1].get('revenue', 1))
    revenue_growth = (current_rev / prior_rev - 1) if prior_rev > 0 else 0.0

# AI Classification
company_profile = self.ai_valuation.classify_company(
    company_name=profile.legal_name if profile else symbol,
    description=profile.description if profile and hasattr(profile, 'description') else "",
    industry=profile.industry if profile and hasattr(profile, 'industry') else "Technology",
    revenue=float(income_stmt.get('revenue', 0)),
    revenue_growth=revenue_growth,
    ebitda=float(income_stmt.get('ebitda', 0)),
    fcf=float(cash_flow.get('freeCashFlow', 0)),
    rd_expense=float(income_stmt.get('researchAndDevelopmentExpenses', 0))
)

logger.success(f"✓ AI: {company_profile.company_type.value} at {company_profile.development_stage.value}")
"""

# 4. After all valuations run, add AI weighting:
"""
# Calculate AI-weighted valuation
if dcf_result or cca_result or lbo_result:
    ai_weighted, explanation, breakdown = self.ai_valuation.calculate_weighted valuation(
        profile=company_profile,
        dcf_value=dcf_result.value_per_share if dcf_result else None,
        cca_value=cca_result.value_per_share_ebitda if cca_result else None,
        lbo_value=((lbo_result.min_value_per_share + lbo_result.max_value_per_share) / 2) if lbo_result else None
    )
    
    logger.success(f"✓ AI-Weighted Fair Value: ${ai_weighted:.2f}/share")
    
    # Add to valuation package
    valuation.ai_weighted_value = ai_weighted
    valuation.ai_classification = company_profile
    valuation.ai_explanation = explanation
"""

# 5. In ComprehensiveAnalysisResult dataclass, add:
"""
@dataclass
class ComprehensiveAnalysisResult:
    ...existing fields...
    ai_classification: Optional[CompanyProfile] = None  # NEW
"""

print("Integration guide created - see code comments above")
print("To complete: Apply these changes to comprehensive_orchestrator.py")
