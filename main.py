"""
FMNA - Financial M&A Analytics Platform
Main entry point
"""

import sys
from pathlib import Path
from loguru import logger
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import get_settings
from ingestion import FMPClient, SECClient
from utils import LLMClient


def setup_logging():
    """Configure logging"""
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    logger.add(
        "logs/fmna_{time}.log",
        rotation="500 MB",
        retention="10 days",
        level="DEBUG"
    )


def demo_fmp_integration(symbol: str = "AAPL"):
    """
    Demonstrate FMP API integration
    
    Args:
        symbol: Stock ticker symbol
    """
    logger.info(f"Running FMP demo for {symbol}")
    
    try:
        fmp = FMPClient()
        
        # Get company profile
        logger.info("Fetching company profile...")
        profile = fmp.get_company_profile(symbol)
        if profile:
            logger.info(f"Company: {profile.legal_name}")
            logger.info(f"Sector: {profile.sector}")
            logger.info(f"Industry: {profile.industry}")
        
        # Get financial statements
        logger.info("Fetching financial statements...")
        financials = fmp.get_all_financial_data(symbol, period="annual", limit=3)
        
        if financials['income_statement']:
            logger.info(f"Retrieved {len(financials['income_statement'])} years of income statements")
        if financials['balance_sheet']:
            logger.info(f"Retrieved {len(financials['balance_sheet'])} years of balance sheets")
        if financials['cash_flow']:
            logger.info(f"Retrieved {len(financials['cash_flow'])} years of cash flow statements")
        
        logger.success("FMP demo completed successfully")
        return financials
        
    except Exception as e:
        logger.error(f"FMP demo failed: {str(e)}")
        return None


def demo_sec_integration(ticker: str = "AAPL"):
    """
    Demonstrate SEC EDGAR integration
    
    Args:
        ticker: Stock ticker symbol
    """
    logger.info(f"Running SEC demo for {ticker}")
    
    try:
        sec = SECClient(email="demo@fmna.local")
        
        # Get CIK
        logger.info("Fetching CIK...")
        cik = sec.get_company_cik(ticker)
        if cik:
            logger.info(f"CIK: {cik}")
        
        # Get latest 10-K
        logger.info("Fetching latest 10-K filing...")
        filing = sec.get_latest_filing(ticker, filing_type="10-K")
        
        if filing:
            logger.info(f"Filing Date: {filing.filing_date}")
            logger.info(f"Accession Number: {filing.accession_number}")
            logger.info(f"Items Extracted: {filing.items_extracted}")
            logger.success("SEC demo completed successfully")
            return filing
        else:
            logger.warning("No filing retrieved")
            return None
        
    except Exception as e:
        logger.error(f"SEC demo failed: {str(e)}")
        return None


def demo_llm_analysis(text: str):
    """
    Demonstrate LLM analysis capabilities
    
    Args:
        text: Text to analyze
    """
    logger.info("Running LLM analysis demo")
    
    try:
        llm = LLMClient()
        
        # Analyze MD&A (using sample text if needed)
        logger.info("Analyzing text with LLM...")
        analysis = llm.analyze_mda(text[:5000])  # Use first 5000 chars
        
        logger.info("LLM Analysis Results:")
        logger.info(f"{analysis}")
        
        logger.success("LLM demo completed successfully")
        return analysis
        
    except Exception as e:
        logger.error(f"LLM demo failed: {str(e)}")
        return None


def run_full_demo(symbol: str = "AAPL"):
    """
    Run complete demo of all integrations
    
    Args:
        symbol: Stock ticker symbol
    """
    logger.info("="*80)
    logger.info(f"FMNA Platform Demo - Analyzing {symbol}")
    logger.info("="*80)
    
    # 1. FMP Integration
    logger.info("\n[1/3] Financial Modeling Prep Integration")
    logger.info("-"*80)
    financials = demo_fmp_integration(symbol)
    
    # 2. SEC Integration
    logger.info("\n[2/3] SEC EDGAR Integration")
    logger.info("-"*80)
    filing = demo_sec_integration(symbol)
    
    # 3. LLM Analysis
    if filing and filing.full_text:
        logger.info("\n[3/3] LLM Analysis")
        logger.info("-"*80)
        analysis = demo_llm_analysis(filing.full_text)
    else:
        logger.warning("Skipping LLM analysis - no filing text available")
        analysis = None
    
    logger.info("\n" + "="*80)
    logger.success("FMNA Platform Demo Completed")
    logger.info("="*80)
    
    return {
        'financials': financials,
        'filing': filing,
        'analysis': analysis
    }


def main():
    """Main entry point"""
    setup_logging()
    
    logger.info("FMNA - Financial M&A Analytics Platform")
    logger.info("Version: 0.1.0")
    logger.info("")
    
    try:
        # Load settings
        settings = get_settings()
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Data directory: {settings.data_dir}")
        
        # Check if running in demo mode
        import argparse
        parser = argparse.ArgumentParser(description="FMNA Platform")
        parser.add_argument('--demo', action='store_true', help='Run demo mode')
        parser.add_argument('--symbol', type=str, default='AAPL', help='Stock symbol for demo')
        args = parser.parse_args()
        
        if args.demo:
            run_full_demo(args.symbol)
        else:
            logger.info("Use --demo flag to run demonstration mode")
            logger.info("Example: python main.py --demo --symbol AAPL")
            
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
