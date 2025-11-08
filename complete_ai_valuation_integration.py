"""
Complete AI Valuation Integration (Remaining 40%)
Integrates AI classification, weighting, and display across entire platform
"""

import re
from pathlib import Path
from loguru import logger


def update_orchestrator():
    """Add AI weighting calculation after valuations"""
    
    orchestrator_path = Path("orchestration/comprehensive_orchestrator.py")
    content = orchestrator_path.read_text(encoding='utf-8')
    
    # Find the valuation step and add AI weighting after it
    search_pattern = r'(logger\.success\(f"✓ Step 2 Complete - All valuations calculated"\)\s+logger\.info\(""\))'
    
    replacement = r'''\1
        
        # STEP 2.5: AI-WEIGHTED VALUATION
        logger.info("┏" + "━" * 78 + "┓")
        logger.info("┃ STEP 2.5: AI-WEIGHTED VALUATION SYNTHESIS")
        logger.info("┗" + "━" * 78 + "┛")
        
        # Calculate AI-weighted fair value
        ai_weighted_value, ai_explanation, ai_breakdown = self.ai_valuation.calculate_weighted_valuation(
            profile=company_profile,
            dcf_value=valuation.dcf_result.value_per_share if valuation.dcf_result else None,
            cca_value=valuation.cca_result.value_per_share_ebitda if valuation.cca_result else None,
            lbo_value=valuation.lbo_result.min_value_per_share if valuation.lbo_result else None,
            growth_scenario_value=(
                valuation.growth_scenarios['Base'].fair_value if 
                valuation.growth_scenarios and 'Base' in valuation.growth_scenarios 
                else None
            )
        )
        
        # Store AI results in valuation package
        valuation.ai_classification = company_profile
        valuation.ai_weighted_value = ai_weighted_value
        valuation.ai_explanation = ai_explanation
        valuation.ai_breakdown = ai_breakdown
        
        logger.success("✓ AI-Weighted Valuation Complete")
        logger.info(f"  🎯 AI Fair Value: ${ai_weighted_value:.2f}/share")
        logger.info(f"  📊 Methodology Blend:")
        for method_name, details in ai_breakdown.items():
            if details.get('used'):
                logger.info(f"     • {method_name.upper()}: {details['weight']:.0%} weight")
        logger.info("")'''
    
    content = re.sub(search_pattern, replacement, content, count=1)
    
    # Update ComprehensiveAnalysisResult to include AI data
    search_pattern2 = r'(@dataclass\s+class ComprehensiveAnalysisResult:.*?# Metadata\s+data_sources_used: List\[str\]\s+total_api_calls: int\s+analysis_duration_seconds: float)'
    
    replacement2 = r'''\1
    
    # AI Valuation Results
    ai_classification: Optional[Any] = None
    ai_weighted_value: Optional[float] = None
    ai_explanation: Optional[str] = None
    ai_breakdown: Optional[Dict[str, Any]] = None'''
    
    content = re.sub(search_pattern2, replacement2, content, count=1, flags=re.DOTALL)
    
    # Update result construction to include AI data
    search_pattern3 = r'(result = ComprehensiveAnalysisResult\(\s+symbol=symbol,\s+company_name=.*?analysis_duration_seconds=duration\s+\))'
    
    replacement3 = r'''\1
        
        # Add AI valuation results
        result.ai_classification = getattr(valuation, 'ai_classification', None)
        result.ai_weighted_value = getattr(valuation, 'ai_weighted_value', None)
        result.ai_explanation = getattr(valuation, 'ai_explanation', None)
        result.ai_breakdown = getattr(valuation, 'ai_breakdown', None)'''
    
    content = re.sub(search_pattern3, replacement3, content, count=1, flags=re.DOTALL)
    
    # Fix step numbering in _run_due_diligence
    content = content.replace('# STEP 3: SEC FILING INGESTION (NEW)', '# STEP 4: SEC FILING INGESTION')
    content = content.replace('┃ STEP 3: SEC FILING INGESTION (10-K, 10-Q)', '┃ STEP 4: SEC FILING INGESTION (10-K, 10-Q)')
    content = content.replace('✓ Step 3 Complete - SEC filings', '✓ Step 4 Complete - SEC filings')
    content = content.replace('# STEP 4: DUE DILIGENCE (ENHANCED WITH FILING DATA)', '# STEP 5: DUE DILIGENCE (ENHANCED WITH FILING DATA)')
    content = content.replace('┃ STEP 4: DUE DILIGENCE (6 Categories with SEC Data)', '┃ STEP 5: DUE DILIGENCE (6 Categories with SEC Data)')
    content = content.replace('✓ Step 4 Complete -', '✓ Step 5 Complete -')
    content = content.replace('# STEP 5: SYNTHESIS & STORAGE', '# STEP 6: SYNTHESIS & STORAGE')
    content = content.replace('┃ STEP 5: SYNTHESIS & STORAGE', '┃ STEP 6: SYNTHESIS & STORAGE')
    content = content.replace('✓ Step 5 Complete - Results stored', '✓ Step 6 Complete - Results stored')
    
    orchestrator_path.write_text(content, encoding='utf-8')
    logger.info("✓ Updated orchestrator with AI weighting")


