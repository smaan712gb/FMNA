"""
DCF (Discounted Cash Flow) Valuation Engine
Professional-grade DCF model with WACC, terminal value, and sensitivities
"""

from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy import stats
from loguru import logger

from config.schemas import ValuationScenario


@dataclass
class WACCInputs:
    """WACC calculation inputs"""
    risk_free_rate: float  # Treasury yield
    equity_risk_premium: float  # Market ERP
    unlevered_beta: float  # Asset beta
    target_debt_to_equity: float  # Target D/E ratio
    cost_of_debt: float  # Pre-tax cost of debt
    tax_rate: float  # Marginal tax rate
    market_cap: float  # Current market cap
    net_debt: float  # Total debt - cash


@dataclass
class TerminalValueInputs:
    """Terminal value calculation inputs"""
    method: str  # "gordon" or "exit_multiple"
    perpetual_growth_rate: Optional[float] = None  # For Gordon Growth
    exit_multiple: Optional[float] = None  # For Exit Multiple (EV/EBITDA)
    terminal_ebitda: Optional[float] = None  # For Exit Multiple


@dataclass
class DCFResult:
    """DCF valuation result"""
    enterprise_value: float
    equity_value: float
    value_per_share: float
    shares_outstanding: float
    
    # Components
    pv_forecast_period: float
    terminal_value: float
    pv_terminal_value: float
    
    # WACC components
    wacc: float
    cost_of_equity: float
    levered_beta: float
    cost_of_debt_after_tax: float
    weight_equity: float
    weight_debt: float
    
    # Sensitivities
    sensitivities: Optional[pd.DataFrame] = None
    
    # Cash flows
    fcff_forecast: Optional[List[float]] = None
    discount_factors: Optional[List[float]] = None


