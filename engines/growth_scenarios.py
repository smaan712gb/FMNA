"""
Growth Scenarios Engine
Models from hypergrowth → steady growth → maturity → distress/bankruptcy
Includes SaaS metrics (NRR, CAC, LTV), Altman Z-Score, Ohlson O-Score
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np
import pandas as pd
from loguru import logger


class GrowthStage(str, Enum):
    """Growth stage classification"""
    HYPERGROWTH = "hypergrowth"  # >40% growth, negative FCF
    GROWTH = "growth"  # 20-40% growth, improving margins
    MATURE = "mature"  # 5-20% growth, stable margins
    DECLINE = "decline"  # 0-5% growth
    DISTRESS = "distress"  # Negative growth, covenant stress


class Industry(str, Enum):
    """Industry classifications for specific metrics"""
    SAAS = "saas"
    ECOMMERCE = "ecommerce"
    FINTECH = "fintech"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    HEALTHCARE = "healthcare"
    ENERGY = "energy"


@dataclass
class SaaSMetrics:
    """SaaS-specific metrics"""
    arr: float  # Annual Recurring Revenue
    new_arr: float  # New ARR added
    expansion_arr: float  # Expansion from existing customers
    churn_arr: float  # Churned ARR
    
    # Cohort metrics
    nrr: float  # Net Revenue Retention (>100% = net expansion)
    grr: float  # Gross Revenue Retention
    
    # Unit economics
    cac: float  # Customer Acquisition Cost
    ltv: float  # Lifetime Value
    ltv_cac_ratio: float  # LTV/CAC ratio (>3x good)
    cac_payback_months: int  # Months to payback CAC
    
    # Magic numbers
    magic_number: float  # New ARR / S&M spend (>0.75 good)
    rule_of_40: float  # Growth % + FCF margin % (>40% good)


@dataclass
class DistressMetrics:
    """Distress/bankruptcy risk metrics"""
    altman_z_score: float  # >2.99 safe, <1.81 distress
    ohlson_o_score: float  # >0.5 high risk
    
    # Liquidity
    current_ratio: float
    quick_ratio: float
    cash_burn_months: float  # Months of cash remaining
    
    # Leverage
    debt_to_ebitda: float
    interest_coverage: float  # EBIT / Interest
    
    # Working capital stress
    dso: float  # Days Sales Outstanding
    dio: float  # Days Inventory Outstanding  
    dpo: float  # Days Payable Outstanding
    cash_conversion_cycle: float  # DIO + DSO - DPO


@dataclass
class GrowthScenarioInputs:
    """Inputs for growth scenario modeling"""
    company_name: str
    industry: Industry
    current_stage: GrowthStage
    
    # Financials (base year)
    revenue: float
    ebitda: float
    ebit: float
    net_income: float
    total_assets: float
    current_assets: float
    current_liabilities: float
    total_debt: float
    cash: float
    working_capital: float
    retained_earnings: Optional[float] = None  # Will be estimated if not provided
    market_value_equity: Optional[float] = None  # Market cap (for Altman Z-Score)
    book_value_liabilities: Optional[float] = None  # Total liabilities from balance sheet
    
    # Forecast assumptions
    years: int = 5
    growth_trajectory: List[float] = None  # Custom growth rates
    margin_trajectory: List[float] = None  # Custom EBITDA margins
    base_revenue_growth: Optional[float] = 0.15  # Default revenue growth assumption
    base_margin_expansion: Optional[float] = 0.02  # Default margin expansion
    market_size_billions: Optional[float] = None  # Total addressable market size in billions
    
    # SaaS specific (if applicable)
    saas_metrics: Optional[SaaSMetrics] = None
    
    # Industry-specific parameters
    capex_pct_revenue: float = 0.05
    nwc_pct_revenue: float = 0.10
    tax_rate: float = 0.21


@dataclass
class ScenarioResult:
    """Growth scenario analysis result"""
    scenario_name: str
    growth_stage: GrowthStage
    
    # Projections
    financial_projections: pd.DataFrame
    
    # Terminal metrics
    terminal_revenue: float
    terminal_ebitda: float
    terminal_fcf: float
    
    # Risk assessment
    distress_metrics: Optional[DistressMetrics] = None
    bankruptcy_probability: float = 0.0
    
    # Valuation impact
    implied_ev_range: Tuple[float, float] = None


class GrowthScenariosEngine:
    """Growth Scenarios Engine - Hypergrowth to Distress"""
    
    def __init__(self):
        """Initialize growth scenarios engine"""
        logger.info("Growth Scenarios Engine initialized")
    
    def calculate_altman_z_score(
        self,
        working_capital: float,
        total_assets: float,
        retained_earnings: float,
        ebit: float,
        market_value_equity: float,
        total_liabilities: float,
        sales: float
    ) -> float:
        """
        Calculate Altman Z-Score for bankruptcy prediction
        
        Z > 2.99: Safe zone
        1.81 < Z < 2.99: Gray zone
        Z < 1.81: Distress zone
        
        Args:
            working_capital: Current assets - current liabilities
            total_assets: Total assets
            retained_earnings: Retained earnings
            ebit: Earnings before interest and taxes
            market_value_equity: Market value of equity
            total_liabilities: Total liabilities
            sales: Total sales/revenue
            
        Returns:
            Altman Z-Score
        """
        X1 = working_capital / total_assets
        X2 = retained_earnings / total_assets
        X3 = ebit / total_assets
        X4 = market_value_equity / total_liabilities
        X5 = sales / total_assets
        
        z_score = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5
        
        logger.debug(f"Altman Z-Score: {z_score:.2f}")
        
        return z_score
    
    def calculate_ohlson_o_score(
        self,
        total_assets: float,
        total_liabilities: float,
        working_capital: float,
        current_liabilities: float,
        current_assets: float,
        net_income: float,
        funds_operations: float,
        negative_earnings_2years: bool = False
    ) -> float:
        """
        Calculate Ohlson O-Score for bankruptcy prediction
        
        O > 0.5: High risk
        O < 0.5: Low risk
        
        Args:
            total_assets: Total assets
            total_liabilities: Total liabilities
            working_capital: Working capital
            current_liabilities: Current liabilities
            current_assets: Current assets (for liquidity ratio)
            net_income: Net income
            funds_operations: Funds from operations
            negative_earnings_2years: True if negative earnings for 2 years
            
        Returns:
            Ohlson O-Score
        """
        # Simplified Ohlson model
        SIZE = np.log(total_assets / 10000)  # Normalized
        TLTA = total_liabilities / total_assets
        WCTA = working_capital / total_assets
        CLCA = current_liabilities / current_assets if current_assets > 0 else 999
        NITA = net_income / total_assets
        FUTL = funds_operations / total_liabilities if total_liabilities > 0 else 0
        INTWO = 1 if negative_earnings_2years else 0
        
        o_score = (
            -1.32 
            - 0.407 * SIZE 
            + 6.03 * TLTA 
            - 1.43 * WCTA 
            + 0.0757 * CLCA 
            - 2.37 * NITA 
            - 1.83 * FUTL 
            + 0.285 * INTWO
        )
        
        o_prob = 1 / (1 + np.exp(-o_score))
        
        logger.debug(f"Ohlson O-Score: {o_prob:.3f} ({'HIGH RISK' if o_prob > 0.5 else 'LOW RISK'})")
        
        return o_prob
    
    def classify_growth_stage(
        self,
        revenue_growth: float,
        ebitda_margin: float,
        fcf_margin: float
    ) -> GrowthStage:
        """
        Classify company into growth stage
        
        Args:
            revenue_growth: Revenue growth rate
            ebitda_margin: EBITDA margin
            fcf_margin: FCF margin
            
        Returns:
            GrowthStage classification
        """
        if revenue_growth > 0.40 and fcf_margin < 0:
            return GrowthStage.HYPERGROWTH
        elif revenue_growth >= 0.20:
            return GrowthStage.GROWTH
        elif revenue_growth >= 0.05:
            return GrowthStage.MATURE
        elif revenue_growth >= 0:
            return GrowthStage.DECLINE
        else:
            return GrowthStage.DISTRESS
    
    def calculate_saas_metrics(
        self,
        arr: float,
        new_arr: float,
        expansion_arr: float,
        churn_arr: float,
        cac: float,
        gross_margin: float,
        churn_rate_monthly: float,
        sm_spend: float
    ) -> SaaSMetrics:
        """
        Calculate comprehensive SaaS metrics
        
        Args:
            arr: Annual Recurring Revenue
            new_arr: New ARR
            expansion_arr: Expansion ARR
            churn_arr: Churned ARR
            cac: Customer Acquisition Cost
            gross_margin: Gross margin %
            churn_rate_monthly: Monthly churn rate
            sm_spend: Sales & Marketing spend
            
        Returns:
            SaaSMetrics object
        """
        # Net Revenue Retention
        starting_arr = arr - new_arr
        nrr = ((starting_arr + expansion_arr - churn_arr) / starting_arr) if starting_arr > 0 else 1.0
        
        # Gross Revenue Retention
        grr = ((starting_arr - churn_arr) / starting_arr) if starting_arr > 0 else 1.0
        
        # LTV calculation
        avg_customer_lifetime_months = 1 / churn_rate_monthly if churn_rate_monthly > 0 else 60
        avg_customer_value = arr / (1 / churn_rate_monthly / 12) if churn_rate_monthly > 0 else arr
        ltv = avg_customer_value * gross_margin * avg_customer_lifetime_months / 12
        
        # LTV/CAC ratio
        ltv_cac_ratio = ltv / cac if cac > 0 else 0
        
        # CAC Payback
        monthly_revenue_per_customer = (arr / (1 / churn_rate_monthly / 12)) / 12 if churn_rate_monthly > 0 else 0
        monthly_gross_profit = monthly_revenue_per_customer * gross_margin
        cac_payback_months = int(cac / monthly_gross_profit) if monthly_gross_profit > 0 else 999
        
        # Magic Number
        magic_number = new_arr / sm_spend if sm_spend > 0 else 0
        
        # Rule of 40 (placeholder - would need growth rate)
        rule_of_40 = 0.0  # Calculated separately
        
        metrics = SaaSMetrics(
            arr=arr,
            new_arr=new_arr,
            expansion_arr=expansion_arr,
            churn_arr=churn_arr,
            nrr=nrr,
            grr=grr,
            cac=cac,
            ltv=ltv,
            ltv_cac_ratio=ltv_cac_ratio,
            cac_payback_months=cac_payback_months,
            magic_number=magic_number,
            rule_of_40=rule_of_40
        )
        
        logger.info(f"SaaS Metrics - NRR: {nrr:.1%}, LTV/CAC: {ltv_cac_ratio:.1f}x, Magic#: {magic_number:.2f}")
        
        return metrics
    
    def project_growth_scenario(
        self,
        inputs: GrowthScenarioInputs,
        scenario_name: str = "Base"
    ) -> ScenarioResult:
        """
        Project financial scenarios across growth stages
        
        Args:
            inputs: Growth scenario inputs
            scenario_name: Name of scenario
            
        Returns:
            ScenarioResult with projections
        """
        logger.info(f"Projecting {scenario_name} scenario for {inputs.company_name}")
        
        # Determine growth trajectory if not provided
        if inputs.growth_trajectory is None:
            if inputs.current_stage == GrowthStage.HYPERGROWTH:
                growth_rates = [0.50, 0.45, 0.35, 0.25, 0.18]
            elif inputs.current_stage == GrowthStage.GROWTH:
                growth_rates = [0.30, 0.25, 0.20, 0.15, 0.12]
            elif inputs.current_stage == GrowthStage.MATURE:
                growth_rates = [0.10, 0.08, 0.07, 0.06, 0.05]
            elif inputs.current_stage == GrowthStage.DECLINE:
                growth_rates = [0.03, 0.02, 0.01, 0.00, -0.02]
            else:  # DISTRESS
                growth_rates = [-0.05, -0.10, -0.15, -0.10, -0.05]
        else:
            growth_rates = inputs.growth_trajectory
        
        # Margin trajectory
        if inputs.margin_trajectory is None:
            base_margin = inputs.ebitda / inputs.revenue if inputs.revenue > 0 else 0.15
            if inputs.current_stage == GrowthStage.HYPERGROWTH:
                margins = [base_margin, base_margin + 0.02, base_margin + 0.04, 
                          base_margin + 0.06, base_margin + 0.08]
            elif inputs.current_stage == GrowthStage.DISTRESS:
                margins = [base_margin, base_margin - 0.03, base_margin - 0.05,
                          base_margin - 0.04, base_margin - 0.03]
            else:
                margins = [base_margin] * inputs.years
        else:
            margins = inputs.margin_trajectory
        
        # Project financials
        projections = []
        revenue = inputs.revenue
        
        for year in range(inputs.years):
            # Revenue
            revenue = revenue * (1 + growth_rates[year])
            
            # EBITDA
            ebitda = revenue * margins[year]
            
            # CapEx
            capex = revenue * inputs.capex_pct_revenue
            
            # Change in NWC
            if year == 0:
                delta_nwc = revenue * inputs.nwc_pct_revenue
            else:
                prev_revenue = projections[-1]['Revenue']
                delta_nwc = (revenue - prev_revenue) * inputs.nwc_pct_revenue
            
            # FCF
            fcf = ebitda - capex - delta_nwc
            fcf_margin = fcf / revenue if revenue > 0 else 0
            
            projections.append({
                'Year': year + 1,
                'Revenue': revenue,
                'Growth_%': growth_rates[year] * 100,
                'EBITDA': ebitda,
                'EBITDA_Margin_%': margins[year] * 100,
                'CapEx': capex,
                'Delta_NWC': delta_nwc,
                'FCF': fcf,
                'FCF_Margin_%': fcf_margin * 100
            })
        
        df = pd.DataFrame(projections)
        
        # Calculate distress metrics
        terminal_revenue = projections[-1]['Revenue']
        terminal_ebitda = projections[-1]['EBITDA']
        terminal_fcf = projections[-1]['FCF']
        
        # Calculate comprehensive distress metrics
        # Altman Z-Score
        retained_earnings = inputs.retained_earnings if inputs.retained_earnings else inputs.total_assets * 0.2
        market_value_equity = inputs.market_value_equity if inputs.market_value_equity else (inputs.total_assets - inputs.total_debt)
        total_liabilities = inputs.book_value_liabilities if inputs.book_value_liabilities else inputs.total_debt
        
        z_score = self.calculate_altman_z_score(
            working_capital=inputs.working_capital,
            total_assets=inputs.total_assets,
            retained_earnings=retained_earnings,
            ebit=inputs.ebit,
            market_value_equity=market_value_equity,
            total_liabilities=total_liabilities,
            sales=inputs.revenue
        )
        
        # Ohlson O-Score
        current_assets = inputs.current_assets if inputs.current_assets > 0 else inputs.total_assets * 0.5
        funds_operations = inputs.ebitda - (inputs.revenue * 0.05)  # Estimate FOF
        negative_earnings_2years = inputs.net_income < 0
        
        o_score = self.calculate_ohlson_o_score(
            total_assets=inputs.total_assets,
            total_liabilities=total_liabilities,
            working_capital=inputs.working_capital,
            current_liabilities=inputs.current_liabilities,
            current_assets=current_assets,
            net_income=inputs.net_income,
            funds_operations=funds_operations,
            negative_earnings_2years=negative_earnings_2years
        )
        
        # Calculate financial health ratios
        # Interest Coverage Ratio (EBIT / Interest Expense)
        # Estimate interest expense as 5% of total debt if not provided
        interest_expense = inputs.total_debt * 0.05
        interest_coverage = inputs.ebit / interest_expense if interest_expense > 0 else 999
        
        # Debt/EBITDA
        debt_to_ebitda = inputs.total_debt / inputs.ebitda if inputs.ebitda > 0 else 0
        
        # Current Ratio (Current Assets / Current Liabilities)
        current_ratio = current_assets / inputs.current_liabilities if inputs.current_liabilities > 0 else 0
        
        # Quick Ratio ((Current Assets - Inventory) / Current Liabilities)
        # Estimate inventory as 30% of current assets if not provided
        inventory = current_assets * 0.30
        quick_ratio = (current_assets - inventory) / inputs.current_liabilities if inputs.current_liabilities > 0 else 0
        
        # Cash burn months (Cash / Monthly Burn Rate)
        # If FCF is negative, estimate months of cash runway
        if terminal_fcf < 0:
            monthly_burn = abs(terminal_fcf) / 12
            cash_burn_months = inputs.cash / monthly_burn if monthly_burn > 0 else 999
        else:
            cash_burn_months = 999  # Not burning cash
        
        # Working capital metrics (simplified)
        dso = 45  # Typical days sales outstanding
        dio = 60  # Typical days inventory outstanding
        dpo = 30  # Typical days payables outstanding
        cash_conversion_cycle = dso + dio - dpo
        
        # Create comprehensive distress metrics object
        distress_metrics = DistressMetrics(
            altman_z_score=z_score,
            ohlson_o_score=o_score,
            current_ratio=current_ratio,
            quick_ratio=quick_ratio,
            cash_burn_months=cash_burn_months,
            debt_to_ebitda=debt_to_ebitda,
            interest_coverage=interest_coverage,
            dso=dso,
            dio=dio,
            dpo=dpo,
            cash_conversion_cycle=cash_conversion_cycle
        )
        
        # Estimate bankruptcy probability based on Z-Score and O-Score
        bankruptcy_prob = 0.0
        if z_score < 1.81 or o_score > 0.5:
            bankruptcy_prob = 0.80  # High distress risk
        elif z_score < 2.99 or o_score > 0.3:
            bankruptcy_prob = 0.30  # Gray zone
        else:
            bankruptcy_prob = 0.05  # Safe zone
        
        # Compile result with full distress metrics
        result = ScenarioResult(
            scenario_name=scenario_name,
            growth_stage=inputs.current_stage,
            financial_projections=df,
            terminal_revenue=terminal_revenue,
            terminal_ebitda=terminal_ebitda,
            terminal_fcf=terminal_fcf,
            distress_metrics=distress_metrics,
            bankruptcy_probability=bankruptcy_prob
        )
        
        logger.info(f"Scenario complete - Terminal Revenue: ${terminal_revenue:,.0f}, " +
                   f"Bankruptcy Prob: {bankruptcy_prob:.0%}")
        
        return result
    
    def compare_scenarios(
        self,
        inputs: GrowthScenarioInputs
    ) -> Dict[str, ScenarioResult]:
        """
        Run multiple scenarios: Bull, Base, Bear, Distress
        
        Args:
            inputs: Base inputs
            
        Returns:
            Dictionary of scenario results
        """
        scenarios = {}
        
        # Bull case
        bull_inputs = GrowthScenarioInputs(
            company_name=inputs.company_name,
            industry=inputs.industry,
            current_stage=inputs.current_stage,
            revenue=inputs.revenue,
            ebitda=inputs.ebitda,
            ebit=inputs.ebit,
            net_income=inputs.net_income,
            total_assets=inputs.total_assets,
            current_assets=inputs.current_assets,
            current_liabilities=inputs.current_liabilities,
            total_debt=inputs.total_debt,
            cash=inputs.cash,
            working_capital=inputs.working_capital,
            years=inputs.years,
            growth_trajectory=[g * 1.3 for g in (inputs.growth_trajectory or [0.2] * inputs.years)],
            margin_trajectory=[m * 1.2 for m in (inputs.margin_trajectory or [0.15] * inputs.years)],
            capex_pct_revenue=inputs.capex_pct_revenue * 0.8,
            nwc_pct_revenue=inputs.nwc_pct_revenue,
            tax_rate=inputs.tax_rate
        )
        scenarios['Bull'] = self.project_growth_scenario(bull_inputs, "Bull")
        
        # Base case
        scenarios['Base'] = self.project_growth_scenario(inputs, "Base")
        
        # Bear case
        bear_inputs = GrowthScenarioInputs(
            company_name=inputs.company_name,
            industry=inputs.industry,
            current_stage=inputs.current_stage,
            revenue=inputs.revenue,
            ebitda=inputs.ebitda,
            ebit=inputs.ebit,
            net_income=inputs.net_income,
            total_assets=inputs.total_assets,
            current_assets=inputs.current_assets,
            current_liabilities=inputs.current_liabilities,
            total_debt=inputs.total_debt,
            cash=inputs.cash,
            working_capital=inputs.working_capital,
            years=inputs.years,
            growth_trajectory=[g * 0.5 for g in (inputs.growth_trajectory or [0.2] * inputs.years)],
            margin_trajectory=[m * 0.8 for m in (inputs.margin_trajectory or [0.15] * inputs.years)],
            capex_pct_revenue=inputs.capex_pct_revenue,
            nwc_pct_revenue=inputs.nwc_pct_revenue,
            tax_rate=inputs.tax_rate
        )
        scenarios['Bear'] = self.project_growth_scenario(bear_inputs, "Bear")
        
        return scenarios


# Example usage
if __name__ == "__main__":
    # Initialize engine
    engine = GrowthScenariosEngine()
    
    # Define company inputs (SaaS hypergrowth example)
    inputs = GrowthScenarioInputs(
        company_name="HyperGrowth SaaS Inc",
        industry=Industry.SAAS,
        current_stage=GrowthStage.HYPERGROWTH,
        revenue=100_000_000,
        ebitda=-10_000_000,  # Burning cash
        ebit=-15_000_000,
        net_income=-20_000_000,
        total_assets=150_000_000,
        current_assets=80_000_000,
        current_liabilities=30_000_000,
        total_debt=50_000_000,
        cash=60_000_000,
        working_capital=50_000_000,
        years=5,
        capex_pct_revenue=0.03,
        nwc_pct_revenue=0.08,
        tax_rate=0.21
    )
    
    # Run scenarios
    print("\n" + "="*70)
    print("GROWTH SCENARIOS ANALYSIS")
    print("="*70)
    
    scenarios = engine.compare_scenarios(inputs)
    
    for scenario_name, result in scenarios.items():
        print(f"\n{scenario_name} Case:")
        print(f"  Terminal Revenue: ${result.terminal_revenue:,.0f}")
        print(f"  Terminal EBITDA: ${result.terminal_ebitda:,.0f}")
        print(f"  Terminal FCF: ${result.terminal_fcf:,.0f}")
        print(f"  Bankruptcy Risk: {result.bankruptcy_probability:.0%}")
        print(f"\n  Projections:")
        print(result.financial_projections.to_string(index=False))
