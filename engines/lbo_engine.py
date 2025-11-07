"""
LBO (Leveraged Buyout) Engine
Complete LBO model with sources & uses, debt tranches, returns analysis
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from decimal import Decimal
import numpy as np
import pandas as pd
from loguru import logger


@dataclass
class DebtTranche:
    """Debt tranche specification"""
    name: str
    amount: float
    interest_rate: float
    term_years: int
    amortization_type: str  # "straight_line", "bullet", "custom"
    pik_toggle: bool = False  # Payment-in-kind option
    mandatory_prepayment: float = 0.0  # % of excess cash flow


@dataclass
class LBOInputs:
    """LBO model inputs"""
    # Purchase
    purchase_enterprise_value: float
    purchase_equity_value: float
    transaction_fees: float  # % of EV
    financing_fees: float  # % of debt
    
    # Capital structure
    equity_contribution: float  # Sponsor equity
    rollover_equity: float  # Management rollover
    debt_tranches: List[DebtTranche]
    
    # Exit
    exit_year: int
    exit_ebitda: float
    exit_multiple: float  # EV/EBITDA
    
    # Operating assumptions
    revenue_growth_rates: List[float]  # Annual growth rates
    ebitda_margins: List[float]  # Annual margins
    capex_pct_revenue: float
    nwc_pct_revenue: float
    tax_rate: float
    
    # Debt paydown
    excess_cash_sweep: float = 1.0  # 100% sweep by default


@dataclass
class LBOResult:
    """LBO analysis result"""
    # Returns
    equity_irr: float
    equity_moic: float  # Money-on-Money Multiple
    
    # Entry valuation
    entry_ev: float
    entry_equity: float
    total_uses: float
    total_sources: float
    
    # Exit valuation
    exit_ev: float
    exit_equity_value: float
    exit_total_debt: float
    
    # Cash flows
    annual_cash_flows: pd.DataFrame
    debt_schedule: pd.DataFrame
    
    # Sources & Uses
    sources_and_uses: pd.DataFrame
    
    # Valuation range per share
    min_value_per_share: float
    max_value_per_share: float
    
    # Sensitivity
    sensitivity_table: Optional[pd.DataFrame] = None


class LBOEngine:
    """LBO Valuation Engine"""
    
    def __init__(self):
        """Initialize LBO engine"""
        logger.info("LBO Engine initialized")
    
    def _calculate_irr(self, cash_flows: List[float], guess: float = 0.1) -> float:
        """
        Calculate Internal Rate of Return with professional-grade validation and MIRR fallback
        This is a skeptical implementation that validates results through multiple methods
        
        Args:
            cash_flows: List of cash flows (negative for outflows, positive for inflows)
            guess: Initial guess for IRR
            
        Returns:
            IRR as a decimal (e.g., 0.15 for 15%)
        """
        # Validation cascade - professional analyst approach
        
        # 1. Pre-flight checks
        if not cash_flows or len(cash_flows) < 2:
            logger.error("IRR: Insufficient cash flows")
            return 0.0
        
        # Check for sign changes (IRR requires at least one)
        sign_changes = sum(1 for i in range(len(cash_flows)-1) 
                          if cash_flows[i] * cash_flows[i+1] < 0)
        
        if sign_changes == 0:
            logger.warning("IRR: No sign changes in cash flows - IRR may not be meaningful")
            # Calculate simple ROI as fallback
            initial = abs(cash_flows[0])
            final = cash_flows[-1]
            if initial > 0:
                simple_return = (final / initial) ** (1 / (len(cash_flows) - 1)) - 1
                logger.info(f"Using simple geometric return: {simple_return:.2%}")
                return simple_return
            return 0.0
        
        if sign_changes > 1:
            logger.warning(f"IRR: Multiple sign changes ({sign_changes}) detected - multiple IRRs may exist, using MIRR instead")
            return self._calculate_mirr(cash_flows)
        
        def npv(rate, cash_flows):
            """Calculate NPV given a discount rate"""
            try:
                return sum(cf / (1 + rate) ** i for i, cf in enumerate(cash_flows))
            except (OverflowError, ZeroDivisionError):
                return float('inf')
        
        def npv_derivative(rate, cash_flows):
            """Calculate derivative of NPV with respect to rate"""
            try:
                return sum(-i * cf / (1 + rate) ** (i + 1) for i, cf in enumerate(cash_flows))
            except (OverflowError, ZeroDivisionError):
                return 0.0
        
        # 2. Try Newton's method with multiple starting points
        attempts = [guess, 0.05, 0.10, 0.15, 0.20, -0.05]
        best_result = None
        best_npv = float('inf')
        
        for starting_guess in attempts:
            rate = starting_guess
            max_iterations = 100
            tolerance = 1e-6
            converged = False
            
            for iteration in range(max_iterations):
                npv_value = npv(rate, cash_flows)
                
                # Check for convergence
                if abs(npv_value) < tolerance:
                    converged = True
                    if abs(npv_value) < abs(best_npv):
                        best_npv = npv_value
                        best_result = rate
                    break
                
                # Calculate next iteration
                derivative = npv_derivative(rate, cash_flows)
                if abs(derivative) < 1e-10:  # Avoid division by zero
                    break
                
                rate = rate - npv_value / derivative
                
                # Keep rate within reasonable bounds
                if rate < -0.99:
                    rate = -0.99
                elif rate > 10:
                    rate = 10
            
            if converged:
                break
        
        # 3. Validate result
        if best_result is not None:
            # Cross-validate with NPV check
            validation_npv = npv(best_result, cash_flows)
            if abs(validation_npv) < 0.01:  # NPV should be near zero
                logger.info(f"✓ IRR converged: {best_result:.4f} (NPV check: ${validation_npv:,.2f})")
                return best_result
            else:
                logger.warning(f"IRR convergence questionable - NPV at {best_result:.4f} is ${validation_npv:,.2f}")
        
        # 4. If Newton's method failed, try bisection as backup
        logger.info("Attempting bisection method as IRR fallback...")
        try:
            lower = -0.99
            upper = 10.0
            max_bisection_iterations = 100
            tolerance = 1e-6
            
            for _ in range(max_bisection_iterations):
                mid = (lower + upper) / 2
                npv_mid = npv(mid, cash_flows)
                
                if abs(npv_mid) < tolerance:
                    logger.info(f"✓ IRR found via bisection: {mid:.4f}")
                    return mid
                
                npv_lower = npv(lower, cash_flows)
                if (npv_lower * npv_mid) < 0:
                    upper = mid
                else:
                    lower = mid
                
                if abs(upper - lower) < 1e-6:
                    logger.info(f"✓ IRR approximated via bisection: {mid:.4f}")
                    return mid
        except Exception as e:
            logger.warning(f"Bisection method failed: {e}")
        
        # 5. Final fallback: Use MIRR (Modified IRR)
        logger.warning("Standard IRR methods inconclusive - using MIRR (Modified IRR)")
        return self._calculate_mirr(cash_flows)
    
    def _calculate_mirr(
        self, 
        cash_flows: List[float], 
        finance_rate: float = 0.10, 
        reinvest_rate: float = 0.10
    ) -> float:
        """
        Calculate Modified Internal Rate of Return (MIRR)
        More stable than IRR for non-conventional cash flows
        
        MIRR assumes:
        - Negative cash flows financed at finance_rate
        - Positive cash flows reinvested at reinvest_rate
        
        Args:
            cash_flows: List of cash flows
            finance_rate: Cost of capital for financing negative flows
            reinvest_rate: Reinvestment rate for positive flows
            
        Returns:
            MIRR as a decimal
        """
        n = len(cash_flows) - 1
        
        if n <= 0:
            return 0.0
        
        # Separate positive and negative flows
        negative_flows = [min(0, cf) for cf in cash_flows]
        positive_flows = [max(0, cf) for cf in cash_flows]
        
        # Present value of negative flows (financed at finance_rate)
        pv_negative = sum(cf / (1 + finance_rate) ** i 
                         for i, cf in enumerate(negative_flows))
        
        # Future value of positive flows (reinvested at reinvest_rate)
        fv_positive = sum(cf * (1 + reinvest_rate) ** (n - i) 
                         for i, cf in enumerate(positive_flows))
        
        if abs(pv_negative) < 1e-10:
            logger.warning("MIRR: No negative flows to finance")
            return 0.0
        
        # Calculate MIRR
        try:
            mirr = (fv_positive / abs(pv_negative)) ** (1 / n) - 1
            logger.info(f"✓ MIRR calculated: {mirr:.4f} (finance={finance_rate:.2%}, reinvest={reinvest_rate:.2%})")
            return mirr
        except (ZeroDivisionError, ValueError) as e:
            logger.error(f"MIRR calculation failed: {e}")
            return 0.0
    
    def build_sources_and_uses(self, inputs: LBOInputs) -> pd.DataFrame:
        """
        Build sources & uses of funds table
        
        Args:
            inputs: LBO model inputs
            
        Returns:
            DataFrame with sources and uses
        """
        # USES
        purchase_ev = inputs.purchase_enterprise_value
        transaction_fees = purchase_ev * inputs.transaction_fees
        
        total_uses = purchase_ev + transaction_fees
        
        uses = {
            'Purchase Enterprise Value': purchase_ev,
            'Transaction Fees': transaction_fees,
            'Total Uses': total_uses
        }
        
        # SOURCES
        equity = inputs.equity_contribution + inputs.rollover_equity
        total_debt = sum(t.amount for t in inputs.debt_tranches)
        financing_fees = total_debt * inputs.financing_fees
        
        # Adjust for financing fees
        net_debt_proceeds = total_debt - financing_fees
        
        sources = {
            'Sponsor Equity': inputs.equity_contribution,
            'Rollover Equity': inputs.rollover_equity,
            'Total Equity': equity
        }
        
        # Add each debt tranche
        for tranche in inputs.debt_tranches:
            sources[f'Debt - {tranche.name}'] = tranche.amount
        
        sources.update({
            'Total Debt': total_debt,
            'Less: Financing Fees': -financing_fees,
            'Net Debt Proceeds': net_debt_proceeds,
            'Total Sources': equity + net_debt_proceeds
        })
        
        # Create DataFrame
        df = pd.DataFrame({
            'Uses': pd.Series(uses),
            'Sources': pd.Series(sources)
        })
        
        logger.debug(f"Total Uses: ${total_uses:,.0f}, Total Sources: ${equity + net_debt_proceeds:,.0f}")
        
        return df
    
    def build_debt_schedule(
        self,
        tranches: List[DebtTranche],
        annual_excess_cash: List[float],
        years: int
    ) -> pd.DataFrame:
        """
        Build debt amortization schedule
        
        Args:
            tranches: List of debt tranches
            annual_excess_cash: Excess cash available for debt paydown
            years: Forecast period
            
        Returns:
            DataFrame with debt schedule by tranche
        """
        schedule_data = []
        
        for tranche in tranches:
            balances = [tranche.amount]
            interest_payments = []
            principal_payments = []
            
            for year in range(years):
                beginning_balance = balances[-1]
                
                # Interest payment
                interest = beginning_balance * tranche.interest_rate
                interest_payments.append(interest)
                
                # Principal amortization
                if tranche.amortization_type == "straight_line":
                    if year < tranche.term_years:
                        scheduled_principal = tranche.amount / tranche.term_years
                    else:
                        scheduled_principal = 0
                elif tranche.amortization_type == "bullet":
                    if year == tranche.term_years - 1:
                        scheduled_principal = beginning_balance
                    else:
                        scheduled_principal = 0
                else:
                    scheduled_principal = 0
                
                # Mandatory prepayment from excess cash
                if year < len(annual_excess_cash):
                    mandatory_prepay = annual_excess_cash[year] * tranche.mandatory_prepayment
                    mandatory_prepay = min(mandatory_prepay, beginning_balance - scheduled_principal)
                else:
                    mandatory_prepay = 0
                
                total_principal = scheduled_principal + mandatory_prepay
                total_principal = min(total_principal, beginning_balance)
                principal_payments.append(total_principal)
                
                # Ending balance
                ending_balance = beginning_balance - total_principal
                balances.append(ending_balance)
            
            schedule_data.append({
                'Tranche': tranche.name,
                'Initial': tranche.amount,
                'Interest_Payments': interest_payments,
                'Principal_Payments': principal_payments,
                'Ending_Balances': balances[1:]
            })
        
        return pd.DataFrame(schedule_data)
    
    def project_financials(self, inputs: LBOInputs) -> pd.DataFrame:
        """
        Project financial statements
        
        Args:
            inputs: LBO model inputs
            
        Returns:
            DataFrame with annual projections
        """
        years = len(inputs.revenue_growth_rates)
        
        # Initialize
        base_revenue = inputs.purchase_enterprise_value / inputs.exit_multiple / inputs.ebitda_margins[0]
        
        projections = []
        
        for year in range(years):
            if year == 0:
                revenue = base_revenue
            else:
                revenue = projections[-1]['Revenue'] * (1 + inputs.revenue_growth_rates[year])
            
            ebitda = revenue * inputs.ebitda_margins[year]
            capex = revenue * inputs.capex_pct_revenue
            
            # Change in NWC
            if year == 0:
                nwc = revenue * inputs.nwc_pct_revenue
                delta_nwc = nwc
            else:
                prev_nwc = projections[-1]['Revenue'] * inputs.nwc_pct_revenue
                nwc = revenue * inputs.nwc_pct_revenue
                delta_nwc = nwc - prev_nwc
            
            # Unlevered Free Cash Flow
            ufcf = ebitda - capex - delta_nwc
            
            projections.append({
                'Year': year + 1,
                'Revenue': revenue,
                'EBITDA': ebitda,
                'EBITDA_Margin': inputs.ebitda_margins[year],
                'CapEx': capex,
                'Delta_NWC': delta_nwc,
                'UFCF': ufcf
            })
        
        return pd.DataFrame(projections)
    
    def calculate_lbo_returns(
        self,
        inputs: LBOInputs
    ) -> LBOResult:
        """
        Calculate full LBO returns analysis
        
        Args:
            inputs: LBO model inputs
            
        Returns:
            LBOResult with IRR, MoIC, and detailed schedules
        """
        logger.info("Calculating LBO returns")
        
        # 1. Sources & Uses
        sources_uses = self.build_sources_and_uses(inputs)
        
        # 2. Project financials
        financials = self.project_financials(inputs)
        
        # 3. Calculate debt service
        total_debt = sum(t.amount for t in inputs.debt_tranches)
        
        # Build debt schedule (simplified)
        years = len(inputs.revenue_growth_rates)
        debt_balances = [total_debt]
        interest_expenses = []
        
        for year in range(years):
            beginning_debt = debt_balances[-1]
            
            # Weighted average interest rate
            avg_interest_rate = sum(t.amount * t.interest_rate for t in inputs.debt_tranches) / total_debt
            interest = beginning_debt * avg_interest_rate
            interest_expenses.append(interest)
            
            # Excess cash for debt paydown
            ufcf = financials.iloc[year]['UFCF']
            excess_cash = max(0, ufcf - interest)
            
            # Debt paydown
            principal_payment = excess_cash * inputs.excess_cash_sweep
            principal_payment = min(principal_payment, beginning_debt)
            
            ending_debt = beginning_debt - principal_payment
            debt_balances.append(ending_debt)
        
        # 4. Calculate exit value
        exit_ebitda = inputs.exit_ebitda
        exit_ev = exit_ebitda * inputs.exit_multiple
        exit_debt = debt_balances[inputs.exit_year]
        exit_equity_value = exit_ev - exit_debt
        
        # 5. Calculate returns
        entry_equity = inputs.equity_contribution + inputs.rollover_equity
        moic = exit_equity_value / entry_equity
        
        # IRR calculation (using custom implementation as np.irr is deprecated)
        cash_flows = [-entry_equity] + [0] * (inputs.exit_year - 1) + [exit_equity_value]
        irr = self._calculate_irr(cash_flows)
        
        logger.info(f"LBO Returns - IRR: {irr:.1%}, MoIC: {moic:.2f}x")
        
        # 6. Calculate valuation range per share (based on exit scenarios)
        # Get shares outstanding from exit equity value assumption
        # Assume a reasonable share count based on equity value
        assumed_shares = 1_000_000  # Default assumption
        if hasattr(inputs, 'shares_outstanding'):
            assumed_shares = inputs.shares_outstanding
        elif inputs.purchase_equity_value > 0:
            # Estimate shares from purchase price assuming $50/share baseline
            assumed_shares = inputs.purchase_equity_value / 50.0
        
        # Calculate base value per share
        base_value_per_share = exit_equity_value / assumed_shares
        
        # Create range based on exit multiple sensitivity
       # Bear case: 80% of exit multiple
        bear_exit_ev = (inputs.exit_ebitda * inputs.exit_multiple * 0.8) - exit_debt
        bear_value_per_share = max(0, bear_exit_ev / assumed_shares)
        
        # Bull case: 120% of exit multiple
        bull_exit_ev = (inputs.exit_ebitda * inputs.exit_multiple * 1.2) - exit_debt
        bull_value_per_share = bull_exit_ev / assumed_shares
        
        min_value_per_share = min(bear_value_per_share, base_value_per_share)
        max_value_per_share = max(bull_value_per_share, base_value_per_share)
        
        # Compile results
        result = LBOResult(
            equity_irr=irr,
            equity_moic=moic,
            entry_ev=inputs.purchase_enterprise_value,
            entry_equity=entry_equity,
            total_uses=sources_uses.loc['Total Uses', 'Uses'],
            total_sources=sources_uses.loc['Total Sources', 'Sources'],
            exit_ev=exit_ev,
            exit_equity_value=exit_equity_value,
            exit_total_debt=exit_debt,
            annual_cash_flows=financials,
            debt_schedule=pd.DataFrame({
                'Year': list(range(years + 1)),
                'Debt_Balance': debt_balances,
                'Interest_Expense': [0] + interest_expenses
            }),
            sources_and_uses=sources_uses,
            min_value_per_share=min_value_per_share,
            max_value_per_share=max_value_per_share
        )
        
        return result
    
    def sensitivity_analysis(
        self,
        base_inputs: LBOInputs,
        exit_multiple_range: Tuple[float, float] = (8.0, 12.0),
        exit_ebitda_range: Tuple[float, float] = (-20, 20),  # % change
        steps: int = 5
    ) -> pd.DataFrame:
        """
        Create sensitivity table for exit multiple and EBITDA
        
        Args:
            base_inputs: Base case LBO inputs
            exit_multiple_range: Range of exit multiples
            exit_ebitda_range: Range of EBITDA growth (% from base)
            steps: Number of steps in each dimension
            
        Returns:
            DataFrame with IRR sensitivity
        """
        multiples = np.linspace(exit_multiple_range[0], exit_multiple_range[1], steps)
        ebitda_changes = np.linspace(exit_ebitda_range[0], exit_ebitda_range[1], steps)
        
        results = np.zeros((steps, steps))
        
        for i, multiple in enumerate(multiples):
            for j, ebitda_pct in enumerate(ebitda_changes):
                # Adjust inputs
                adjusted_inputs = LBOInputs(
                    purchase_enterprise_value=base_inputs.purchase_enterprise_value,
                    purchase_equity_value=base_inputs.purchase_equity_value,
                    transaction_fees=base_inputs.transaction_fees,
                    financing_fees=base_inputs.financing_fees,
                    equity_contribution=base_inputs.equity_contribution,
                    rollover_equity=base_inputs.rollover_equity,
                    debt_tranches=base_inputs.debt_tranches,
                    exit_year=base_inputs.exit_year,
                    exit_ebitda=base_inputs.exit_ebitda * (1 + ebitda_pct / 100),
                    exit_multiple=multiple,
                    revenue_growth_rates=base_inputs.revenue_growth_rates,
                    ebitda_margins=base_inputs.ebitda_margins,
                    capex_pct_revenue=base_inputs.capex_pct_revenue,
                    nwc_pct_revenue=base_inputs.nwc_pct_revenue,
                    tax_rate=base_inputs.tax_rate,
                    excess_cash_sweep=base_inputs.excess_cash_sweep
                )
                
                # Calculate returns
                result = self.calculate_lbo_returns(adjusted_inputs)
                results[i, j] = result.equity_irr * 100  # Convert to percentage
        
        # Create DataFrame
        df = pd.DataFrame(
            results,
            index=[f"{m:.1f}x" for m in multiples],
            columns=[f"{e:+.0f}%" for e in ebitda_changes]
        )
        df.index.name = "Exit Multiple"
        df.columns.name = "EBITDA Growth"
        
        logger.info("LBO sensitivity analysis completed")
        
        return df


# Example usage
if __name__ == "__main__":
    # Initialize engine
    engine = LBOEngine()
    
    # Define debt tranches
    debt_tranches = [
        DebtTranche(
            name="Revolver",
            amount=50_000_000,
            interest_rate=0.045,
            term_years=5,
            amortization_type="bullet",
            mandatory_prepayment=0.0
        ),
        DebtTranche(
            name="Term Loan B",
            amount=300_000_000,
            interest_rate=0.065,
            term_years=7,
            amortization_type="straight_line",
            mandatory_prepayment=0.50  # 50% cash sweep
        ),
        DebtTranche(
            name="Subordinated Debt",
            amount=100_000_000,
            interest_rate=0.095,
            term_years=8,
            amortization_type="bullet",
            pik_toggle=True,
            mandatory_prepayment=0.25
        )
    ]
    
    # Define LBO inputs
    inputs = LBOInputs(
        purchase_enterprise_value=800_000_000,
        purchase_equity_value=350_000_000,
        transaction_fees=0.02,  # 2%
        financing_fees=0.03,  # 3%
        equity_contribution=300_000_000,
        rollover_equity=50_000_000,
        debt_tranches=debt_tranches,
        exit_year=5,
        exit_ebitda=120_000_000,
        exit_multiple=10.0,
        revenue_growth_rates=[0.0, 0.05, 0.06, 0.06, 0.05, 0.04],
        ebitda_margins=[0.12, 0.13, 0.14, 0.15, 0.15, 0.15],
        capex_pct_revenue=0.03,
        nwc_pct_revenue=0.10,
        tax_rate=0.25,
        excess_cash_sweep=0.75  # 75% sweep
    )
    
    # Calculate returns
    result = engine.calculate_lbo_returns(inputs)
    
    print("\n" + "="*60)
    print("LBO ANALYSIS RESULTS")
    print("="*60)
    print(f"\nReturns:")
    print(f"  IRR: {result.equity_irr:.1%}")
    print(f"  MoIC: {result.equity_moic:.2f}x")
    
    print(f"\nEntry:")
    print(f"  Enterprise Value: ${result.entry_ev:,.0f}")
    print(f"  Equity Investment: ${result.entry_equity:,.0f}")
    
    print(f"\nExit (Year {inputs.exit_year}):")
    print(f"  Enterprise Value: ${result.exit_ev:,.0f}")
    print(f"  Remaining Debt: ${result.exit_total_debt:,.0f}")
    print(f"  Equity Value: ${result.exit_equity_value:,.0f}")
    
    print(f"\nValuation Range:")
    print(f"  Min Value per Share: ${result.min_value_per_share:.2f}")
    print(f"  Max Value per Share: ${result.max_value_per_share:.2f}")
    
    print(f"\nSources & Uses:")
    print(result.sources_and_uses)
    
    print(f"\nFinancial Projections:")
    print(result.annual_cash_flows.to_string(index=False))
    
    # Sensitivity
    print(f"\nRunning sensitivity analysis...")
    sensitivity = engine.sensitivity_analysis(inputs)
    print(f"\nIRR Sensitivity (%):")
    print(sensitivity.to_string())
