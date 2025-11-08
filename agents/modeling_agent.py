"""
Modeling Agent
Orchestrates valuation models (DCF, CCA, LBO, Merger, Growth Scenarios)
Uses all 5 modeling engines to produce comprehensive valuations
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
import asyncio
from loguru import logger

from engines import (
    DCFEngine, WACCInputs, TerminalValueInputs, DCFResult,
    CCAEngine, PeerMetrics, CCAResult,
    LBOEngine, LBOInputs, LBOResult, DebtTranche,
    MergerModel, MergerInputs, MergerResult, CompanyFinancials,
    GrowthScenariosEngine, GrowthScenarioInputs, GrowthStage, Industry
)
from storage.duckdb_adapter import DuckDBAdapter
from storage.cognee_adapter import CogneeAdapter
from storage.memory_manager import MemoryManager, AnalysisMemory
from utils.llm_client import LLMClient


@dataclass
class ValuationPackage:
    """Complete valuation package output"""
    symbol: str
    company_name: str
    timestamp: datetime
    
    # Valuations
    dcf_result: Optional[DCFResult] = None
    cca_result: Optional[CCAResult] = None
    lbo_result: Optional[LBOResult] = None
    merger_result: Optional[MergerResult] = None
    three_statement_result: Optional[Any] = None
    growth_scenarios: Optional[Dict[str, Any]] = None
    
    # Summary
    valuation_range: Optional[Tuple[float, float]] = None
    recommended_value: Optional[float] = None
    confidence_level: str = "Medium"
    
    # Insights
    key_drivers: List[str] = None
    risk_factors: List[str] = None
    llm_summary: str = ""


class ModelingAgent:
    """
    Modeling Agent - orchestrates all valuation engines
    
    Responsibilities:
    - Run DCF, CCA, LBO, Merger, Growth Scenarios
    - Synthesize results into valuation range
    - Generate LLM-powered insights
    - Store results in Cognee
    """
    
    def __init__(self):
        """Initialize modeling agent with all engines"""
        self.dcf_engine = DCFEngine()
        self.cca_engine = CCAEngine()
        self.lbo_engine = LBOEngine()
        self.merger_model = MergerModel()
        self.growth_engine = GrowthScenariosEngine()
        
        self.db = DuckDBAdapter()
        self.cognee = CogneeAdapter()
        self.memory = MemoryManager()
        self.llm = LLMClient()
        
        logger.info("Modeling Agent initialized with all 5 engines + MemoryManager")
    
    def run_dcf_valuation(
        self,
        symbol: str,
        fcff_forecast: List[float],
        wacc_inputs: WACCInputs,
        terminal_inputs: TerminalValueInputs,
        shares_outstanding: float,
        cash: float,
        debt: float
    ) -> DCFResult:
        """
        Run DCF valuation
        
        Args:
            symbol: Stock symbol
            fcff_forecast: Forecasted free cash flows
            wacc_inputs: WACC calculation inputs
            terminal_inputs: Terminal value inputs
            shares_outstanding: Shares outstanding
            cash: Cash balance
            debt: Debt balance
            
        Returns:
            DCFResult
        """
        logger.info(f"Running DCF for {symbol}")
        
        result = self.dcf_engine.calculate_dcf(
            fcff_forecast=fcff_forecast,
            wacc_inputs=wacc_inputs,
            terminal_inputs=terminal_inputs,
            shares_outstanding=shares_outstanding,
            cash=cash,
            debt=debt
        )
        
        logger.info(f"DCF Complete - Value/Share: ${result.value_per_share:.2f}")
        return result
    
    def run_cca_valuation(
        self,
        symbol: str,
        target_metrics: Dict[str, float],
        peers: List[PeerMetrics],
        shares_outstanding: float,
        net_debt: float
    ) -> CCAResult:
        """
        Run Comparable Company Analysis
        
        Args:
            symbol: Stock symbol
            target_metrics: Target company metrics
            peers: List of peer companies
            shares_outstanding: Shares outstanding
            net_debt: Net debt
            
        Returns:
            CCAResult
        """
        logger.info(f"Running CCA for {symbol} with {len(peers)} peers")
        
        result = self.cca_engine.calculate_valuation(
            target_symbol=symbol,
            target_metrics=target_metrics,
            peers=peers,
            shares_outstanding=shares_outstanding,
            net_debt=net_debt,
            use_winsorization=True
        )
        
        logger.info(f"CCA Complete - Value/Share (EV/EBITDA): ${result.value_per_share_ebitda:.2f}")
        return result
    
    def run_lbo_analysis(
        self,
        symbol: str,
        lbo_inputs: LBOInputs
    ) -> LBOResult:
        """
        Run LBO analysis
        
        Args:
            symbol: Stock symbol
            lbo_inputs: LBO model inputs
            
        Returns:
            LBOResult
        """
        logger.info(f"Running LBO analysis for {symbol}")
        
        result = self.lbo_engine.calculate_lbo_returns(lbo_inputs)
        
        logger.info(f"LBO Complete - IRR: {result.equity_irr:.1%}, MoIC: {result.equity_moic:.2f}x")
        return result
    
    def run_growth_scenarios(
        self,
        symbol: str,
        inputs: GrowthScenarioInputs
    ) -> Dict[str, Any]:
        """
        Run growth scenario analysis
        
        Args:
            symbol: Stock symbol
            inputs: Growth scenario inputs
            
        Returns:
            Dictionary with Bull/Base/Bear scenarios
        """
        logger.info(f"Running growth scenarios for {symbol}")
        
        scenarios = self.growth_engine.compare_scenarios(inputs)
        
        logger.info(f"Scenarios Complete - {len(scenarios)} cases analyzed")
        return scenarios
    
    def detect_growth_stage(
        self,
        revenue: float,
        revenue_growth: float,
        fcf: float,
        ebitda_margin: float
    ) -> tuple:
        """
        Detect company growth stage and determine valuation strategy
        
        Returns:
            (GrowthStage, strategy_dict with weights and guidance)
        """
        fcf_margin = fcf / revenue if revenue > 0 else -1
        
        if revenue_growth > 0.40 and fcf_margin < 0:
            stage = "HYPERGROWTH"
            strategy = {
                'dcf_weight': 0.10,  # Low - unreliable with negative FCF
                'cca_weight': 0.80,  # Primary - revenue multiples
                'scenarios_weight': 0.10,
                'primary_method': 'CCA Revenue Multiple',
                'guidance': 'Hypergrowth company - trust revenue multiples over DCF',
                'dcf_note': 'DCF less reliable due to negative/volatile cash flows',
                'cca_note': 'Revenue multiples primary valuation method',
                'trust_levels': {'DCF': 'LOW', 'CCA': 'HIGH', 'Scenarios': 'MEDIUM'}
            }
        elif revenue_growth >= 0.20 and fcf_margin >= 0:
            stage = "GROWTH"
            strategy = {
                'dcf_weight': 0.30,  # Secondary - volatility
                'cca_weight': 0.60,  # Primary - growth-adjusted
                'scenarios_weight': 0.10,
                'primary_method': 'Growth-Adjusted CCA',
                'guidance': 'High-growth company - blend CCA (60%) and DCF (30%)',
                'dcf_note': 'Use DCF with conservative terminal assumptions',
                'cca_note': 'Apply growth/ROIC regression adjustments',
                'trust_levels': {'DCF': 'MEDIUM', 'CCA': 'HIGH', 'Scenarios': 'MEDIUM'}
            }
        elif revenue_growth >= 0.05:
            stage = "MATURE"
            strategy = {
                'dcf_weight': 0.60,  # Primary - reliable FCF
                'cca_weight': 0.30,  # Validation
                'lbo_weight': 0.10,  # Floor value
                'primary_method': 'Discounted Cash Flow',
                'guidance': 'Mature company - DCF primary with CCA validation',
                'dcf_note': 'Primary valuation method - stable cash flows',
                'cca_note': 'Use for peer validation',
                'trust_levels': {'DCF': 'HIGH', 'CCA': 'MEDIUM', 'LBO': 'LOW'}
            }
        else:
            stage = "DECLINE"
            strategy = {
                'dcf_weight': 0.0,  # Not applicable
                'cca_weight': 0.50,  # Distressed discount
                'liquidation_weight': 0.50,
                'primary_method': 'Distressed Valuation',
                'guidance': 'Declining/distressed - use liquidation + distressed multiples',
                'dcf_note': 'DCF not applicable - going concern questionable',
                'cca_note': 'Apply 40-50% discount to peer multiples',
                'trust_levels': {'DCF': 'NONE', 'CCA': 'MEDIUM', 'Liquidation': 'HIGH'}
            }
        
        logger.info(f"Growth Stage Detected: {stage}")
        logger.info(f"  Primary Method: {strategy['primary_method']}")
        logger.info(f"  Weighting: DCF={strategy.get('dcf_weight', 0):.0%}, "
                   f"CCA={strategy.get('cca_weight', 0):.0%}")
        
        return stage, strategy
    

    def build_valuation_package(
        self,
        symbol: str,
        company_name: str,
        dcf_result: Optional[DCFResult] = None,
        cca_result: Optional[CCAResult] = None,
        lbo_result: Optional[LBOResult] = None,
        growth_scenarios: Optional[Dict] = None,
        merger_result: Optional[Any] = None,
        three_statement_result: Optional[Any] = None
    ) -> ValuationPackage:
        """
        Build comprehensive valuation package
        
        Args:
            symbol: Stock symbol
            company_name: Company name
            dcf_result: DCF result
            cca_result: CCA result
            lbo_result: LBO result
            growth_scenarios: Growth scenarios
            
        Returns:
            ValuationPackage with synthesized analysis
        """
        logger.info(f"Building valuation package for {symbol}")
        
        # Collect all valuations
        valuations = []
        
        if dcf_result:
            valuations.append(("DCF", dcf_result.value_per_share))
        
        if cca_result:
            valuations.append(("CCA - EV/Revenue", cca_result.value_per_share_revenue))
            valuations.append(("CCA - EV/EBITDA", cca_result.value_per_share_ebitda))
            valuations.append(("CCA - P/E", cca_result.value_per_share_pe))
        
        # Calculate valuation range
        if valuations:
            values = [v[1] for v in valuations]
            valuation_range = (min(values), max(values))
            recommended_value = sum(values) / len(values)  # Average
        else:
            valuation_range = None
            recommended_value = None
        
        # Generate LLM summary
        llm_summary = self._generate_llm_summary(
            symbol, dcf_result, cca_result, lbo_result, growth_scenarios
        )
        
        # Identify key drivers and risks
        key_drivers = self._identify_key_drivers(dcf_result, cca_result)
        risk_factors = self._identify_risk_factors(growth_scenarios, lbo_result)
        
        package = ValuationPackage(
            symbol=symbol,
            company_name=company_name,
            timestamp=datetime.utcnow(),
            dcf_result=dcf_result,
            cca_result=cca_result,
            lbo_result=lbo_result,
            growth_scenarios=growth_scenarios,
            merger_result=merger_result,
            three_statement_result=three_statement_result,
            valuation_range=valuation_range,
            recommended_value=recommended_value,
            key_drivers=key_drivers,
            risk_factors=risk_factors,
            llm_summary=llm_summary
        )
        
        logger.info(f"Valuation Package Complete - Range: ${valuation_range[0]:.2f} - ${valuation_range[1]:.2f}")
        
        return package
    
    def _generate_llm_summary(
        self,
        symbol: str,
        dcf_result: Optional[DCFResult],
        cca_result: Optional[CCAResult],
        lbo_result: Optional[LBOResult],
        growth_scenarios: Optional[Dict]
    ) -> str:
        """Generate LLM-powered valuation summary"""
        
        summary_data = {
            "symbol": symbol,
            "dcf_value": dcf_result.value_per_share if dcf_result else None,
            "dcf_wacc": f"{dcf_result.wacc:.2%}" if dcf_result else None,
            "cca_ebitda_value": cca_result.value_per_share_ebitda if cca_result else None,
            "cca_peers": cca_result.peer_count if cca_result else None,
            "lbo_irr": f"{lbo_result.equity_irr:.1%}" if lbo_result else None,
            "lbo_moic": f"{lbo_result.equity_moic:.2f}x" if lbo_result else None,
            "growth_stage": growth_scenarios['Base'].growth_stage.value if growth_scenarios else None
        }
        
        prompt = f"""Synthesize this valuation analysis for {symbol}:

