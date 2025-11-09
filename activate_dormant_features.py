"""
Dormant Features Activation Script
Activates: Monte Carlo, LBO Sensitivity, Merger Sensitivity, 3SM→DCF Integration, Individual DD Storage
"""

import re
from pathlib import Path
from loguru import logger


def activate_features():
    """Activate all dormant features in orchestrator and related files"""
    
    logger.info("="*80)
    logger.info("ACTIVATING DORMANT FEATURES")
    logger.info("="*80)
    
    # Read orchestrator
    orch_path = Path("orchestration/comprehensive_orchestrator.py")
    with open(orch_path, 'r', encoding='utf-8') as f:
        orch_content = f.read()
    
    original_content = orch_content
    
    # ========================================
    # ACTIVATION 1: 3SM → DCF Integration
    # ========================================
    logger.info("\n[1/5] Activating 3SM → DCF Integration...")
    
    # Find the FCFF forecast building section (needs to check for 3SM first)
    fcff_pattern = r'(# Build FCFF forecast from cash flow data\n\s+cf_statements = financial_data\.get\(\'cash_flow\', \[\]\))'
    
    replacement = """# ACTIVATION: Use 3SM FCFF if available, else build manually
                # Check if Three Statement Model was run and has FCFF
                if three_statement_result and hasattr(three_statement_result, 'fcf_forecast') and three_statement_result.fcf_forecast:
                    fcff_forecast = three_statement_result.fcf_forecast
                    logger.info(f"   ✅ Using FCFF from 3-Statement Model ({len(fcff_forecast)} periods)")
                else:
                    # Fallback: Build FCFF forecast from cash flow data
                    cf_statements = financial_data.get('cash_flow', [])"""
    
    if re.search(fcff_pattern, orch_content):
        orch_content = re.sub(fcff_pattern, replacement, orch_content)
        logger.success("   ✓ 3SM → DCF integration activated")
    else:
        logger.warning("   ⚠ Could not find FCFF forecast section - may need manual edit")
    
    # ========================================
    # ACTIVATION 2: Monte Carlo Simulation
    # ========================================
    logger.info("\n[2/5] Activating Monte Carlo Simulation...")
    
    # Find where DCF completes successfully and add Monte Carlo
    monte_carlo_code = """
                # ACTIVATION: Monte Carlo Simulation for uncertainty quantification
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
                            simulations=10000,
                            random_seed=42  # For reproducibility
                        )
                        
                        # Store Monte Carlo results with DCF
                        if not hasattr(dcf_result, 'monte_carlo'):
                            dcf_result.monte_carlo = mc_results
                        
                        logger.success(f"   ✅ Monte Carlo: Mean=${mc_results['mean']:.2f}, "
                                      f"P10-P90: ${mc_results['p10']:.2f}-${mc_results['p90']:.2f}, "
                                      f"Simulations: {mc_results['simulations']:,}")
                    except Exception as e:
                        logger.warning(f"   ⚠ Monte Carlo simulation failed: {e}")
                        import traceback
                        logger.debug(traceback.format_exc())
"""
    
    # Insert after the DCF success log
    dcf_success_pattern = r'(logger\.success\(f"   ✅ DCF: \$\{dcf_result\.value_per_share:.2f\}/share \(WACC: \{dcf_result\.wacc:.2%\}\)"\)\n)'
    if re.search(dcf_success_pattern, orch_content):
        orch_content = re.sub(dcf_success_pattern, r'\1' + monte_carlo_code, orch_content)
        logger.success("   ✓ Monte Carlo activation added after DCF")
    else:
        logger.warning("   ⚠ Could not find DCF success log - may need manual edit")
    
    # ========================================
    # ACTIVATION 3: LBO Sensitivity Analysis
    # ========================================
    logger.info("\n[3/5] Activating LBO Sensitivity Analysis...")
    
    lbo_sensitivity_code = """
                # ACTIVATION: LBO Sensitivity Analysis
                if run_lbo and lbo_result:
                    logger.info("   → Running LBO sensitivity analysis...")
                    try:
                        lbo_sensitivity = self.lbo_engine.sensitivity_analysis(
                            base_inputs=lbo_inputs,
                            exit_multiple_range=(8.0, 14.0),  # 8x to 14x exit multiples
                            ebitda_range=(0.85, 1.15),  # 85% to 115% of base EBITDA
                            steps=5
                        )
                        
                        # Store sensitivity with LBO result
                        if not hasattr(lbo_result, 'sensitivity'):
                            lbo_result.sensitivity = lbo_sensitivity
                        
                        logger.success(f"   ✅ LBO Sensitivity: Exit multiples 8x-14x analyzed")
                    except Exception as e:
                        logger.warning(f"   ⚠ LBO sensitivity failed: {e}")
"""
    
    # Insert after LBO success log
    lbo_success_pattern = r'(logger\.success\(f"   ✅ LBO: IRR=\{lbo_result\.equity_irr:.1%\}, MoIC=\{lbo_result\.equity_moic:.2f\}x"\)\n)'
    if re.search(lbo_success_pattern, orch_content):
        orch_content = re.sub(lbo_success_pattern, r'\1' + lbo_sensitivity_code, orch_content)
        logger.success("   ✓ LBO Sensitivity activation added after LBO")
    else:
        logger.warning("   ⚠ Could not find LBO success log - may need manual edit")
    
    # ========================================  
    # ACTIVATION 4: Merger Sensitivity Analysis
    # ========================================
    logger.info("\n[4/5] Activating Merger Sensitivity Analysis...")
    
    merger_sensitivity_code = """
                    # ACTIVATION: Merger Sensitivity Analysis
                    if run_merger and merger_result:
                        logger.info("   → Running merger sensitivity analysis...")
                        try:
                            merger_sensitivity = merger_model.sensitivity_analysis(
                                base_inputs=merger_inputs,
                                premium_range=(0.20, 0.40),  # 20% to 40% premium
                                stock_consideration_range=(0.0, 1.0),  # 0% to 100% stock
                                steps=5
                            )
                            
                            # Store sensitivity with merger result
                            if not hasattr(merger_result, 'sensitivity'):
                                merger_result.sensitivity = merger_sensitivity
                            
                            logger.success(f"   ✅ Merger Sensitivity: Premium 20%-40%, Stock 0%-100% analyzed")
                        except Exception as e:
                            logger.warning(f"   ⚠ Merger sensitivity failed: {e}")
"""
    
    # Insert after merger success log
    merger_success_pattern = r'(logger\.success\(f"   ✅ Merger: \{merger_result\.accretion_dilution_pct:\+\.1%\} EPS impact \(\{\'ACCRETIVE\' if merger_result\.is_accretive else \'DILUTIVE\'\}\)"\)\n)'
    if re.search(merger_success_pattern, orch_content):
        # Need to add proper indentation
        indented_code = merger_sensitivity_code
        orch_content = re.sub(merger_success_pattern, r'\1' + indented_code, orch_content)
        logger.success("   ✓ Merger Sensitivity activation added after Merger")
    else:
        logger.warning("   ⚠ Could not find Merger success log - may need manual edit")
    
    # ========================================
    # ACTIVATION 5: Individual DD Risk Storage
    # ========================================
    logger.info("\n[5/5] Activating Individual DD Risk Storage...")
    
    dd_risk_storage_code = """
            # ACTIVATION: Store individual DD risk cards for granular AI queries
            if result.due_diligence:
                logger.info("   → Storing individual DD risk cards for AI queries...")
                risk_count = 0
                
                for category, risks in result.due_diligence.items():
                    for risk in risks:
                        # Store each risk card individually in memory
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
                                'subcategory': risk.subcategory,
                                'session_id': comprehensive_memory.session_id
                            }
                        )
                        risk_count += 1
                
                logger.success(f"   ✓ Stored {risk_count} individual risk cards for AI retrieval")
                logger.info(f"   ✓ AI can now query by: ticker, category, severity, subcategory")
"""
    
    # Insert after comprehensive memory storage
    memory_store_pattern = r'(success = self\.modeling\.memory\.store_analysis\(comprehensive_memory\)\n)'
    if re.search(memory_store_pattern, orch_content):
        orch_content = re.sub(memory_store_pattern, r'\1' + dd_risk_storage_code, orch_content)
        logger.success("   ✓ Individual DD risk storage activated")
    else:
        logger.warning("   ⚠ Could not find memory storage location - may need manual edit")
    
    # Write back if changes were made
    if orch_content != original_content:
        logger.info("\n" + "="*80)
        logger.info("WRITING ACTIVATED ORCHESTRATOR")
        logger.info("="*80)
        
        with open(orch_path, 'w', encoding='utf-8') as f:
            f.write(orch_content)
        
        logger.success(f"✅ Orchestrator updated: {orch_path}")
        logger.success("✅ All 5 dormant features activated:")
        logger.success("   1. 3SM → DCF FCFF integration")
        logger.success("   2. Monte Carlo simulation (10,000 sims)")
        logger.success("   3. LBO sensitivity analysis")
        logger.success("   4. Merger sensitivity analysis")
        logger.success("   5. Individual DD risk storage")
        
        return True
    else:
        logger.warning("⚠ No changes made - patterns may not have matched")
        logger.warning("Manual editing may be required")
        return False


if __name__ == "__main__":
    logger.info("Dormant Features Activation Script")
    logger.info("This script activates advanced features that exist but aren't called")
    logger.info("")
    
    success = activate_features()
    
    if success:
        print("\n" + "="*80)
        print("ACTIVATION COMPLETE")
        print("="*80)
        print("\nNext steps:")
        print("1. Test the activation: python test_complete_integration.py")
        print("2. Run analysis to verify Monte Carlo appears")
        print("3. Check Excel for Monte_Carlo tab")
        print("4. Test AI queries: 'What are high severity financial risks?'")
        print("="*80)
    else:
        print("\n⚠ Activation incomplete - review logs above")
        print("Some patterns may not have matched - manual editing required")
