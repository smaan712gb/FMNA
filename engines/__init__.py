"""
Modeling Engines - Complete financial modeling and valuation suite
"""

from engines.dcf_engine import DCFEngine, WACCInputs, TerminalValueInputs, DCFResult
from engines.cca_engine import CCAEngine, PeerMetrics, CCAResult
from engines.lbo_engine import LBOEngine, LBOInputs, LBOResult, DebtTranche
from engines.merger_model import MergerModel, MergerInputs, MergerResult, CompanyFinancials
from engines.growth_scenarios import (
    GrowthScenariosEngine, 
    GrowthScenarioInputs, 
    ScenarioResult,
    GrowthStage,
    Industry,
    SaaSMetrics,
    DistressMetrics
)
from engines.three_statement_model import IntegratedThreeStatementModel, DriverInputs, ThreeStatementResult

# Alias for compatibility
ThreeStatementModel = IntegratedThreeStatementModel

__all__ = [
    # DCF
    'DCFEngine',
    'WACCInputs',
    'TerminalValueInputs',
    'DCFResult',
    # CCA
    'CCAEngine',
    'PeerMetrics',
    'CCAResult',
    # LBO
    'LBOEngine',
    'LBOInputs',
    'LBOResult',
    'DebtTranche',
    # Merger
    'MergerModel',
    'MergerInputs',
    'MergerResult',
    'CompanyFinancials',
    # Growth Scenarios
    'GrowthScenariosEngine',
    'GrowthScenarioInputs',
    'ScenarioResult',
    'GrowthStage',
    'Industry',
    'SaaSMetrics',
    'DistressMetrics',
    # 3-Statement
    'ThreeStatementModel',
    'DriverInputs',
    'ThreeStatementResult'
]