def update_valuation_package():
    """Add AI fields to ValuationPackage"""
    
    modeling_path = Path("agents/modeling_agent.py")
    content = modeling_path.read_text(encoding='utf-8')
    
    # Add AI fields to ValuationPackage
    search_pattern = r'(@dataclass\s+class ValuationPackage:.*?llm_summary: str = "")'
    
    replacement = r'''\1
    
    # AI Valuation Results
    ai_classification: Optional[Any] = None
    ai_weighted_value: Optional[float] = None
    ai_explanation: Optional[str] = None
    ai_breakdown: Optional[Dict[str, Any]] = None'''
    
    content = re.sub(search_pattern, replacement, content, count=1, flags=re.DOTALL)
    
    # Update store_valuation_in_memory to include AI data
    search_pattern2 = r"('llm_summary': package\.llm_summary\s+\})"
    
    replacement2 = r'''\1,
                'ai_classification': {
                    'company_type': package.ai_classification.company_type.value if package.ai_classification else None,
                    'development_stage': package.ai_classification.development_stage.value if package.ai_classification else None,
                    'key_value_drivers': package.ai_classification.key_value_drivers if package.ai_classification else [],
                    'classification_confidence': package.ai_classification.classification_confidence if package.ai_classification else None,
                    'reasoning': package.ai_classification.reasoning if package.ai_classification else None
                } if package.ai_classification else None,
                'ai_weighted_value': package.ai_weighted_value,
                'ai_breakdown': package.ai_breakdown'''
    
    content = re.sub(search_pattern2, replacement2, content, count=1)
    
    modeling_path.write_text(content, encoding='utf-8')
    logger.info("✓ Updated ValuationPackage with AI fields")


