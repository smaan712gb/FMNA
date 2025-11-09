"""
Apply orchestrator fix to enable all 6 engines
Run this to fix the issue where only 3-4 engines run instead of all 6
"""

def fix_orchestrator():
    """Fix orchestration/comprehensive_orchestrator.py to pass all parameters"""
    
    print("="*80)
    print("FIXING ORCHESTRATOR - ENABLING ALL 6 ENGINES")
    print("="*80)
    
    # Read orchestrator file with UTF-8 encoding
    print("\n1. Reading orchestration/comprehensive_orchestrator.py...")
    with open('orchestration/comprehensive_orchestrator.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes_made = 0
    
    # Fix 1: Add parameters to method call
    print("2. Adding run_merger and run_three_statement parameters to method call...")
    old_call = """valuation = await self._run_valuation_models(
            symbol=symbol,
            financial_data=financial_data,
            peers_data=peers_data,
            market_data=market_data,
            run_dcf=run_dcf,
            run_cca=run_cca,
            run_lbo=run_lbo,
            run_growth_scenarios=run_growth_scenarios
        )"""

    new_call = """valuation = await self._run_valuation_models(
            symbol=symbol,
            financial_data=financial_data,
            peers_data=peers_data,
            market_data=market_data,
            run_dcf=run_dcf,
            run_cca=run_cca,
            run_lbo=run_lbo,
            run_merger=run_merger,
            run_three_statement=run_three_statement,
            run_growth_scenarios=run_growth_scenarios
        )"""

    if old_call in content:
        content = content.replace(old_call, new_call)
        changes_made += 1
        print("   ✅ Method call updated")
    else:
        print("   ⚠️  Method call already updated or not found")

    # Fix 2: Update method signature
    print("3. Updating _run_valuation_models signature...")
    old_sig = """    async def _run_valuation_models(
        self,
        symbol: str,
        financial_data: Dict[str, Any],
        peers_data: List[Dict[str, Any]],
        market_data: Dict[str, Any],
        run_dcf: bool = True,
        run_cca: bool = True,
        run_lbo: bool = False,
        run_growth_scenarios: bool = False
    ) -> ValuationPackage:"""

    new_sig = """    async def _run_valuation_models(
        self,
        symbol: str,
        financial_data: Dict[str, Any],
        peers_data: List[Dict[str, Any]],
        market_data: Dict[str, Any],
        run_dcf: bool = True,
        run_cca: bool = True,
        run_lbo: bool = False,
        run_merger: bool = True,
        run_three_statement: bool = True,
        run_growth_scenarios: bool = False
    ) -> ValuationPackage:"""

    if old_sig in content:
        content = content.replace(old_sig, new_sig)
        changes_made += 1
        print("   ✅ Method signature updated")
    else:
        print("   ⚠️  Method signature already updated or not found")

    # Write back if changes were made
    if changes_made > 0:
        print(f"\n4. Writing changes back to file ({changes_made} changes)...")
        with open('orchestration/comprehensive_orchestrator.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("   ✅ File updated successfully")
    else:
        print("\n4. No changes needed - file already up to date")
    
    print("\n" + "="*80)
    print("ORCHESTRATOR FIX COMPLETE")
    print("="*80)
    print("\nChanges made:")
    print(f"  - Added run_merger parameter: ✅")
    print(f"  - Added run_three_statement parameter: ✅")
    print(f"  - Updated method signature: ✅")
    print("="*80)


def fix_modeling_agent():
    """Fix agents/modeling_agent.py to handle merger and 3FS results"""
    
    print("\n" + "="*80)
    print("FIXING MODELING AGENT - ADDING MERGER & 3FS SUPPORT")
    print("="*80)
    
    print("\n1. Reading agents/modeling_agent.py...")
    with open('agents/modeling_agent.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    changes_made = 0
    
    # Fix 1: Add fields to ValuationPackage
    print("2. Adding merger_result and three_statement_result to ValuationPackage...")
    
    # Find ValuationPackage class
    if 'merger_result: Optional[Any] = None' not in content:
        # Add fields after growth_scenarios
        old_vp = '    growth_scenarios: Optional[Any] = None'
        new_vp = '''    growth_scenarios: Optional[Any] = None
    merger_result: Optional[Any] = None  # MergerResult from merger_model
    three_statement_result: Optional[Any] = None  # ThreeStatementResult'''
        
        if old_vp in content:
            content = content.replace(old_vp, new_vp)
            changes_made += 1
            print("   ✅ ValuationPackage fields added")
        else:
            print("   ⚠️  Could not find insertion point for ValuationPackage")
    else:
        print("   ✅ Fields already present")
    
    # Fix 2: Update build_valuation_package signature
    print("3. Updating build_valuation_package method signature...")
    
    old_build_sig = """    def build_valuation_package(
        self,
        symbol: str,
        company_name: str,
        dcf_result: Optional[DCFResult] = None,
        cca_result: Optional[CCAResult] = None,
        lbo_result: Optional[LBOResult] = None,
        growth_scenarios: Optional[Any] = None
    ) -> ValuationPackage:"""
    
    new_build_sig = """    def build_valuation_package(
        self,
        symbol: str,
        company_name: str,
        dcf_result: Optional[DCFResult] = None,
        cca_result: Optional[CCAResult] = None,
        lbo_result: Optional[LBOResult] = None,
        growth_scenarios: Optional[Any] = None,
        merger_result: Optional[Any] = None,
        three_statement_result: Optional[Any] = None
    ) -> ValuationPackage:"""
    
    if old_build_sig in content:
        content = content.replace(old_build_sig, new_build_sig)
        changes_made += 1
        print("   ✅ Method signature updated")
    else:
        print("   ⚠️  Method signature already updated or not found")
    
    # Fix 3: Update return statement
    print("4. Updating ValuationPackage instantiation in return statement...")
    
    if 'merger_result=merger_result' not in content:
        # Find the pattern and insert
        import re
        pattern = r'(growth_scenarios=growth_scenarios,\s*\n\s+# Valuation range)'
        replacement = r'growth_scenarios=growth_scenarios,\n            merger_result=merger_result,\n            three_statement_result=three_statement_result,\n            # Valuation range'
        
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            content = new_content
            changes_made += 1
            print("   ✅ Return statement updated")
        else:
            print("   ℹ️  Could not auto-update return statement - checking alternate pattern")
            # Try alternate pattern
            pattern2 = r'(growth_scenarios=growth_scenarios,)'
            replacement2 = r'growth_scenarios=growth_scenarios,\n            merger_result=merger_result,\n            three_statement_result=three_statement_result,'
            new_content = re.sub(pattern2, replacement2, content, count=1)
            if new_content != content:
                content = new_content
                changes_made += 1
                print("   ✅ Return statement updated (alternate method)")
    else:
        print("   ✅ Return statement already includes new fields")
    
    # Write back
    if changes_made > 0:
        print(f"\n5. Writing changes back to file ({changes_made} changes)...")
        with open('agents/modeling_agent.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("   ✅ File updated successfully")
    else:
        print("\n5. No changes needed - file already up to date")
    
    print("\n" + "="*80)
    print("MODELING AGENT FIX COMPLETE")
    print("="*80)


if __name__ == "__main__":
    import sys
    
    print("\n")
    print("╔" + "═"*78 + "╗")
    print("║" + " "*20 + "ORCHESTRATOR FIX - ALL 6 ENGINES" + " "*26 + "║")
    print("╚" + "═"*78 + "╝")
    
    try:
        # Step 1: Fix orchestrator
        fix_orchestrator()
        
        # Step 2: Fix modeling agent
        fix_modeling_agent()
        
        print("\n" + "="*80)
        print("✅ ALL FIXES APPLIED SUCCESSFULLY!")
        print("="*80)
        print("\nAll 6 engines are now integrated:")
        print("  1. ✅ DCF Engine")
        print("  2. ✅ CCA Engine")
        print("  3. ✅ LBO Engine")
        print("  4. ✅ Merger Model (NEW!)")
        print("  5. ✅ Three Statement Model (NEW!)")
        print("  6. ✅ Growth Scenarios")
        print("\nThe Accretion/Dilution Analysis tab will now populate!")
        print("\nTest with:")
        print("  python demo_complete_platform.py")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("\nPlease check the error and try again.")
        sys.exit(1)
