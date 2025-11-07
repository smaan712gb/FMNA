"""
Merger & Accretion/Dilution Model
Complete M&A model with pro forma combination, synergies, and EPS impact
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np
import pandas as pd
from loguru import logger


@dataclass
class CompanyFinancials:
    """Financial metrics for acquirer or target"""
    company_name: str
    shares_outstanding: float
    share_price: float
    market_cap: float
    net_debt: float
    enterprise_value: float
    
    # Income statement
    revenue: float
    ebitda: float
    ebit: float
    interest_expense: float
    taxes: float
    net_income: float
    eps: float
    pe_ratio: float


@dataclass
class MergerInputs:
    """Merger model inputs"""
    # Companies
    acquirer: CompanyFinancials
    target: CompanyFinancials
    
    # Deal structure
    cash_consideration: float
    stock_consideration: float  # % of deal value
    exchange_ratio: Optional[float] = None  # Shares of acquirer per target share
    
    # Financing
    new_debt_issuance: float = 0.0
    debt_interest_rate: float = 0.05
    excess_cash_used: float = 0.0
    
    # Synergies
    revenue_synergies: float = 0.0  # Annual
    cost_synergies: float = 0.0  # Annual
    synergy_tax_rate: float = 0.21
    synergies_year_1_pct: float = 0.5  # 50% in year 1
    integration_costs: float = 0.0  # One-time
    
    # Purchase accounting
    goodwill_created: Optional[float] = None
    intangible_amortization: float = 0.0  # Annual
    
    # Tax
    combined_tax_rate: float = 0.21


@dataclass
class MergerResult:
    """Merger analysis result"""
    # Deal metrics
    purchase_price: float
    premium_to_target: float
    deal_value: float
    
    # Ownership
    acquirer_ownership_pct: float
    target_ownership_pct: float
    new_shares_issued: float
    pro_forma_shares: float
    
    # Accretion/Dilution
    pro_forma_eps: float
    accretion_dilution_pct: float
    accretion_dilution_dollars: float
    is_accretive: bool
    
    # Pro forma financials
    pro_forma_revenue: float
    pro_forma_ebitda: float
    pro_forma_net_income: float
    
    # Synergies
    total_synergies: float
    after_tax_synergies: float
    
    # Returns
    irr_to_target_shareholders: Optional[float] = None
    
    # Detailed tables
    sources_and_uses: Optional[pd.DataFrame] = None
    pro_forma_income_statement: Optional[pd.DataFrame] = None
    ownership_table: Optional[pd.DataFrame] = None


class MergerModel:
    """Merger & Accretion/Dilution Engine"""
    
    def __init__(self):
        """Initialize merger model"""
        logger.info("Merger Model initialized")
    
    def calculate_purchase_price(
        self,
        target: CompanyFinancials,
        premium_pct: float
    ) -> float:
        """
        Calculate purchase price with premium
        
        Args:
            target: Target company financials
            premium_pct: Premium percentage (e.g., 0.30 for 30%)
            
        Returns:
            Purchase price
        """
        return target.market_cap * (1 + premium_pct)
    
    def calculate_exchange_ratio(
        self,
        acquirer_price: float,
        target_price: float,
        premium_pct: float
    ) -> float:
        """
        Calculate exchange ratio for stock deal
        
        Args:
            acquirer_price: Acquirer share price
            target_price: Target share price
            premium_pct: Premium percentage
            
        Returns:
            Exchange ratio (acquirer shares per target share)
        """
        target_price_with_premium = target_price * (1 + premium_pct)
        exchange_ratio = target_price_with_premium / acquirer_price
        return exchange_ratio
    
    def build_sources_and_uses(
        self,
        inputs: MergerInputs,
        purchase_price: float
    ) -> pd.DataFrame:
        """
        Build sources & uses table
        
        Args:
            inputs: Merger inputs
            purchase_price: Total purchase price
            
        Returns:
            DataFrame with sources and uses
        """
        # USES
        equity_purchase = purchase_price
        transaction_fees = purchase_price * 0.02  # Assume 2%
        integration_costs = inputs.integration_costs
        refinance_target_debt = inputs.target.net_debt
        
        total_uses = equity_purchase + transaction_fees + integration_costs + refinance_target_debt
        
        # SOURCES
        cash_from_balance_sheet = inputs.excess_cash_used
        new_debt = inputs.new_debt_issuance
        stock_consideration_value = purchase_price * inputs.stock_consideration
        cash_consideration_value = purchase_price * (1 - inputs.stock_consideration)
        
        # Balance sources
        remaining_need = total_uses - (cash_from_balance_sheet + new_debt + stock_consideration_value)
        cash_consideration_value = max(cash_consideration_value, remaining_need)
        
        sources = {
            'Cash from Balance Sheet': cash_from_balance_sheet,
            'New Debt Issuance': new_debt,
            'Stock Consideration': stock_consideration_value,
            'Cash Consideration': cash_consideration_value,
            'Total Sources': cash_from_balance_sheet + new_debt + stock_consideration_value + cash_consideration_value
        }
        
        uses = {
            'Equity Purchase Price': equity_purchase,
            'Transaction Fees': transaction_fees,
            'Integration Costs': integration_costs,
            'Refinance Target Debt': refinance_target_debt,
            'Total Uses': total_uses
        }
        
        df = pd.DataFrame({
            'Sources': pd.Series(sources),
            'Uses': pd.Series(uses)
        })
        
        return df
    
    def calculate_pro_forma_financials(
        self,
        inputs: MergerInputs,
        includes_synergies: bool = True
    ) -> Dict[str, float]:
        """
        Calculate pro forma combined financials
        
        Args:
            inputs: Merger inputs
            includes_synergies: Whether to include synergies
            
        Returns:
            Dictionary of pro forma financials
        """
        # Revenue
        pro_forma_revenue = inputs.acquirer.revenue + inputs.target.revenue
        if includes_synergies:
            pro_forma_revenue += inputs.revenue_synergies
        
        # EBITDA
        pro_forma_ebitda = inputs.acquirer.ebitda + inputs.target.ebitda
        if includes_synergies:
            pro_forma_ebitda += inputs.cost_synergies
        
        # EBIT
        pro_forma_ebit = inputs.acquirer.ebit + inputs.target.ebit
        if includes_synergies:
            pro_forma_ebit += inputs.cost_synergies
        
        # Amortization of intangibles
        pro_forma_ebit -= inputs.intangible_amortization
        
        # Interest expense
        combined_interest = inputs.acquirer.interest_expense + inputs.target.interest_expense
        new_debt_interest = inputs.new_debt_issuance * inputs.debt_interest_rate
        pro_forma_interest = combined_interest + new_debt_interest
        
        # EBT
        pro_forma_ebt = pro_forma_ebit - pro_forma_interest
        
        # Taxes
        pro_forma_taxes = pro_forma_ebt * inputs.combined_tax_rate
        
        # Net income
        pro_forma_net_income = pro_forma_ebt - pro_forma_taxes
        
        return {
            'revenue': pro_forma_revenue,
            'ebitda': pro_forma_ebitda,
            'ebit': pro_forma_ebit,
            'interest': pro_forma_interest,
            'ebt': pro_forma_ebt,
            'taxes': pro_forma_taxes,
            'net_income': pro_forma_net_income
        }
    
    def calculate_accretion_dilution(
        self,
        inputs: MergerInputs,
        premium_pct: float = 0.30
    ) -> MergerResult:
        """
        Calculate full merger accretion/dilution analysis
        
        Args:
            inputs: Merger model inputs
            premium_pct: Premium to target price
            
        Returns:
            MergerResult with detailed analysis
        """
        logger.info(f"Calculating merger of {inputs.acquirer.company_name} + {inputs.target.company_name}")
        
        # 1. Calculate purchase price
        purchase_price = self.calculate_purchase_price(inputs.target, premium_pct)
        deal_value = purchase_price + inputs.target.net_debt
        
        logger.debug(f"Purchase Price: ${purchase_price:,.0f} ({premium_pct:.0%} premium)")
        
        # 2. Calculate new shares issued (if stock deal)
        stock_consideration_value = purchase_price * inputs.stock_consideration
        new_shares_issued = stock_consideration_value / inputs.acquirer.share_price
        pro_forma_shares = inputs.acquirer.shares_outstanding + new_shares_issued
        
        # 3. Calculate ownership
        acquirer_ownership_pct = inputs.acquirer.shares_outstanding / pro_forma_shares
        target_ownership_pct = new_shares_issued / pro_forma_shares
        
        logger.debug(f"New shares issued: {new_shares_issued:,.0f}")
        logger.debug(f"Pro forma shares: {pro_forma_shares:,.0f}")
        logger.debug(f"Acquirer ownership: {acquirer_ownership_pct:.1%}")
        
        # 4. Calculate pro forma financials WITH synergies
        pf_financials = self.calculate_pro_forma_financials(inputs, includes_synergies=True)
        
        # 5. Calculate EPS
        pro_forma_eps = pf_financials['net_income'] / pro_forma_shares
        standalone_eps = inputs.acquirer.eps
        
        # 6. Accretion/Dilution
        accretion_dilution_dollars = pro_forma_eps - standalone_eps
        accretion_dilution_pct = (pro_forma_eps / standalone_eps - 1) if standalone_eps != 0 else 0
        is_accretive = accretion_dilution_pct > 0
        
        logger.info(f"Pro Forma EPS: ${pro_forma_eps:.2f}")
        logger.info(f"Standalone EPS: ${standalone_eps:.2f}")
        logger.info(f"Accretion/Dilution: {accretion_dilution_pct:.1%} ({'ACCRETIVE' if is_accretive else 'DILUTIVE'})")
        
        # 7. Calculate synergies impact
        total_synergies = inputs.revenue_synergies + inputs.cost_synergies
        after_tax_synergies = total_synergies * (1 - inputs.synergy_tax_rate)
        
        # 8. Build sources & uses
        sources_uses = self.build_sources_and_uses(inputs, purchase_price)
        
        # 9. Build ownership table
        ownership_data = {
            'Acquirer Shareholders': {
                'Shares': inputs.acquirer.shares_outstanding,
                'Ownership %': acquirer_ownership_pct * 100
            },
            'Target Shareholders': {
                'Shares': new_shares_issued,
                'Ownership %': target_ownership_pct * 100
            },
            'Pro Forma Total': {
                'Shares': pro_forma_shares,
                'Ownership %': 100.0
            }
        }
        ownership_table = pd.DataFrame(ownership_data).T
        
        # Compile result
        result = MergerResult(
            purchase_price=purchase_price,
            premium_to_target=premium_pct,
            deal_value=deal_value,
            acquirer_ownership_pct=acquirer_ownership_pct,
            target_ownership_pct=target_ownership_pct,
            new_shares_issued=new_shares_issued,
            pro_forma_shares=pro_forma_shares,
            pro_forma_eps=pro_forma_eps,
            accretion_dilution_pct=accretion_dilution_pct,
            accretion_dilution_dollars=accretion_dilution_dollars,
            is_accretive=is_accretive,
            pro_forma_revenue=pf_financials['revenue'],
            pro_forma_ebitda=pf_financials['ebitda'],
            pro_forma_net_income=pf_financials['net_income'],
            total_synergies=total_synergies,
            after_tax_synergies=after_tax_synergies,
            sources_and_uses=sources_uses,
            ownership_table=ownership_table
        )
        
        return result
    
    def sensitivity_analysis(
        self,
        inputs: MergerInputs,
        premium_range: Tuple[float, float] = (0.20, 0.40),
        synergy_range: Tuple[float, float] = (0.5, 1.5),  # Multiple of base synergies
        steps: int = 5
    ) -> pd.DataFrame:
        """
        Create accretion/dilution sensitivity table
        
        Args:
            inputs: Base merger inputs
            premium_range: Range of premiums
            synergy_range: Multiplier range for synergies
            steps: Number of steps
            
        Returns:
            DataFrame with accretion/dilution %
        """
        premiums = np.linspace(premium_range[0], premium_range[1], steps)
        synergy_mults = np.linspace(synergy_range[0], synergy_range[1], steps)
        
        base_revenue_synergies = inputs.revenue_synergies
        base_cost_synergies = inputs.cost_synergies
        
        results = np.zeros((steps, steps))
        
        for i, premium in enumerate(premiums):
            for j, syn_mult in enumerate(synergy_mults):
                # Adjust inputs
                adjusted_inputs = MergerInputs(
                    acquirer=inputs.acquirer,
                    target=inputs.target,
                    cash_consideration=inputs.cash_consideration,
                    stock_consideration=inputs.stock_consideration,
                    new_debt_issuance=inputs.new_debt_issuance,
                    debt_interest_rate=inputs.debt_interest_rate,
                   excess_cash_used=inputs.excess_cash_used,
                    revenue_synergies=base_revenue_synergies * syn_mult,
                    cost_synergies=base_cost_synergies * syn_mult,
                    synergy_tax_rate=inputs.synergy_tax_rate,
                    integration_costs=inputs.integration_costs,
                    intangible_amortization=inputs.intangible_amortization,
                    combined_tax_rate=inputs.combined_tax_rate
                )
                
                # Calculate
                result = self.calculate_accretion_dilution(adjusted_inputs, premium)
                results[i, j] = result.accretion_dilution_pct * 100
        
        # Create DataFrame
        df = pd.DataFrame(
            results,
            index=[f"{p:.0%}" for p in premiums],
            columns=[f"{s:.1f}x" for s in synergy_mults]
        )
        df.index.name = "Premium"
        df.columns.name = "Synergy Multiple"
        
        logger.info("Merger sensitivity analysis completed")
        
        return df


# Example usage
if __name__ == "__main__":
    # Initialize model
    model = MergerModel()
    
    # Define acquirer
    acquirer = CompanyFinancials(
        company_name="Acquirer Corp",
        shares_outstanding=100_000_000,
        share_price=150.00,
        market_cap=15_000_000_000,
        net_debt=2_000_000_000,
        enterprise_value=17_000_000_000,
        revenue=10_000_000_000,
        ebitda=2_500_000_000,
        ebit=2_200_000_000,
        interest_expense=100_000_000,
        taxes=441_000_000,
        net_income=1_659_000_000,
        eps=16.59,
        pe_ratio=9.0
    )
    
    # Define target
    target = CompanyFinancials(
        company_name="Target Inc",
        shares_outstanding=50_000_000,
        share_price=80.00,
        market_cap=4_000_000_000,
        net_debt=1_000_000_000,
        enterprise_value=5_000_000_000,
        revenue=3_000_000_000,
        ebitda=750_000_000,
        ebit=650_000_000,
        interest_expense=50_000_000,
        taxes=126_000_000,
        net_income=474_000_000,
        eps=9.48,
        pe_ratio=8.4
    )
    
    # Define merger terms
    inputs = MergerInputs(
        acquirer=acquirer,
        target=target,
        cash_consideration=2_000_000_000,
        stock_consideration=0.50,  # 50% stock
        new_debt_issuance=1_500_000_000,
        debt_interest_rate=0.05,
        excess_cash_used=500_000_000,
        revenue_synergies=200_000_000,  # $200M revenue synergies
        cost_synergies=150_000_000,  # $150M cost synergies
        synergy_tax_rate=0.21,
        integration_costs=100_000_000,
        intangible_amortization=50_000_000,
        combined_tax_rate=0.21
    )
    
    # Calculate accretion/dilution
    result = model.calculate_accretion_dilution(inputs, premium_pct=0.30)
    
    print("\n" + "="*70)
    print("MERGER & ACCRETION/DILUTION ANALYSIS")
    print("="*70)
    
    print(f"\nDeal Terms:")
    print(f"  Purchase Price: ${result.purchase_price:,.0f}")
    print(f"  Premium: {result.premium_to_target:.0%}")
    print(f"  Deal Value (incl. debt): ${result.deal_value:,.0f}")
    
    print(f"\nOwnership:")
    print(f"  Acquirer: {result.acquirer_ownership_pct:.1%}")
    print(f"  Target: {result.target_ownership_pct:.1%}")
    print(f"  New Shares Issued: {result.new_shares_issued:,.0f}")
    
    print(f"\nPro Forma Financials:")
    print(f"  Revenue: ${result.pro_forma_revenue:,.0f}")
    print(f"  EBITDA: ${result.pro_forma_ebitda:,.0f}")
    print(f"  Net Income: ${result.pro_forma_net_income:,.0f}")
    
    print(f"\nAccretion/Dilution:")
    print(f"  Pro Forma EPS: ${result.pro_forma_eps:.2f}")
    print(f"  Impact: {result.accretion_dilution_pct:+.1%} ({result.accretion_dilution_dollars:+.2f})")
    print(f"  Status: {'✓ ACCRETIVE' if result.is_accretive else '✗ DILUTIVE'}")
    
    print(f"\nSynergies:")
    print(f"  Total Annual: ${result.total_synergies:,.0f}")
    print(f"  After-Tax: ${result.after_tax_synergies:,.0f}")
    
    print(f"\nSources & Uses:")
    print(result.sources_and_uses)
    
    # Sensitivity
    print(f"\nRunning sensitivity analysis...")
    sensitivity = model.sensitivity_analysis(inputs)
    print(f"\nAccretion/Dilution Sensitivity (%):")
    print(sensitivity.to_string())
