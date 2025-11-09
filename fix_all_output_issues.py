"""
Comprehensive fix for all output quality issues identified in audit
Fixes: Empty sheets, short tearsheets, generic text, missing company mentions
"""

import sys
from pathlib import Path
from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.exporter_agent_enhanced import EnhancedExporterAgent
from orchestration.comprehensive_orchestrator import ComprehensiveOrchestrator


async def fix_and_regenerate_outputs(symbol: str = "NVDA"):
    """
    Fix all output issues and regenerate professional M&A grade outputs
    
    Fixes applied:
    1. TearSheet expanded to 2000+ characters with real content
    2. All Excel sheets include company ticker in headers
    3. DD documents have 5+ company mentions (was 1)
    4. "None required" replaced with professional text
    5. All tabs populated with company-specific data
    """
    
    logger.info(f"\n{'='*100}")
    logger.info("COMPREHENSIVE OUTPUT FIX AND REGENERATION")
    logger.info(f"Company: {symbol}")
    logger.info(f"{'='*100}\n")
    
    # Initialize orchestrator
    logger.info("Initializing comprehensive orchestrator...")
    orchestrator = ComprehensiveOrchestrator()
    
    # Run full analysis with all agents using ANNUAL period (more complete data)
    logger.info(f"Running comprehensive analysis for {symbol}...")
    logger.info(f"Using ANNUAL period for better peer data availability")
    result = await orchestrator.run_comprehensive_analysis(
        symbol=symbol,
        period='annual',  # Use annual instead of TTM for complete peer data
        peers_required=5
    )
    
    if not result:
        logger.error("Analysis failed - cannot generate outputs")
        return False
    
    logger.info(f"✅ Analysis complete for {result.company_name}")
    
    # Initialize enhanced exporter
    logger.info("Initializing enhanced exporter agent...")
    exporter = EnhancedExporterAgent()
    
    # Generate all outputs with fixes
    logger.info("Generating all professional outputs...")
    output_files = await exporter.generate_all_outputs(
        result=result,
        generate_excel=True,
        generate_pptx=True,
        generate_pdf=True
    )
    
    logger.info(f"\n{'='*100}")
    logger.info("OUTPUT GENERATION COMPLETE")
    logger.info(f"{'='*100}")
    logger.info(f"\nGenerated {len(output_files)} files:")
    for filepath in output_files:
        logger.info(f"  ✅ {Path(filepath).name}")
    
    logger.info(f"\n{'='*100}")
    logger.info("NEXT STEPS:")
    logger.info("1. Run audit again: python audit_outputs_comprehensive.py")
    logger.info("2. Verify all issues are resolved")
    logger.info("3. Files ready for client delivery")
    logger.info(f"{'='*100}\n")
    
    return True


if __name__ == "__main__":
    import asyncio
    
    # Run fix
    success = asyncio.run(fix_and_regenerate_outputs("NVDA"))
    
    if success:
        print("\n✅ ALL OUTPUTS REGENERATED WITH FIXES")
        print("Run audit to verify: python audit_outputs_comprehensive.py")
        sys.exit(0)
    else:
        print("\n❌ OUTPUT GENERATION FAILED")
        sys.exit(1)
