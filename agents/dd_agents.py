"""
Due Diligence Agents Suite
Financial QoE, Commercial, Legal/Tax, HR, Tech, ESG agents
Each returns risk cards with severity ratings
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger

from config.schemas import RiskCard
from storage.duckdb_adapter import DuckDBAdapter
from utils.llm_client import LLMClient
from ingestion.sec_client import SECClient


class FinancialQoEAgent:
    """Financial Quality of Earnings Agent"""
    
    def __init__(self):
        self.llm = LLMClient()
        self.db = DuckDBAdapter()
        logger.info("Financial QoE Agent initialized")
    
    def analyze_quality_of_earnings(
        self,
        symbol: str,
        financial_data: Dict[str, Any],
        filing_data: Optional[Dict[str, Any]] = None
    ) -> List[RiskCard]:
        """Analyze financial quality and identify red flags"""
        logger.info(f"Running QoE analysis for {symbol}")
        
        risk_cards = []
        
        # Check revenue recognition
        if isinstance(financial_data.get('revenue'), list) and len(financial_data['revenue']) >= 2:
            revenue_growth = (financial_data['revenue'][-1] / financial_data['revenue'][-2] - 1)
            if revenue_growth > 0.50:
                risk_cards.append(RiskCard(
                    risk_id=f"qoe_{symbol}_rev_spike_{datetime.now().timestamp()}",
                    symbol=symbol,
                    category="Financial",
                    subcategory="Revenue Recognition",
                    severity="High",
                    title="Unusual Revenue Spike",
                    description=f"Revenue grew {revenue_growth:.0%}, significantly above peer average",
                    impact=None,
                    probability=0.6,
                    mitigation="Review revenue recognition policies, check for channel stuffing",
                    source_ref="Financial analysis"
                ))
        
        # Check working capital trends
        if financial_data.get('dso'):
            dso_values = financial_data['dso']
            if isinstance(dso_values, list) and len(dso_values) >= 2:
                dso_increase = dso_values[-1] - dso_values[-2]
                if dso_increase > 10:
                    risk_cards.append(RiskCard(
                        risk_id=f"qoe_{symbol}_dso_{datetime.now().timestamp()}",
                        symbol=symbol,
                        category="Financial",
                        subcategory="Working Capital",
                        severity="Medium",
                        title="Rising Days Sales Outstanding",
                        description=f"DSO increased by {dso_increase:.0f} days, indicating collection issues",
                        impact=None,
                        probability=0.5,
                        mitigation="Review aged receivables, customer credit quality",
                        source_ref="Working capital analysis"
                    ))
        
        # Use LLM for deeper analysis
        if filing_data and filing_data.get('md_a'):
            red_flags = self.llm.generate_red_flags_summary(financial_data, filing_data)
            for flag in red_flags:
                risk_cards.append(RiskCard(
                    risk_id=f"qoe_{symbol}_llm_{datetime.now().timestamp()}",
                    symbol=symbol,
                    category="Financial",
                    subcategory=flag.get('Category', 'Other'),
                    severity=flag.get('Severity', 'Medium'),
                    title=flag.get('Description', 'LLM-identified risk'),
                    description=flag.get('Description', ''),
                    impact=None,
                    probability=None,
                    mitigation=flag.get('Recommended mitigation', ''),
                    source_ref="LLM analysis"
                ))
        
        logger.info(f"QoE analysis complete - {len(risk_cards)} risk cards")
        return risk_cards


class CommercialDDAgent:
    """Commercial Due Diligence Agent"""
    
    def __init__(self):
        self.llm = LLMClient()
        logger.info("Commercial DD Agent initialized")
    
    def analyze_market_position(
        self,
        symbol: str,
        company_data: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> List[RiskCard]:
        """Analyze commercial position and market risks"""
        logger.info(f"Running commercial DD for {symbol}")
        
        risk_cards = []
        
        # Customer concentration
        if market_data.get('customer_concentration'):
            top_customer_pct = market_data['customer_concentration']
            if top_customer_pct > 0.20:
                risk_cards.append(RiskCard(
                    risk_id=f"comm_{symbol}_cust_{datetime.now().timestamp()}",
                    symbol=symbol,
                    category="Commercial",
                    subcategory="Customer Concentration",
                    severity="High" if top_customer_pct > 0.30 else "Medium",
                    title="Customer Concentration Risk",
                    description=f"Top customer represents {top_customer_pct:.0%} of revenue",
                    impact=None,
                    probability=0.4,
                    mitigation="Diversify customer base, longer-term contracts",
                    source_ref="Commercial analysis"
                ))
        
        # Market share trends
        if market_data.get('market_share_trend') == 'declining':
            risk_cards.append(RiskCard(
                risk_id=f"comm_{symbol}_share_{datetime.now().timestamp()}",
                symbol=symbol,
                category="Commercial",
                subcategory="Market Position",
                severity="Medium",
                title="Declining Market Share",
                description="Market share declining versus competitors",
                impact=None,
                probability=0.5,
                mitigation="Assess competitive positioning, pricing strategy",
                source_ref="Market analysis"
            ))
        
        logger.info(f"Commercial DD complete - {len(risk_cards)} risk cards")
        return risk_cards


class LegalTaxDDAgent:
    """Legal & Tax Due Diligence Agent"""
    
    def __init__(self):
        self.llm = LLMClient()
        self.sec = SECClient()
        logger.info("Legal/Tax DD Agent initialized")
    
    def extract_legal_clauses(
        self,
        symbol: str,
        filing_text: str
    ) -> List[RiskCard]:
        """Extract and analyze legal clauses"""
        logger.info(f"Extracting legal clauses for {symbol}")
        
        risk_cards = []
        
        # Use LLM to extract clauses
        clause_types = ['change-of-control', 'indemnity', 'termination', 'assignment']
        clauses = self.llm.extract_clauses(filing_text, clause_types)
        
        for clause in clauses:
            risk_rating = clause.get('risk_rating', 'Low')
            if risk_rating in ['Medium', 'High']:
                risk_cards.append(RiskCard(
                    risk_id=f"legal_{symbol}_clause_{datetime.now().timestamp()}",
                    symbol=symbol,
                    category="Legal",
                    subcategory=clause.get('clause_type', 'Contract'),
                    severity=risk_rating,
                    title=clause.get('title', 'Legal Clause Risk'),
                    description=clause.get('analysis', clause.get('text', '')[:200]),
                    impact=None,
                    probability=None,
                    mitigation="Legal review required",
                    source_ref=clause.get('page_span', 'Filing')
                ))
        
        logger.info(f"Legal DD complete - {len(risk_cards)} risk cards")
        return risk_cards


class TechDDAgent:
    """Technology Due Diligence Agent"""
    
    def __init__(self):
        self.llm = LLMClient()
        logger.info("Tech DD Agent initialized")
    
    def analyze_tech_stack(
        self,
        symbol: str,
        tech_data: Dict[str, Any]
    ) -> List[RiskCard]:
        """Analyze technology stack and IP"""
        logger.info(f"Running tech DD for {symbol}")
        
        risk_cards = []
        
        # Check for tech debt
        if tech_data.get('legacy_systems_pct', 0) > 0.40:
            risk_cards.append(RiskCard(
                risk_id=f"tech_{symbol}_legacy_{datetime.now().timestamp()}",
                symbol=symbol,
                category="Technology",
                subcategory="Technical Debt",
                severity="High",
                title="Significant Legacy Systems",
                description="Over 40% of systems on legacy/end-of-life technology",
                impact=tech_data.get('modernization_cost_estimate'),
                probability=0.8,
                mitigation="Plan technology modernization, assess migration costs",
                source_ref="Tech assessment"
            ))
        
        # IP risks
        if tech_data.get('ip_litigation_pending'):
            risk_cards.append(RiskCard(
                risk_id=f"tech_{symbol}_ip_{datetime.now().timestamp()}",
                symbol=symbol,
                category="Technology",
                subcategory="Intellectual Property",
                severity="High",
                title="Pending IP Litigation",
                description="Active intellectual property disputes identified",
                impact=None,
                probability=0.7,
                mitigation="Legal review of IP portfolio, indemnification clauses",
                source_ref="Legal filings"
            ))
        
        logger.info(f"Tech DD complete - {len(risk_cards)} risk cards")
        return risk_cards


class ESGAgent:
    """ESG (Environmental, Social, Governance) Agent"""
    
    def __init__(self):
        self.llm = LLMClient()
        logger.info("ESG Agent initialized")
    
    def analyze_esg_factors(
        self,
        symbol: str,
        esg_data: Dict[str, Any],
        filing_data: Optional[Dict] = None
    ) -> List[RiskCard]:
        """Analyze ESG factors and risks"""
        logger.info(f"Running ESG analysis for {symbol}")
        
        risk_cards = []
        
        # Environmental risks
        if esg_data.get('carbon_intensity_high'):
            risk_cards.append(RiskCard(
                risk_id=f"esg_{symbol}_carbon_{datetime.now().timestamp()}",
                symbol=symbol,
                category="ESG",
                subcategory="Environmental",
                severity="Medium",
                title="High Carbon Intensity",
                description="Above-average carbon emissions for sector",
                impact=None,
                probability=0.6,
                mitigation="Carbon reduction plan, renewable energy transition",
                source_ref="ESG assessment"
            ))
        
        # Governance risks
        if esg_data.get('board_independence_pct', 100) < 0.50:
            risk_cards.append(RiskCard(
                risk_id=f"esg_{symbol}_board_{datetime.now().timestamp()}",
                symbol=symbol,
                category="ESG",
                subcategory="Governance",
                severity="High",
                title="Poor Board Independence",
                description="Less than 50% independent board members",
                impact=None,
                probability=0.7,
                mitigation="Board restructuring, add independent directors",
                source_ref="Proxy statement"
            ))
        
        logger.info(f"ESG analysis complete - {len(risk_cards)} risk cards")
        return risk_cards


class HRDDAgent:
    """Human Resources Due Diligence Agent"""
    
    def __init__(self):
        self.llm = LLMClient()
        logger.info("HR DD Agent initialized")
    
    def analyze_hr_factors(
        self,
        symbol: str,
        hr_data: Dict[str, Any]
    ) -> List[RiskCard]:
        """Analyze HR and cultural factors"""
        logger.info(f"Running HR DD for {symbol}")
        
        risk_cards = []
        
        # Turnover risks
        if hr_data.get('employee_turnover_pct', 0) > 0.25:
            risk_cards.append(RiskCard(
                risk_id=f"hr_{symbol}_turnover_{datetime.now().timestamp()}",
                symbol=symbol,
                category="HR",
                subcategory="Talent Retention",
                severity="High",
                title="High Employee Turnover",
                description=f"Turnover rate of {hr_data['employee_turnover_pct']:.0%} exceeds industry norm",
                impact=None,
                probability=0.7,
                mitigation="Retention programs, compensation review, culture assessment",
                source_ref="HR data"
            ))
        
        # Key person dependency
        if hr_data.get('key_person_dependency'):
            risk_cards.append(RiskCard(
                risk_id=f"hr_{symbol}_keyperson_{datetime.now().timestamp()}",
                symbol=symbol,
                category="HR",
                subcategory="Key Person Risk",
                severity="High",
                title="Key Person Dependency",
                description="Business heavily dependent on specific individuals",
                impact=None,
                probability=0.5,
                mitigation="Succession planning, knowledge transfer programs",
                source_ref="Organizational assessment"
            ))
        
        logger.info(f"HR DD complete - {len(risk_cards)} risk cards")
        return risk_cards


class DDAgentsSuite:
    """
    Complete DD Agents Suite - coordinates all diligence agents
    
    Agents:
    - Financial QoE
    - Commercial
    - Legal/Tax
    - HR/Culture
    - Technology/IP
    - ESG
    """
    
    def __init__(self):
        """Initialize all DD agents"""
        self.financial_qoe = FinancialQoEAgent()
        self.commercial = CommercialDDAgent()
        self.legal_tax = LegalTaxDDAgent()
        self.tech = TechDDAgent()
        self.esg = ESGAgent()
        self.hr = HRDDAgent()
        
        logger.info("DD Agents Suite initialized - 6 agents ready")
    
    async def run_full_dd(
        self,
        symbol: str,
        financial_data: Dict[str, Any],
        filing_data: Optional[Dict] = None,
        market_data: Optional[Dict] = None,
        tech_data: Optional[Dict] = None,
        esg_data: Optional[Dict] = None,
        hr_data: Optional[Dict] = None
    ) -> Dict[str, List[RiskCard]]:
        """
        Run comprehensive due diligence across all areas
        
        Args:
            symbol: Stock symbol
            financial_data: Financial metrics and statements
            filing_data: SEC filing data
            market_data: Market and commercial data
            tech_data: Technology assessment data
            esg_data: ESG metrics
            hr_data: HR data
            
        Returns:
            Dictionary of risk cards by category
        """
        logger.info(f"Running comprehensive DD for {symbol}")
        
        results = {}
        
        # Financial QoE
        results['financial'] = self.financial_qoe.analyze_quality_of_earnings(
            symbol, financial_data, filing_data
        )
        
        # Commercial
        if market_data:
            results['commercial'] = self.commercial.analyze_market_position(
                symbol, financial_data, market_data
            )
        
        # Legal/Tax
        if filing_data and filing_data.get('full_text'):
            results['legal'] = self.legal_tax.extract_legal_clauses(
                symbol, filing_data['full_text']
            )
        
        # Technology
        if tech_data:
            results['tech'] = self.tech.analyze_tech_stack(symbol, tech_data)
        
        # ESG
        if esg_data:
            results['esg'] = self.esg.analyze_esg_factors(symbol, esg_data, filing_data)
        
        # HR
        if hr_data:
            results['hr'] = self.hr.analyze_hr_factors(symbol, hr_data)
        
        # Calculate total risks
        all_risks = []
        for category, risks in results.items():
            all_risks.extend(risks)
        
        logger.info(f"Full DD complete - {len(all_risks)} total risk cards")
        
        return results
    
    def generate_dd_summary(
        self,
        dd_results: Dict[str, List[RiskCard]]
    ) -> Dict[str, Any]:
        """
        Generate DD summary report
        
        Args:
            dd_results: DD results by category
            
        Returns:
            Summary statistics
        """
        total_risks = sum(len(risks) for risks in dd_results.values())
        
        severity_counts = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}
        for risks in dd_results.values():
            for risk in risks:
                severity_counts[risk.severity] = severity_counts.get(risk.severity, 0) + 1
        
        summary = {
            'total_risks': total_risks,
            'by_severity': severity_counts,
            'by_category': {cat: len(risks) for cat, risks in dd_results.items()},
            'critical_risks': [
                risk for risks in dd_results.values() for risk in risks 
                if risk.severity in ['Critical', 'High']
            ]
        }
        
        return summary


# Example usage
if __name__ == "__main__":
    import asyncio
    
    # Initialize DD suite
    suite = DDAgentsSuite()
    
    print("\n" + "="*70)
    print("DUE DILIGENCE AGENTS SUITE")
    print("="*70)
    
    # Sample data
    financial_data = {
        'revenue': [1_000_000_000, 1_100_000_000, 1_800_000_000],  # Spike!
        'dso': [45, 47, 62],  # Rising DSO
        'inventory_turnover': [8.5, 8.2, 7.1]
    }
    
    market_data = {
        'customer_concentration': 0.35,  # 35% from top customer
        'market_share_trend': 'declining'
    }
    
    tech_data = {
        'legacy_systems_pct': 0.55,
        'ip_litigation_pending': True
    }
    
    esg_data = {
        'carbon_intensity_high': True,
        'board_independence_pct': 0.40
    }
    
    hr_data = {
        'employee_turnover_pct': 0.30,
        'key_person_dependency': True
    }
    
    # Run full DD
    results = asyncio.run(suite.run_full_dd(
        symbol="TARGET",
        financial_data=financial_data,
        market_data=market_data,
        tech_data=tech_data,
        esg_data=esg_data,
        hr_data=hr_data
    ))
    
    # Generate summary
    summary = suite.generate_dd_summary(results)
    
    print(f"\nDD Summary:")
    print(f"  Total Risks: {summary['total_risks']}")
    print(f"  By Severity: {summary['by_severity']}")
    print(f"  By Category: {summary['by_category']}")
    
    print(f"\nCritical/High Risks:")
    for risk in summary['critical_risks']:
        print(f"  - [{risk.severity}] {risk.title} ({risk.category})")
