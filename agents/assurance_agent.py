"""
Assurance Agent
Quality control: tie-outs, triangle tests, citation validation, balance sheet checks
"""

from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
from loguru import logger

from storage.duckdb_adapter import DuckDBAdapter
from utils.llm_client import LLMClient
from engines import DCFResult, CCAResult, LBOResult


class AssuranceAgent:
    """
    Assurance Agent - quality control and validation
    
    Responsibilities:
    - Balance sheet tie-outs
    - Triangle tests (DCF vs CCA vs Precedent)
    - Cash flow waterfall validation
    - Citation verification
    - Source reference linking
    """
    
    def __init__(self):
        """Initialize assurance agent"""
        self.db = DuckDBAdapter()
        self.llm = LLMClient()
        
        logger.info("Assurance Agent initialized")
    
    def validate_balance_sheet(
        self,
        balance_sheet: pd.DataFrame
    ) -> Tuple[bool, List[str]]:
        """
        Validate balance sheet equations
        
        Args:
            balance_sheet: Balance sheet DataFrame
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        logger.info("Validating balance sheet equations")
        
        errors = []
        
        for idx, row in balance_sheet.iterrows():
            # Assets = Liabilities + Equity
            assets = row.get('Total_Assets', 0)
            liabilities = row.get('Total_Liabilities', 0)
            equity = row.get('Equity', 0)
            
            diff = abs(assets - (liabilities + equity))
            
            if diff > 1.0:  # Allow $1 rounding
                errors.append(f"Year {row.get('Year', idx)}: Assets don't balance by ${diff:,.2f}")
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info("✓ Balance sheet validation passed")
        else:
            logger.warning(f"✗ Balance sheet validation failed: {len(errors)} errors")
        
        return is_valid, errors
    
    def validate_cash_flow(
        self,
        cash_flow: pd.DataFrame,
        balance_sheet: pd.DataFrame
    ) -> Tuple[bool, List[str]]:
        """
        Validate cash flow reconciles with balance sheet
        
        Args:
            cash_flow: Cash flow statement DataFrame
            balance_sheet: Balance sheet DataFrame
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        logger.info("Validating cash flow waterfall")
        
        errors = []
        
        for idx in range(len(cash_flow)):
            # CFO + CFI + CFF = Change in Cash
            cfo = cash_flow.iloc[idx].get('CFO', 0)
            cfi = cash_flow.iloc[idx].get('CFI', 0)
            cff = cash_flow.iloc[idx].get('CFF', 0)
            
            total_cf = cfo + cfi + cff
            delta_cash = cash_flow.iloc[idx].get('Delta_Cash', 0)
            
            diff = abs(total_cf - delta_cash)
            
            if diff > 1.0:
                errors.append(f"Year {idx+1}: Cash flow doesn't reconcile by ${diff:,.2f}")
            
            # Reconcile with balance sheet change in cash
            if idx > 0:
                bs_delta_cash = balance_sheet.iloc[idx]['Cash'] - balance_sheet.iloc[idx-1]['Cash']
                diff_bs = abs(delta_cash - bs_delta_cash)
                
                if diff_bs > 1.0:
                    errors.append(f"Year {idx+1}: Cash flow doesn't match balance sheet by ${diff_bs:,.2f}")
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info("✓ Cash flow validation passed")
        else:
            logger.warning(f"✗ Cash flow validation failed: {len(errors)} errors")
        
        return is_valid, errors
    
    def triangle_test(
        self,
        dcf_value: float,
        cca_value: float,
        precedent_value: Optional[float] = None,
        tolerance: float = 0.20
    ) -> Dict[str, Any]:
        """
        Triangle test: validate valuations are reasonably consistent
        
        Args:
            dcf_value: DCF value per share
            cca_value: CCA value per share
            precedent_value: Precedent transaction value (optional)
            tolerance: Acceptable variance (default 20%)
            
        Returns:
            Dictionary with test results
        """
        logger.info("Running triangle test")
        
        valuations = [('DCF', dcf_value), ('CCA', cca_value)]
        if precedent_value:
            valuations.append(('Precedent', precedent_value))
        
        values = [v[1] for v in valuations]
        mean_value = sum(values) / len(values)
        
        # Check each vs mean
        variances = []
        for name, value in valuations:
            variance = abs(value - mean_value) / mean_value
            variances.append((name, variance))
        
        # Determine if test passes
        max_variance = max(v[1] for v in variances)
        test_passed = max_variance <= tolerance
        
        result = {
            'test_passed': test_passed,
            'mean_value': mean_value,
            'max_variance': max_variance,
            'tolerance': tolerance,
            'valuations': dict(valuations),
            'variances': dict(variances)
        }
        
        if test_passed:
            logger.info(f"✓ Triangle test passed - Max variance: {max_variance:.1%}")
        else:
            logger.warning(f"✗ Triangle test failed - Max variance: {max_variance:.1%} > {tolerance:.1%}")
        
        return result
    
    def verify_citations(
        self,
        metric_name: str,
        metric_value: float,
        source_ref: str,
        filing_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Verify metric can be cited to source
        
        Args:
            metric_name: Name of metric
            metric_value: Value to verify
            source_ref: Source reference (e.g., "10-K-2023, Item 8")
            filing_data: Filing data for verification
            
        Returns:
            True if citation verified
        """
        logger.debug(f"Verifying citation: {metric_name} = {metric_value} from {source_ref}")
        
        # In production, would:
        # 1. Parse source_ref to get filing and page
        # 2. Extract metric from filing
        # 3. Compare values
        
        # For now, simple check
        if source_ref and source_ref != "":
            logger.debug(f"✓ Citation exists: {source_ref}")
            return True
        else:
            logger.warning(f"✗ Missing citation for {metric_name}")
            return False
    
    def run_full_qa(
        self,
        symbol: str,
        balance_sheet: pd.DataFrame,
        cash_flow: pd.DataFrame,
        dcf_result: Optional[DCFResult] = None,
        cca_result: Optional[CCAResult] = None,
        precedent_value: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Run full quality assurance checks
        
        Args:
            symbol: Company symbol
            balance_sheet: Balance sheet projections
            cash_flow: Cash flow projections
            dcf_result: DCF valuation result
            cca_result: CCA valuation result
            precedent_value: Precedent transaction value
            
        Returns:
            QA results dictionary
        """
        logger.info(f"Running full QA for {symbol}")
        
        qa_results = {
            'symbol': symbol,
            'timestamp': datetime.utcnow().isoformat(),
            'checks_passed': 0,
            'checks_failed': 0,
            'errors': []
        }
        
        # 1. Balance sheet validation
        bs_valid, bs_errors = self.validate_balance_sheet(balance_sheet)
        if bs_valid:
            qa_results['checks_passed'] += 1
        else:
            qa_results['checks_failed'] += 1
            qa_results['errors'].extend(bs_errors)
        
        # 2. Cash flow validation
        cf_valid, cf_errors = self.validate_cash_flow(cash_flow, balance_sheet)
        if cf_valid:
            qa_results['checks_passed'] += 1
        else:
            qa_results['checks_failed'] += 1
            qa_results['errors'].extend(cf_errors)
        
        # 3. Triangle test
        if dcf_result and cca_result:
            triangle_result = self.triangle_test(
                dcf_result.value_per_share,
                cca_result.value_per_share_ebitda,
                precedent_value
            )
            
            if triangle_result['test_passed']:
                qa_results['checks_passed'] += 1
            else:
                qa_results['checks_failed'] += 1
                qa_results['errors'].append(f"Triangle test failed: variance {triangle_result['max_variance']:.1%}")
            
            qa_results['triangle_test'] = triangle_result
        
        # 4. Overall status
        qa_results['status'] = 'PASSED' if qa_results['checks_failed'] == 0 else 'FAILED'
        
        logger.info(f"QA Complete - {qa_results['checks_passed']} passed, {qa_results['checks_failed']} failed")
        
        return qa_results
    
    def close(self):
        """Clean up resources"""
        self.db.close()
        logger.info("Assurance agent closed")


# Example usage
if __name__ == "__main__":
    from engines.three_statement_model import ThreeStatementModel, DriverInputs
    
    # Initialize agent
    agent = AssuranceAgent()
    
    print("\n" + "="*70)
    print("ASSURANCE AGENT - QUALITY CONTROL")
    print("="*70)
    
    # Build sample 3-statement model
    model = ThreeStatementModel()
    drivers = DriverInputs(
        base_revenue=1_000_000_000,
        revenue_growth_rates=[0.00, 0.10, 0.12, 0.10, 0.08],
        cogs_pct_revenue=[0.60] * 5,
        sga_pct_revenue=[0.20] * 5,
        da_pct_revenue=[0.03] * 5,
        ar_days=[45] * 5,
        inventory_days=[60] * 5,
        ap_days=[50] * 5,
        capex_pct_revenue=[0.04] * 5,
        base_debt=500_000_000,
        interest_rate=0.05,
        mandatory_debt_payment=50_000_000,
        tax_rate=0.21,
        sbc_pct_revenue=[0.02] * 5
    )
    
    result = model.build_three_statement_model(drivers, years=5)
    
    # Run QA
    qa_results = agent.run_full_qa(
        symbol="TEST",
        balance_sheet=result.balance_sheet,
        cash_flow=result.cash_flow_statement
    )
    
    print(f"\nQA Results:")
    print(f"  Status: {qa_results['status']}")
    print(f"  Checks Passed: {qa_results['checks_passed']}")
    print(f"  Checks Failed: {qa_results['checks_failed']}")
    
    if qa_results['errors']:
        print(f"\n  Errors:")
        for error in qa_results['errors']:
            print(f"    - {error}")
    
    agent.close()