class DCFEngine:
    """DCF Valuation Engine"""
    
    def __init__(self):
        """Initialize DCF engine"""
        logger.info("DCF Engine initialized")
    
    def calculate_wacc(self, inputs: WACCInputs) -> Tuple[float, float, float]:
        """
        Calculate Weighted Average Cost of Capital (WACC)
        
        Args:
            inputs: WACC calculation inputs
            
        Returns:
            Tuple of (WACC, cost_of_equity, levered_beta)
        """
        # Step 1: Relever beta to target capital structure
        levered_beta = inputs.unlevered_beta * (
            1 + (1 - inputs.tax_rate) * inputs.target_debt_to_equity
        )
        
        # Step 2: Calculate cost of equity (CAPM)
        cost_of_equity = (
            inputs.risk_free_rate + 
            levered_beta * inputs.equity_risk_premium
        )
        
        # Step 3: After-tax cost of debt
        cost_of_debt_after_tax = inputs.cost_of_debt * (1 - inputs.tax_rate)
        
        # Step 4: Calculate weights
        total_value = inputs.market_cap + inputs.net_debt
        weight_equity = inputs.market_cap / total_value
        weight_debt = inputs.net_debt / total_value
        
        # Step 5: Calculate WACC
        wacc = (
            weight_equity * cost_of_equity + 
            weight_debt * cost_of_debt_after_tax
        )
        
        logger.debug(f"WACC: {wacc:.2%}, CoE: {cost_of_equity:.2%}, Levered Beta: {levered_beta:.2f}")
        
        return wacc, cost_of_equity, levered_beta
    
    def calculate_terminal_value(
        self,
        last_fcff: float,
        inputs: TerminalValueInputs,
        wacc: float
    ) -> float:
        """
        Calculate terminal value using Gordon Growth or Exit Multiple
        
        Args:
            last_fcff: Last year FCFF in forecast period
            inputs: Terminal value calculation inputs
            wacc: WACC for discounting
            
        Returns:
            Terminal value
        """
        if inputs.method.lower() == "gordon":
            if inputs.perpetual_growth_rate is None:
                raise ValueError("perpetual_growth_rate required for Gordon Growth method")
            
            if inputs.perpetual_growth_rate >= wacc:
                raise ValueError("Perpetual growth rate must be less than WACC")
            
            # Gordon Growth Model: TV = FCF(n+1) / (WACC - g)
            terminal_fcff = last_fcff * (1 + inputs.perpetual_growth_rate)
            terminal_value = terminal_fcff / (wacc - inputs.perpetual_growth_rate)
            
            logger.debug(f"Terminal Value (Gordon Growth @ {inputs.perpetual_growth_rate:.1%}): {terminal_value:,.0f}")
            
        elif inputs.method.lower() == "exit_multiple":
            if inputs.exit_multiple is None or inputs.terminal_ebitda is None:
                raise ValueError("exit_multiple and terminal_ebitda required for Exit Multiple method")
            
            # Exit Multiple: TV = Terminal EBITDA × Exit Multiple
            terminal_value = inputs.terminal_ebitda * inputs.exit_multiple
            
            logger.debug(f"Terminal Value (Exit Multiple {inputs.exit_multiple:.1f}x): {terminal_value:,.0f}")
            
        else:
            raise ValueError(f"Unknown terminal value method: {inputs.method}")
        
        return terminal_value
    
    def discount_cash_flows(
        self,
        cash_flows: List[float],
        wacc: float,
        mid_year_convention: bool = True
    ) -> Tuple[List[float], float]:
        """
        Discount cash flows to present value
        
        Args:
            cash_flows: List of future cash flows
            wacc: Discount rate (WACC)
            mid_year_convention: If True, assume mid-year cash flows
            
        Returns:
            Tuple of (discount_factors, present_value_sum)
        """
        discount_factors = []
        pv_sum = 0.0
        
        for i, cf in enumerate(cash_flows):
            # Period (1, 2, 3, ...)
            period = i + 1
            
            # Adjust for mid-year convention
            if mid_year_convention:
                adjusted_period = period - 0.5
            else:
                adjusted_period = period
            
            # Discount factor
            df = 1 / ((1 + wacc) ** adjusted_period)
            discount_factors.append(df)
            
            # Present value
            pv = cf * df
            pv_sum += pv
            
            logger.debug(f"Year {period}: CF={cf:,.0f}, DF={df:.4f}, PV={pv:,.0f}")
        
        return discount_factors, pv_sum
    
    def calculate_dcf(
        self,
        fcff_forecast: List[float],
        wacc_inputs: WACCInputs,
        terminal_inputs: TerminalValueInputs,
        shares_outstanding: float,
        cash: float = 0.0,
        debt: float = 0.0,
        minority_interest: float = 0.0,
        investments: float = 0.0,
        mid_year_convention: bool = True
    ) -> DCFResult:
        """
        Calculate full DCF valuation
        
        Args:
            fcff_forecast: List of forecasted Free Cash Flows to Firm
            wacc_inputs: WACC calculation inputs
            terminal_inputs: Terminal value inputs
            shares_outstanding: Diluted shares outstanding
            cash: Cash and equivalents
            debt: Total debt
            minority_interest: Minority interest to subtract
            investments: Non-operating investments to add
            mid_year_convention: Use mid-year discounting
            
        Returns:
            DCFResult object with full valuation
        """
        logger.info("Starting DCF calculation")
        
        # Step 1: Calculate WACC
        wacc, cost_of_equity, levered_beta = self.calculate_wacc(wacc_inputs)
        
        # Step 2: Discount forecast period cash flows
        discount_factors, pv_forecast = self.discount_cash_flows(
            fcff_forecast, wacc, mid_year_convention
        )
        
        # Step 3: Calculate terminal value
        last_fcff = fcff_forecast[-1]
        terminal_value = self.calculate_terminal_value(
            last_fcff, terminal_inputs, wacc
        )
        
        # Step 4: Discount terminal value to present
        n = len(fcff_forecast)
        if mid_year_convention:
            tv_period = n + 0.5
        else:
            tv_period = n
        
        tv_discount_factor = 1 / ((1 + wacc) ** tv_period)
        pv_terminal_value = terminal_value * tv_discount_factor
        
        logger.debug(f"Terminal Value: {terminal_value:,.0f}, PV: {pv_terminal_value:,.0f}")
        
        # Step 5: Calculate Enterprise Value
        enterprise_value = pv_forecast + pv_terminal_value
        
        # Step 6: Bridge to Equity Value
        net_debt = debt - cash
        equity_value = (
            enterprise_value 
            - net_debt 
            - minority_interest 
            + investments
        )
        
        # Step 7: Value per share
        value_per_share = equity_value / shares_outstanding if shares_outstanding > 0 else 0
        
        # Log results
        logger.info(f"Enterprise Value: ${enterprise_value:,.0f}")
        logger.info(f"Equity Value: ${equity_value:,.0f}")
        logger.info(f"Value per Share: ${value_per_share:.2f}")
        
        # Prepare result
        result = DCFResult(
            enterprise_value=enterprise_value,
            equity_value=equity_value,
            value_per_share=value_per_share,
            shares_outstanding=shares_outstanding,
            pv_forecast_period=pv_forecast,
            terminal_value=terminal_value,
            pv_terminal_value=pv_terminal_value,
            wacc=wacc,
            cost_of_equity=cost_of_equity,
            levered_beta=levered_beta,
            cost_of_debt_after_tax=wacc_inputs.cost_of_debt * (1 - wacc_inputs.tax_rate),
            weight_equity=wacc_inputs.market_cap / (wacc_inputs.market_cap + wacc_inputs.net_debt),
            weight_debt=wacc_inputs.net_debt / (wacc_inputs.market_cap + wacc_inputs.net_debt),
            fcff_forecast=fcff_forecast,
            discount_factors=discount_factors
        )
        
        return result
    
    def sensitivity_analysis(
        self,
        base_fcff: List[float],
        base_wacc_inputs: WACCInputs,
        terminal_inputs: TerminalValueInputs,
        shares_outstanding: float,
        cash: float,
        debt: float,
        wacc_range: Tuple[float, float] = (-0.02, 0.02),  # +/- 2%
        growth_range: Tuple[float, float] = (-0.01, 0.01),  # +/- 1%
        steps: int = 5
    ) -> pd.DataFrame:
        """
        Create sensitivity table for WACC and Terminal Growth Rate
        
        Args:
            base_fcff: Base case FCFF forecast
            base_wacc_inputs: Base WACC inputs
            terminal_inputs: Terminal value inputs (must use Gordon Growth)
            shares_outstanding: Shares outstanding
            cash: Cash balance
            debt: Debt balance
            wacc_range: Range for WACC sensitivity (min, max)
            growth_range: Range for growth rate sensitivity (min, max)
            steps: Number of steps in each dimension
            
        Returns:
            DataFrame with sensitivity analysis results
        """
        if terminal_inputs.method.lower() != "gordon":
            raise ValueError("Sensitivity analysis requires Gordon Growth terminal value method")
        
        base_wacc = base_wacc_inputs.risk_free_rate + \
                    base_wacc_inputs.unlevered_beta * base_wacc_inputs.equity_risk_premium
        
        base_growth = terminal_inputs.perpetual_growth_rate
        
        # Create ranges
        wacc_values = np.linspace(
            base_wacc + wacc_range[0],
            base_wacc + wacc_range[1],
            steps
        )
        
        growth_values = np.linspace(
            base_growth + growth_range[0],
            base_growth + growth_range[1],
            steps
        )
        
        # Build sensitivity table
        results = np.zeros((steps, steps))
        
        for i, wacc_adj in enumerate(wacc_values):
            for j, growth in enumerate(growth_values):
                # Adjust WACC inputs
                adjusted_wacc_inputs = WACCInputs(
                    risk_free_rate=wacc_adj - base_wacc_inputs.unlevered_beta * base_wacc_inputs.equity_risk_premium,
                    equity_risk_premium=base_wacc_inputs.equity_risk_premium,
                    unlevered_beta=base_wacc_inputs.unlevered_beta,
                    target_debt_to_equity=base_wacc_inputs.target_debt_to_equity,
                    cost_of_debt=base_wacc_inputs.cost_of_debt,
                    tax_rate=base_wacc_inputs.tax_rate,
                    market_cap=base_wacc_inputs.market_cap,
                    net_debt=base_wacc_inputs.net_debt
                )
                
                # Adjust terminal value inputs
                adjusted_terminal_inputs = TerminalValueInputs(
                    method="gordon",
                    perpetual_growth_rate=growth
                )
                
                # Calculate DCF
                try:
                    result = self.calculate_dcf(
                        fcff_forecast=base_fcff,
                        wacc_inputs=adjusted_wacc_inputs,
                        terminal_inputs=adjusted_terminal_inputs,
                        shares_outstanding=shares_outstanding,
                        cash=cash,
                        debt=debt
                    )
                    results[i, j] = result.value_per_share
                except:
                    results[i, j] = np.nan
        
        # Create DataFrame
        df = pd.DataFrame(
            results,
            index=[f"{w:.2%}" for w in wacc_values],
            columns=[f"{g:.2%}" for g in growth_values]
        )
        df.index.name = "WACC"
        df.columns.name = "Terminal Growth"
        
        logger.info("Sensitivity analysis completed")
        
        return df
    
    def monte_carlo_simulation(
        self,
        fcff_forecast: List[float],
        wacc_inputs: WACCInputs,
        terminal_inputs: TerminalValueInputs,
        shares_outstanding: float,
        cash: float,
        debt: float,
        # Distributions for key parameters
        erp_mean: float = 0.065,
        erp_std: float = 0.02,
        beta_std: float = 0.2,
        growth_std: float = 0.005,
        simulations: int = 10000,
        random_seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Monte Carlo simulation for DCF valuation
        
        Args:
            fcff_forecast: Base FCFF forecast
            wacc_inputs: Base WACC inputs
            terminal_inputs: Terminal value inputs
            shares_outstanding: Shares outstanding
            cash: Cash balance
            debt: Debt balance
            erp_mean: Mean equity risk premium
            erp_std: Std dev of equity risk premium
            beta_std: Std dev of beta
            growth_std: Std dev of perpetual growth rate
            simulations: Number of simulations
            random_seed: Random seed for reproducibility
            
        Returns:
            Dictionary with simulation results and statistics
        """
        if random_seed:
            np.random.seed(random_seed)
        
        logger.info(f"Running Monte Carlo simulation with {simulations} iterations")
        
        results = []
        
        for i in range(simulations):
            # Sample from distributions
            erp_sample = np.random.normal(erp_mean, erp_std)
            beta_sample = max(0.1, np.random.normal(wacc_inputs.unlevered_beta, beta_std))
            
            if terminal_inputs.perpetual_growth_rate:
                growth_sample = np.random.normal(
                    terminal_inputs.perpetual_growth_rate,
                    growth_std
                )
                growth_sample = max(0.0, min(growth_sample, 0.05))  # Bound between 0% and 5%
            else:
                growth_sample = terminal_inputs.perpetual_growth_rate
            
            # Create adjusted inputs
            sim_wacc_inputs = WACCInputs(
                risk_free_rate=wacc_inputs.risk_free_rate,
                equity_risk_premium=erp_sample,
                unlevered_beta=beta_sample,
                target_debt_to_equity=wacc_inputs.target_debt_to_equity,
                cost_of_debt=wacc_inputs.cost_of_debt,
                tax_rate=wacc_inputs.tax_rate,
                market_cap=wacc_inputs.market_cap,
                net_debt=wacc_inputs.net_debt
            )
            
            sim_terminal_inputs = TerminalValueInputs(
                method=terminal_inputs.method,
                perpetual_growth_rate=growth_sample,
                exit_multiple=terminal_inputs.exit_multiple,
                terminal_ebitda=terminal_inputs.terminal_ebitda
            )
            
            # Run DCF
            try:
                result = self.calculate_dcf(
                    fcff_forecast=fcff_forecast,
                    wacc_inputs=sim_wacc_inputs,
                    terminal_inputs=sim_terminal_inputs,
                    shares_outstanding=shares_outstanding,
                    cash=cash,
                    debt=debt
                )
                results.append(result.value_per_share)
            except:
                continue
        
        results = np.array(results)
        
        # Calculate statistics
        statistics = {
            'mean': float(np.mean(results)),
            'median': float(np.median(results)),
            'std': float(np.std(results)),
            'min': float(np.min(results)),
            'max': float(np.max(results)),
            'p10': float(np.percentile(results, 10)),
            'p25': float(np.percentile(results, 25)),
            'p75': float(np.percentile(results, 75)),
            'p90': float(np.percentile(results, 90)),
            'simulations': len(results),
            'results': results.tolist()
        }
        
        logger.info(f"Monte Carlo Results - Mean: ${statistics['mean']:.2f}, "
                   f"P10-P90: ${statistics['p10']:.2f} - ${statistics['p90']:.2f}")
        
        return statistics


# Example usage
if __name__ == "__main__":
    # Initialize engine
    engine = DCFEngine()
    
    # Define inputs
    wacc_inputs = WACCInputs(
        risk_free_rate=0.045,  # 4.5% Treasury
        equity_risk_premium=0.065,  # 6.5% ERP
        unlevered_beta=1.0,
        target_debt_to_equity=0.25,  # 25% D/E
        cost_of_debt=0.05,  # 5% pre-tax
        tax_rate=0.21,  # 21% tax rate
        market_cap=100_000_000,  # $100M market cap
        net_debt=25_000_000  # $25M net debt
    )
    
    terminal_inputs = TerminalValueInputs(
        method="gordon",
        perpetual_growth_rate=0.025  # 2.5% perpetual growth
    )
    
    # Forecast FCFF (5 years)
    fcff_forecast = [
        10_000_000,  # Year 1
        11_000_000,  # Year 2
        12_100_000,  # Year 3
        13_310_000,  # Year 4
        14_641_000   # Year 5
    ]
    
    # Calculate DCF
    result = engine.calculate_dcf(
        fcff_forecast=fcff_forecast,
        wacc_inputs=wacc_inputs,
        terminal_inputs=terminal_inputs,
        shares_outstanding=10_000_000,  # 10M shares
        cash=5_000_000,
        debt=30_000_000
    )
    
    print(f"Enterprise Value: ${result.enterprise_value:,.0f}")
    print(f"Equity Value: ${result.equity_value:,.0f}")
    print(f"Value per Share: ${result.value_per_share:.2f}")
    print(f"WACC: {result.wacc:.2%}")
    
    # Sensitivity analysis
    sensitivity = engine.sensitivity_analysis(
        base_fcff=fcff_forecast,
        base_wacc_inputs=wacc_inputs,
        terminal_inputs=terminal_inputs,
        shares_outstanding=10_000_000,
        cash=5_000_000,
        debt=30_000_000
    )
    print("\nSensitivity Analysis:")
    print(sensitivity)