def update_storage():
    """Add AI classification storage to memory_manager"""
    
    memory_path = Path("storage/memory_manager.py")
    content = memory_path.read_text(encoding='utf-8')
    
    # Add method to store AI classification
    search_pattern = r'(class MemoryManager:.*?def __init__\(self\):.*?logger\.info\("MemoryManager initialized"\))'
    
    # Find the end of the class and add new method
    if 'def store_ai_classification(' not in content:
        # Find last method in class
        insert_pos = content.rfind('    def ')
        # Find end of that method
        next_class_pos = content.find('\nclass ', insert_pos + 1)
        if next_class_pos == -1:
            next_class_pos = len(content)
        
        new_method = '''
    
    def store_ai_classification(
        self,
        ticker: str,
        company_profile: Any,
        weighted_value: float,
        breakdown: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> bool:
        """
        Store AI classification and valuation weighting
        
        Args:
            ticker: Stock ticker
            company_profile: CompanyProfile from AI engine
            weighted_value: AI-weighted fair value
            breakdown: Methodology breakdown
            session_id: Optional session ID
            
        Returns:
            Success status
        """
        try:
            # Store in context for AI QA retrieval
            ai_data = {
                'company_type': company_profile.company_type.value,
                'development_stage': company_profile.development_stage.value,
                'key_value_drivers': company_profile.key_value_drivers,
                'classification_confidence': company_profile.classification_confidence,
                'reasoning': company_profile.reasoning,
                'valuation_methodologies': [
                    {
                        'method': m.method_name,
                        'weight': m.weight,
                        'reason': m.reason,
                        'focus_multiples': m.focus_multiples
                    }
                    for m in company_profile.valuation_methodologies if m.use
                ],
                'ai_weighted_value': weighted_value,
                'methodology_breakdown': breakdown
            }
            
            self.store_context(
                context_type='ai_classification',
                data=ai_data,
                metadata={
                    'ticker': ticker,
                    'session_id': session_id or f'ai_{ticker}_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}',
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"✓ Stored AI classification for {ticker}")
            logger.info(f"  Type: {company_profile.company_type.value}")
            logger.info(f"  Stage: {company_profile.development_stage.value}")
            logger.info(f"  AI Fair Value: ${weighted_value:.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store AI classification: {e}")
            return False
'''
        
        content = content[:next_class_pos] + new_method + content[next_class_pos:]
        
        memory_path.write_text(content, encoding='utf-8')
        logger.info("✓ Added AI classification storage to MemoryManager")


def update_orchestrator_storage():
    """Update orchestrator to call AI classification storage"""
    
    orchestrator_path = Path("orchestration/comprehensive_orchestrator.py")
    content = orchestrator_path.read_text(encoding='utf-8')
    
    # Add AI storage call in _store_results
    search_pattern = r'(# Store valuation in memory \(existing\)\s+await self\.modeling\.store_valuation_in_memory\(result\.valuation\)\s+logger\.success\("   ✓ Valuation package stored"\))'
    
    replacement = r'''\1
            
            # Store AI classification if available
            if result.ai_classification and result.ai_weighted_value:
                self.modeling.memory.store_ai_classification(
                    ticker=result.symbol,
                    company_profile=result.ai_classification,
                    weighted_value=result.ai_weighted_value,
                    breakdown=result.ai_breakdown,
                    session_id=comprehensive_memory.session_id
                )
                logger.success("   ✓ AI classification stored for QA retrieval")'''
    
    content = re.sub(search_pattern, replacement, content, count=1)
    
    orchestrator_path.write_text(content, encoding='utf-8')
    logger.info("✓ Updated orchestrator to store AI classification")


def main():
    """Run all integration updates"""
    logger.info("="*80)
    logger.info("COMPLETING AI VALUATION INTEGRATION (40% REMAINING)")
    logger.info("="*80)
    
    try:
        logger.info("\n[1/4] Updating Orchestrator...")
        update_orchestrator()
        
        logger.info("\n[2/4] Updating ValuationPackage...")
        update_valuation_package()
        
        logger.info("\n[3/4] Updating Storage...")
        update_storage()
        
        logger.info("\n[4/4] Updating Orchestrator Storage Call...")
        update_orchestrator_storage()
        
        logger.info("\n" + "="*80)
        logger.success("✓ BACKEND INTEGRATION COMPLETE (30% of 40%)")
        logger.info("="*80)
        logger.info("\nCompleted:")
        logger.info("  ✓ Orchestrator: AI weighting after valuations")
        logger.info("  ✓ ValuationPackage: AI fields added")
        logger.info("  ✓ ComprehensiveAnalysisResult: AI data included")
        logger.info("  ✓ MemoryManager: AI classification storage")
        logger.info("  ✓ Step numbering fixed")
        logger.info("\nRemaining:")
        logger.info("  ⏳ Frontend: AI display (Streamlit)")
        logger.info("  ⏳ Outputs: Excel, IC Memo, Dashboard")
        logger.info("\nNext: Run frontend and outputs integration")
        
    except Exception as e:
        logger.error(f"Integration failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
