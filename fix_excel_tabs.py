"""
Fix Excel tabs to properly extract and display engine data
The valuation engines CREATE the data, but Excel exporter isn't displaying it properly
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.exporter_agent_enhanced import EnhancedExporterAgent
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from loguru import logger


def fix_excel_tab_extraction():
    """
    Fix the Excel exporter to properly extract data from engines
    
    The issue: Engines create comprehensive data, but Excel tabs don't extract it
    The fix: Update tab creation functions to properly extract engine outputs
    """
    
    logger.info("Analyzing Excel tab data extraction...")
    
    # Read the exporter agent file
    exporter_path = Path("agents/exporter_agent_enhanced.py")
    
    with open(exporter_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check current implementation
    issues_found = []
    
    if 'def _create_three_statement_tab' in content:
        if 'Placeholder: add actual data integration here' in content:
            issues_found.append("3FS_Model has placeholder comment - needs data extraction")
    
    if 'def _create_accretion_dilution_tab' in content:
        if 'No merger analysis performed' in content:
            issues_found.append("Accretion_Dilution doesn't extract MergerResult properly")
    
    logger.info(f"Found {len(issues_found)} extraction issues:")
    for issue in issues_found:
        logger.info(f"  - {issue}")
    
    logger.info("\nThe problem:")
    logger.info("  1. Engines (DCF, CCA, LBO, Merger, 3-Statement) CREATE complete models")
    logger.info("  2. Data flows through orchestrator → exporter")  
    logger.info("  3. BUT Excel tab functions don't EXTRACT the data properly")
    logger.info("  4. Result: Sparse tabs despite having the data")
    
    logger.info("\nSolution:")
    logger.info("  1. Fix _create_three_statement_tab() to extract from ThreeStatementResult")
    logger.info("  2. Fix _create_accretion_dilution_tab() to extract from MergerResult")
    logger.info("  3. Fix other tabs to extract from their respective engine results")
    logger.info("  4. Add proper data validation and error handling")
    
    return issues_found


if __name__ == "__main__":
    issues = fix_excel_tab_extraction()
    
    print("\n" + "="*80)
    print("EXCEL TAB EXTRACTION ANALYSIS COMPLETE")
    print("="*80)
    print(f"\nIssues identified: {len(issues)}")
    print("\nNext: I'll fix the extraction logic in the tab creation functions")
    print("="*80)