{summary_data}

Provide:
1. Overall valuation conclusion
2. Key value drivers
3. Main risks
4. Investment recommendation

Format as concise executive summary (3-4 paragraphs)."""
        
        try:
            summary = self.llm.chat(
                messages=[
                    {"role": "system", "content": "You are a senior investment banker providing valuation summaries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            return summary
        except Exception as e:
            logger.error(f"LLM summary failed: {str(e)}")
            return "Valuation analysis complete. See detailed results above."
    
    def _identify_key_drivers(
        self,
        dcf_result: Optional[DCFResult],
        cca_result: Optional[CCAResult]
    ) -> List[str]:
        """Identify key value drivers"""
        drivers = []
        
        if dcf_result:
            if dcf_result.wacc < 0.08:
                drivers.append("Low WACC (favorable cost of capital)")
            if dcf_result.pv_terminal_value / dcf_result.enterprise_value > 0.7:
                drivers.append("Terminal value represents >70% of value")
        
        if cca_result:
            if cca_result.peer_count >= 5:
                drivers.append(f"Strong peer set ({cca_result.peer_count} comparables)")
        
        if not drivers:
            drivers.append("Standard valuation assumptions")
        
        return drivers
    
    def _identify_risk_factors(
        self,
        growth_scenarios: Optional[Dict],
        lbo_result: Optional[LBOResult]
    ) -> List[str]:
        """Identify key risk factors"""
        risks = []
        
        if growth_scenarios and 'Base' in growth_scenarios:
            base_scenario = growth_scenarios['Base']
            if base_scenario.bankruptcy_probability > 0.3:
                risks.append(f"Elevated bankruptcy risk ({base_scenario.bankruptcy_probability:.0%})")
        
        if lbo_result:
            if lbo_result.equity_irr < 0.15:
                risks.append(f"Below-target IRR ({lbo_result.equity_irr:.1%} vs 15%+ target)")
        
        if not risks:
            risks.append("Standard market risks apply")
        
        return risks
    
    async def store_valuation_in_memory(
        self,
        package: ValuationPackage
    ) -> bool:
        """
        Store valuation package in MemoryManager (DuckDB + ChromaDB)
        NOW INCLUDES: Monte Carlo, LBO Sensitivity, Merger Sensitivity
        
        Args:
            package: ValuationPackage to store
            
        Returns:
            Success status
        """
        try:
            # Prepare results dictionary with NEW activated features
            results = {
                'valuation_range': {
                    'low': package.valuation_range[0] if package.valuation_range else None,
                    'high': package.valuation_range[1] if package.valuation_range else None
                },
                'recommended_value': package.recommended_value,
                'dcf': {
                    'value_per_share': package.dcf_result.value_per_share if package.dcf_result else None,
                    'wacc': package.dcf_result.wacc if package.dcf_result else None,
                    'enterprise_value': package.dcf_result.enterprise_value if package.dcf_result else None,
                    # ACTIVATION: Monte Carlo uncertainty results
                    'monte_carlo': {
                        'mean': package.dcf_result.monte_carlo.get('mean') if hasattr(package.dcf_result, 'monte_carlo') else None,
                        'median': package.dcf_result.monte_carlo.get('median') if hasattr(package.dcf_result, 'monte_carlo') else None,
                        'p10': package.dcf_result.monte_carlo.get('p10') if hasattr(package.dcf_result, 'monte_carlo') else None,
                        'p90': package.dcf_result.monte_carlo.get('p90') if hasattr(package.dcf_result, 'monte_carlo') else None,
                        'std': package.dcf_result.monte_carlo.get('std') if hasattr(package.dcf_result, 'monte_carlo') else None
                    } if package.dcf_result and hasattr(package.dcf_result, 'monte_carlo') else None
                } if package.dcf_result else None,
                'cca': {
                    'value_per_share_ebitda': package.cca_result.value_per_share_ebitda if package.cca_result else None,
                    'value_per_share_revenue': package.cca_result.value_per_share_revenue if package.cca_result else None,
                    'peer_count': package.cca_result.peer_count if package.cca_result else None
                } if package.cca_result else None,
                'lbo': {
                    'equity_irr': package.lbo_result.equity_irr if package.lbo_result else None,
                    'equity_moic': package.lbo_result.equity_moic if package.lbo_result else None,
                    # ACTIVATION: LBO sensitivity available
                    'has_sensitivity': hasattr(package.lbo_result, 'sensitivity') if package.lbo_result else False
                } if package.lbo_result else None,
                'merger': {
                    'accretion_dilution_pct': package.merger_result.accretion_dilution_pct if package.merger_result and hasattr(package.merger_result, 'accretion_dilution_pct') else None,
                    'is_accretive': package.merger_result.is_accretive if package.merger_result and hasattr(package.merger_result, 'is_accretive') else None,
                    # ACTIVATION: Merger sensitivity available
                    'has_sensitivity': hasattr(package.merger_result, 'sensitivity') if package.merger_result else False
                } if package.merger_result else None,
                'key_drivers': package.key_drivers,
                'risk_factors': package.risk_factors,
                'llm_summary': package.llm_summary
            }
            
            # Create AnalysisMemory object
            memory = AnalysisMemory(
                session_id=f"valuation_{package.symbol}_{package.timestamp.strftime('%Y%m%d_%H%M%S')}",
                ticker=package.symbol,
                timestamp=package.timestamp,
                context={
                    'company_name': package.company_name,
                    'analysis_type': 'comprehensive_valuation',
                    'timestamp': package.timestamp.isoformat()
                },
                results=results,
                metadata={
                    'confidence_level': package.confidence_level,
                    'models_used': [
                        'DCF' if package.dcf_result else None,
                        'CCA' if package.cca_result else None,
                        'LBO' if package.lbo_result else None,
                        'Growth' if package.growth_scenarios else None
                    ]
                }
            )
            
            # Store in MemoryManager
            success = self.memory.store_analysis(memory)
            
            if success:
                logger.info(f"Valuation package stored in MemoryManager for {package.symbol}")
            else:
                logger.warning(f"Failed to store valuation in MemoryManager for {package.symbol}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error storing in MemoryManager: {str(e)}")
            return False
    
    def close(self):
        """Clean up resources"""
        try:
            self.db.close()
            logger.info("Modeling agent resources closed")
        except Exception as e:
            logger.error(f"Error closing resources: {str(e)}")


# Example usage
if __name__ == "__main__":
    import asyncio
    
    # Initialize agent
    agent = ModelingAgent()
    
    print("\n" + "="*70)
    print("MODELING AGENT - COMPREHENSIVE VALUATION")
    print("="*70)
    
    symbol = "AAPL"
    company_name = "Apple Inc."
    
    # 1. Run DCF
    print(f"\n[1/3] Running DCF valuation...")
    wacc_inputs = WACCInputs(
        risk_free_rate=0.045,
        equity_risk_premium=0.065,
        unlevered_beta=1.2,
        target_debt_to_equity=0.15,
        cost_of_debt=0.038,
        tax_rate=0.15,
        market_cap=2_800_000_000_000,
        net_debt=-50_000_000_000
    )
    
    terminal_inputs = TerminalValueInputs(
        method="gordon",
        perpetual_growth_rate=0.025
    )
    
    fcff_forecast = [100_000_000_000, 108_000_000_000, 116_640_000_000, 
                     125_971_000_000, 136_049_000_000]
    
    dcf_result = agent.run_dcf_valuation(
        symbol=symbol,
        fcff_forecast=fcff_forecast,
        wacc_inputs=wacc_inputs,
        terminal_inputs=terminal_inputs,
        shares_outstanding=15_500_000_000,
        cash=165_000_000_000,
        debt=115_000_000_000
    )
    
    # 2. Run CCA
    print(f"\n[2/3] Running CCA valuation...")
    peers = [
        PeerMetrics(
            symbol="MSFT",
            company_name="Microsoft",
            market_cap=2_750_000_000_000,
            enterprise_value=2_700_000_000_000,
            revenue=211_900_000_000,
            ebitda=101_000_000_000,
            ebit=88_500_000_000,
            net_income=72_400_000_000,
            revenue_growth=0.12,
            roic=0.30,
            sector="Technology"
        )
    ]
    
    target_metrics = {
        'revenue': 383_300_000_000,
        'ebitda': 123_000_000_000,
        'ebit': 114_000_000_000,
        'net_income': 97_000_000_000,
        'revenue_growth': 0.08,
        'roic': 0.45
    }
    
    cca_result = agent.run_cca_valuation(
        symbol=symbol,
        target_metrics=target_metrics,
        peers=peers,
        shares_outstanding=15_500_000_000,
        net_debt=-50_000_000_000
    )
    
    # 3. Build valuation package
    print(f"\n[3/3] Building valuation package...")
    package = agent.build_valuation_package(
        symbol=symbol,
        company_name=company_name,
        dcf_result=dcf_result,
        cca_result=cca_result
    )
    
    # Display results
    print("\n" + "="*70)
    print("VALUATION PACKAGE SUMMARY")
    print("="*70)
    print(f"\nValuation Range: ${package.valuation_range[0]:.2f} - ${package.valuation_range[1]:.2f}")
    print(f"Recommended Value: ${package.recommended_value:.2f}")
    print(f"Confidence Level: {package.confidence_level}")
    
    print(f"\nKey Drivers:")
    for driver in package.key_drivers:
        print(f"  • {driver}")
    
    print(f"\nRisk Factors:")
    for risk in package.risk_factors:
        print(f"  • {risk}")
    
    print(f"\nLLM Summary:")
    print(package.llm_summary)
    
    # Store in MemoryManager
    print(f"\n[4/4] Storing in MemoryManager...")
    asyncio.run(agent.store_valuation_in_memory(package))
    print("✓ Valuation stored in DuckDB")
    
    agent.close()
