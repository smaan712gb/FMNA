"""
AI-Powered Smart Valuation Engine
Adapts valuation methodologies based on company type, sector, stage, and business model
Uses LLM to intelligently classify companies and select appropriate valuation frameworks
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
import json

try:
    from utils.llm_client import LLMClient
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    logger.warning("LLM client not available - AI classification will use rule-based fallback")


class CompanyType(str, Enum):
    """Company type classifications"""
    SAAS_SOFTWARE = "saas_software"
    ECOMMERCE_MARKETPLACE = "ecommerce_marketplace"
    BIOTECH_PHARMA = "biotech_pharma"
    MEDTECH_DEVICES = "medtech_devices"
    FINTECH_PAYMENTS = "fintech_payments"
    HARDWARE_SEMICONDUCTORS = "hardware_semiconductors"
    CONSUMER_BRANDS = "consumer_brands"
    INDUSTRIAL_MANUFACTURING = "industrial_manufacturing"
    ENERGY_UTILITIES = "energy_utilities"
    REAL_ESTATE = "real_estate"
    MEDIA_ENTERTAINMENT = "media_entertainment"
    TELECOM_NETWORKS = "telecom_networks"
    DRUG_DISCOVERY = "drug_discovery"
    CLINICAL_STAGE_BIOTECH = "clinical_stage_biotech"
    INFRASTRUCTURE = "infrastructure"


class DevelopmentStage(str, Enum):
    """Development stage classifications"""
    # General stages
    PRE_REVENUE = "pre_revenue"
    EARLY_REVENUE = "early_revenue"
    HYPERGROWTH = "hypergrowth"
    GROWTH = "growth"
    MATURE = "mature"
    DECLINE = "decline"
    DISTRESS = "distress"
    
    # Biotech/Pharma specific
    PRECLINICAL = "preclinical"
    PHASE_1 = "phase_1"
    PHASE_2 = "phase_2"
    PHASE_3 = "phase_3"
    COMMERCIALIZATION = "commercialization"
    
    # Hardware specific
    PROTOTYPE = "prototype"
    PILOT_PRODUCTION = "pilot_production"
    MASS_PRODUCTION = "mass_production"


@dataclass
class ValuationMethodology:
    """Valuation methodology configuration"""
    method_name: str
    use: bool
    weight: float
    reason: str
    config: Dict[str, Any] = field(default_factory=dict)
    focus_multiples: List[str] = field(default_factory=list)
    

@dataclass
class CompanyProfile:
    """Company classification and profile"""
    company_name: str
    company_type: CompanyType
    development_stage: DevelopmentStage
    sector_specific_metrics: Dict[str, Any]
    key_value_drivers: List[str]
    valuation_methodologies: List[ValuationMethodology]
    classification_confidence: float
    reasoning: str


@dataclass
class SectorSpecificMetrics:
    """Sector-specific metrics for different company types"""
    
    # SaaS metrics
    arr: Optional[float] = None
    nrr: Optional[float] = None
    ltv_cac_ratio: Optional[float] = None
    magic_number: Optional[float] = None
    rule_of_40: Optional[float] = None
    
    # Biotech/Pharma metrics
    pipeline_value: Optional[float] = None
    phase_1_assets: Optional[int] = None
    phase_2_assets: Optional[int] = None
    phase_3_assets: Optional[int] = None
    peak_sales_potential: Optional[float] = None
    years_to_market: Optional[int] = None
    probability_of_success: Optional[float] = None
    rd_efficiency: Optional[float] = None
    
    # Hardware/Semiconductor metrics
    gross_margin: Optional[float] = None
    inventory_turns: Optional[float] = None
    capex_intensity: Optional[float] = None
    r_and_d_pct_revenue: Optional[float] = None
    
    # E-commerce/Marketplace metrics
    gmv: Optional[float] = None  # Gross Merchandise Value
    take_rate: Optional[float] = None
    cohort_retention: Optional[float] = None
    customer_payback_period: Optional[int] = None


class AIValuationEngine:
    """AI-Powered Smart Valuation Engine"""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize AI valuation engine
        
        Args:
            llm_client: Optional LLMClient instance. If not provided, will create one from settings.
        """
        if LLM_AVAILABLE:
            if llm_client:
                self.llm = llm_client
            else:
                try:
                    self.llm = LLMClient()
                    logger.info("AI Valuation Engine initialized with DeepSeek LLM support")
                except Exception as e:
                    logger.warning(f"Failed to initialize LLM client: {e}, using rule-based fallback")
                    self.llm = None
        else:
            self.llm = None
            logger.info("AI Valuation Engine initialized with rule-based fallback")
    
    def classify_company(
        self,
        company_name: str,
        description: str,
        industry: str,
        revenue: float,
        revenue_growth: float,
        ebitda: float,
        fcf: float,
        rd_expense: float,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> CompanyProfile:
        """
        Use AI to classify company and determine appropriate valuation methodology
        
        Args:
            company_name: Company name
            description: Business description
            industry: Industry classification
            revenue: Current revenue
            revenue_growth: Revenue growth rate
            ebitda: EBITDA
            fcf: Free cash flow
            rd_expense: R&D expense
            additional_context: Additional context (products, pipeline, etc.)
            
        Returns:
            CompanyProfile with classification and valuation strategy
        """
        if self.llm:
            return self._classify_with_llm(
                company_name, description, industry, revenue, 
                revenue_growth, ebitda, fcf, rd_expense, additional_context
            )
        else:
            return self._classify_rule_based(
                company_name, description, industry, revenue,
                revenue_growth, ebitda, fcf, rd_expense, additional_context
            )
    
    def _classify_with_llm(
        self,
        company_name: str,
        description: str,
        industry: str,
        revenue: float,
        revenue_growth: float,
        ebitda: float,
        fcf: float,
        rd_expense: float,
        additional_context: Optional[Dict[str, Any]]
    ) -> CompanyProfile:
        """Use LLM to intelligently classify company and determine valuation approach"""
        
        context_str = json.dumps(additional_context, indent=2) if additional_context else "None"
        
        prompt = f"""You are a senior investment banker and valuation expert. Analyze this company and determine the most appropriate valuation methodology.

Company: {company_name}
Description: {description}
Industry: {industry}

Financial Metrics:
- Revenue: ${revenue:,.0f}
- Revenue Growth: {revenue_growth:.1%}
- EBITDA: ${ebitda:,.0f}
- EBITDA Margin: {(ebitda/revenue*100 if revenue > 0 else 0):.1f}%
- FCF: ${fcf:,.0f}
- FCF Margin: {(fcf/revenue*100 if revenue > 0 else 0):.1f}%
- R&D Expense: ${rd_expense:,.0f}
- R&D % Revenue: {(rd_expense/revenue*100 if revenue > 0 else 0):.1f}%

Additional Context:
{context_str}

Please provide:
1. Company Type (SaaS, Biotech, Hardware, E-commerce, etc.)
2. Development Stage (Hypergrowth, Growth, Mature, Pre-clinical, Phase 2, etc.)
3. Key Value Drivers (3-5 most important metrics for valuation)
4. Recommended Valuation Methodologies with weights (must sum to 100%)
5. Sector-Specific Metrics to focus on
6. Reasoning for your classification

Respond in JSON format:
{{
    "company_type": "one of: saas_software, biotech_pharma, drug_discovery, clinical_stage_biotech, hardware_semiconductors, ecommerce_marketplace, fintech_payments, consumer_brands, industrial_manufacturing, energy_utilities, real_estate, media_entertainment, telecom_networks, infrastructure",
    "development_stage": "one of: pre_revenue, early_revenue, hypergrowth, growth, mature, decline, distress, preclinical, phase_1, phase_2, phase_3, commercialization, prototype, pilot_production, mass_production",
    "key_value_drivers": ["driver 1", "driver 2", ...],
    "valuation_methodologies": [
        {{
            "method": "dcf",
            "use": true/false,
            "weight": 0-100,
            "reason": "explanation",
            "config": {{"terminal_growth": 0.025, "wacc_adjustment": 0}},
            "focus_multiples": []
        }},
        {{
            "method": "cca",
            "use": true/false,
            "weight": 0-100,
            "reason": "explanation",
            "config": {{"peer_filter": "growth > 0.30", "apply_discount": 0}},
            "focus_multiples": ["EV/Revenue", "EV/EBITDA", "P/E"]
        }},
        {{
            "method": "sum_of_parts",
            "use": true/false,
            "weight": 0-100,
            "reason": "explanation for biotech pipeline valuation",
            "config": {{"risk_adjust": true, "phase_weights": {{"phase_1": 0.10, "phase_2": 0.30, "phase_3": 0.60}}}},
            "focus_multiples": []
        }},
        {{
            "method": "precedent_transactions",
            "use": true/false,
            "weight": 0-100,
            "reason": "explanation",
            "config": {{}},
            "focus_multiples": ["EV/Revenue", "EV/Pipeline"]
        }}
    ],
    "sector_specific_metrics": {{
        "for_saas": {{"arr": null, "nrr": null, "ltv_cac_ratio": null}},
        "for_biotech": {{"pipeline_value": null, "peak_sales": null, "pos": null}},
        "for_hardware": {{"gross_margin": null, "inventory_turns": null}}
    }},
    "confidence": 0.0-1.0,
    "reasoning": "detailed explanation of classification and methodology selection"
}}
"""
        
        try:
            # Use DeepSeek LLM via LLMClient
            messages = [
                {"role": "system", "content": "You are a senior investment banker and valuation expert."},
                {"role": "user", "content": prompt}
            ]
            
            json_text = self.llm.chat(messages, temperature=0.7, max_tokens=4000)
            
            # Extract JSON from markdown code blocks if present
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0].strip()
            elif "```" in json_text:
                json_text = json_text.split("```")[1].split("```")[0].strip()
            
            classification = json.loads(json_text)
            
            # Convert to CompanyProfile
            company_type = CompanyType(classification["company_type"])
            development_stage = DevelopmentStage(classification["development_stage"])
            
            methodologies = []
            for method_data in classification["valuation_methodologies"]:
                methodologies.append(ValuationMethodology(
                    method_name=method_data["method"],
                    use=method_data["use"],
                    weight=method_data["weight"] / 100.0,  # Convert to decimal
                    reason=method_data["reason"],
                    config=method_data.get("config", {}),
                    focus_multiples=method_data.get("focus_multiples", [])
                ))
            
            profile = CompanyProfile(
                company_name=company_name,
                company_type=company_type,
                development_stage=development_stage,
                sector_specific_metrics=classification.get("sector_specific_metrics", {}),
                key_value_drivers=classification["key_value_drivers"],
                valuation_methodologies=methodologies,
                classification_confidence=classification.get("confidence", 0.85),
                reasoning=classification["reasoning"]
            )
            
            logger.info(f"✓ AI Classification complete for {company_name}")
            logger.info(f"  Type: {company_type.value}, Stage: {development_stage.value}")
            logger.info(f"  Primary Method: {[m.method_name for m in methodologies if m.weight > 0.4]}")
            
            return profile
            
        except Exception as e:
            logger.error(f"LLM classification failed: {e}, falling back to rule-based")
            return self._classify_rule_based(
                company_name, description, industry, revenue,
                revenue_growth, ebitda, fcf, rd_expense, additional_context
            )
    
    def _classify_rule_based(
        self,
        company_name: str,
        description: str,
        industry: str,
        revenue: float,
        revenue_growth: float,
        ebitda: float,
        fcf: float,
        rd_expense: float,
        additional_context: Optional[Dict[str, Any]]
    ) -> CompanyProfile:
        """Rule-based classification fallback"""
        
        fcf_margin = fcf / revenue if revenue > 0 else -1
        ebitda_margin = ebitda / revenue if revenue > 0 else 0
        rd_pct_revenue = rd_expense / revenue if revenue > 0 else 0
        
        # Determine company type
        description_lower = description.lower()
        industry_lower = industry.lower()
        
        # Biotech/Pharma detection
        if (rd_pct_revenue > 0.50 or 
            "biotech" in industry_lower or "pharma" in industry_lower or 
            "drug" in description_lower or "clinical" in description_lower or
            "pipeline" in description_lower):
            
            if revenue < 10_000_000:  # Pre-revenue or early
                company_type = CompanyType.CLINICAL_STAGE_BIOTECH
                development_stage = DevelopmentStage.PHASE_2  # Default assumption
            else:
                company_type = CompanyType.BIOTECH_PHARMA
                development_stage = DevelopmentStage.COMMERCIALIZATION
        
        # SaaS detection
        elif ("saas" in description_lower or "software" in description_lower or
              "cloud" in description_lower or "subscription" in description_lower):
            company_type = CompanyType.SAAS_SOFTWARE
            
            if revenue_growth > 0.40 and fcf_margin < 0:
                development_stage = DevelopmentStage.HYPERGROWTH
            elif revenue_growth >= 0.20:
                development_stage = DevelopmentStage.GROWTH
            else:
                development_stage = DevelopmentStage.MATURE
        
        # Hardware/Semiconductor
        elif ("semiconductor" in industry_lower or "chip" in description_lower or
              "hardware" in description_lower):
            company_type = CompanyType.HARDWARE_SEMICONDUCTORS
            development_stage = DevelopmentStage.GROWTH if revenue_growth > 0.15 else DevelopmentStage.MATURE
        
        # E-commerce/Marketplace
        elif ("ecommerce" in description_lower or "marketplace" in description_lower or
              "retail" in industry_lower):
            company_type = CompanyType.ECOMMERCE_MARKETPLACE
            development_stage = DevelopmentStage.GROWTH if revenue_growth > 0.20 else DevelopmentStage.MATURE
        
        # Default to industrial
        else:
            company_type = CompanyType.INDUSTRIAL_MANUFACTURING
            development_stage = DevelopmentStage.MATURE
        
        # Determine valuation methodology based on classification
        methodologies = self._get_methodologies_for_type(
            company_type, development_stage, revenue_growth, fcf_margin, ebitda_margin
        )
        
        profile = CompanyProfile(
            company_name=company_name,
            company_type=company_type,
            development_stage=development_stage,
            sector_specific_metrics={},
            key_value_drivers=self._get_key_drivers(company_type, development_stage),
            valuation_methodologies=methodologies,
            classification_confidence=0.70,  # Lower confidence for rule-based
            reasoning=f"Rule-based classification: {company_type.value} at {development_stage.value} stage"
        )
        
        logger.info(f"✓ Rule-based classification for {company_name}")
        logger.info(f"  Type: {company_type.value}, Stage: {development_stage.value}")
        
        return profile
    
    def _get_methodologies_for_type(
        self,
        company_type: CompanyType,
        stage: DevelopmentStage,
        revenue_growth: float,
        fcf_margin: float,
        ebitda_margin: float
    ) -> List[ValuationMethodology]:
        """Get appropriate valuation methodologies for company type and stage"""
        
        methodologies = []
        
        # Biotech/Clinical Stage
        if company_type in [CompanyType.BIOTECH_PHARMA, CompanyType.CLINICAL_STAGE_BIOTECH]:
            if stage in [DevelopmentStage.PRECLINICAL, DevelopmentStage.PHASE_1, 
                         DevelopmentStage.PHASE_2, DevelopmentStage.PHASE_3]:
                # Sum-of-parts pipeline valuation
                methodologies.append(ValuationMethodology(
                    method_name="sum_of_parts",
                    use=True,
                    weight=0.70,
                    reason="Pipeline valuation with risk-adjusted NPV for each program",
                    config={
                        "risk_adjust": True,
                        "phase_weights": {
                            "phase_1": 0.10,
                            "phase_2": 0.30,
                            "phase_3": 0.60
                        }
                    }
                ))
                
                # Precedent biotech transactions
                methodologies.append(ValuationMethodology(
                    method_name="precedent_transactions",
                    use=True,
                    weight=0.30,
                    reason="Comparable biotech M&A transactions by stage",
                    config={"filter_by_stage": stage.value},
                    focus_multiples=["EV/Pipeline Asset", "Per-Phase Value"]
                ))
                
                # Skip DCF for pre-revenue biotech
                methodologies.append(ValuationMethodology(
                    method_name="dcf",
                    use=False,
                    weight=0.0,
                    reason="Not applicable for clinical-stage companies without revenue"
                ))
            
            else:  # Commercialization stage
                methodologies.append(ValuationMethodology(
                    method_name="dcf",
                    use=True,
                    weight=0.40,
                    reason="Revenue generated - DCF applicable with peak sales assumptions",
                    config={"terminal_growth": 0.03}
                ))
                
                methodologies.append(ValuationMethodology(
                    method_name="cca",
                    use=True,
                    weight=0.40,
                    reason="Compare to commercialized biotech peers",
                    focus_multiples=["EV/Revenue", "EV/EBITDA", "P/E"]
                ))
                
                methodologies.append(ValuationMethodology(
                    method_name="sum_of_parts",
                    use=True,
                    weight=0.20,
                    reason="Value pipeline in addition to marketed products"
                ))
        
        # SaaS Software
        elif company_type == CompanyType.SAAS_SOFTWARE:
            if stage == DevelopmentStage.HYPERGROWTH and fcf_margin < 0:
                # Revenue multiples only
                methodologies.append(ValuationMethodology(
                    method_name="cca",
                    use=True,
                    weight=0.80,
                    reason="Hypergrowth SaaS valued on revenue multiples, not cash flow",
                    config={"peer_filter": "growth > 0.30"},
                    focus_multiples=["EV/Revenue", "EV/NTM Revenue", "EV/ARR"]
                ))
                
                methodologies.append(ValuationMethodology(
                    method_name="growth_scenarios",
                    use=True,
                    weight=0.20,
                    reason="TAM analysis and Rule of 40 assessment"
                ))
                
                methodologies.append(ValuationMethodology(
                    method_name="dcf",
                    use=False,
                    weight=0.0,
                    reason="Negative FCF makes DCF unreliable for hypergrowth SaaS"
                ))
            
            elif stage == DevelopmentStage.GROWTH:
                methodologies.append(ValuationMethodology(
                    method_name="cca",
                    use=True,
                    weight=0.60,
                    reason="Growth-stage SaaS primarily valued on multiples",
                    config={"use_regression": True},
                    focus_multiples=["EV/Revenue", "EV/EBITDA"]
                ))
                
                methodologies.append(ValuationMethodology(
                    method_name="dcf",
                    use=True,
                    weight=0.30,
                    reason="FCF positive - DCF applicable with conservative terminal value",
                    config={"terminal_growth": 0.025}
                ))
                
                methodologies.append(ValuationMethodology(
                    method_name="growth_scenarios",
                    use=True,
                    weight=0.10,
                    reason="Scenario analysis for valuation range"
                ))
            
            else:  # Mature SaaS
                methodologies.append(ValuationMethodology(
                    method_name="dcf",
                    use=True,
                    weight=0.60,
                    reason="Stable cash flows make DCF primary methodology",
                    config={"terminal_growth": 0.025}
                ))
                
                methodologies.append(ValuationMethodology(
                    method_name="cca",
                    use=True,
                    weight=0.30,
                    reason="Peer validation",
                    focus_multiples=["EV/EBITDA", "P/E"]
                ))
                
                methodologies.append(ValuationMethodology(
                    method_name="lbo",
                    use=True,
                    weight=0.10,
                    reason="LBO floor value applicable for mature SaaS"
                ))
        
        # Semiconductors/Hardware
        elif company_type == CompanyType.HARDWARE_SEMICONDUCTORS:
            methodologies.append(ValuationMethodology(
                method_name="dcf",
                use=True,
                weight=0.50,
                reason="Capital-intensive business - DCF captures capex needs",
                config={"terminal_growth": 0.03}
            ))
            
            methodologies.append(ValuationMethodology(
                method_name="cca",
                use=True,
                weight=0.40,
                reason="Compare to semiconductor peers",
                focus_multiples=["EV/EBITDA", "P/E", "EV/Sales"]
            ))
            
            methodologies.append(ValuationMethodology(
                method_name="replacement_cost",
                use=True,
                weight=0.10,
                reason="Asset-heavy business - replacement cost relevant"
            ))
        
        # Default for other industries
        else:
            if revenue_growth > 0.05 and fcf > 0:
                methodologies.append(ValuationMethodology(
                    method_name="dcf",
                    use=True,
                    weight=0.50,
                    reason="Stable business with positive cash flow",
                    config={"terminal_growth": 0.025}
                ))
                
                methodologies.append(ValuationMethodology(
                    method_name="cca",
                    use=True,
                    weight=0.40,
                    reason="Peer comparison",
                    focus_multiples=["EV/EBITDA", "P/E"]
                ))
                
                methodologies.append(ValuationMethodology(
                    method_name="lbo",
                    use=True,
                    weight=0.10,
                    reason="LBO floor value"
                ))
            else:
                # distressed
                methodologies.append(ValuationMethodology(
                    method_name="liquidation",
                    use=True,
                    weight=0.50,
                    reason="Distressed company - asset-based valuation",
                    config={"recovery_rate": 0.60}
                ))
                
                methodologies.append(ValuationMethodology(
                    method_name="cca",
                    use=True,
                    weight=0.50,
                    reason="Distressed multiples with heavy discount",
                    config={"apply_discount": 0.50},
                    focus_multiples=["EV/EBITDA"]
                ))
        
        return methodologies
    
    def _get_key_drivers(
        self,
        company_type: CompanyType,
        stage: DevelopmentStage
    ) -> List[str]:
        """Get key value drivers for company type"""
        
        if company_type in [CompanyType.BIOTECH_PHARMA, CompanyType.CLINICAL_STAGE_BIOTECH]:
            return [
                "Pipeline value (risk-adjusted NPV)",
                "Phase advancement probability",
                "Peak sales potential",
                "Time to market",
                "R&D productivity"
            ]
        
        elif company_type == CompanyType.SAAS_SOFTWARE:
            if stage == DevelopmentStage.HYPERGROWTH:
                return [
                    "ARR growth rate",
                    "Net Revenue Retention (NRR)",
                    "Total Addressable Market (TAM)",
                    "LTV/CAC ratio",
                    "Rule of 40 score"
                ]
            else:
                return [
                    "Revenue growth",
                    "EBITDA margin expansion",
                    "Free cash flow generation",
                    "Customer retention",
                    "Market share"
                ]
        
        elif company_type == CompanyType.HARDWARE_SEMICONDUCTORS:
            return [
                "Gross margin",
                "R&D efficiency",
                "Market position",
                "Technology leadership",
                "Capex requirements"
            ]
        
        else:
            return [
                "Revenue growth",
                "EBITDA margin",
                "Free cash flow",
                "Market position",
                "ROIC"
            ]
    
    def calculate_weighted_valuation(
        self,
        profile: CompanyProfile,
        dcf_value: Optional[float] = None,
        cca_value: Optional[float] = None,
        lbo_value: Optional[float] = None,
        sum_of_parts_value: Optional[float] = None,
        liquidation_value: Optional[float] = None,
        precedent_tx_value: Optional[float] = None,
        growth_scenario_value: Optional[float] = None
    ) -> Tuple[float, str, Dict[str, Any]]:
        """
        Calculate weighted valuation based on methodology weights
        
        Args:
            profile: Company profile with methodology weights
            Various valuation method results
            
        Returns:
            (weighted_value, explanation, breakdown)
        """
        value_map = {
            "dcf": dcf_value,
            "cca": cca_value,
            "lbo": lbo_value,
            "sum_of_parts": sum_of_parts_value,
            "liquidation": liquidation_value,
            "precedent_transactions": precedent_tx_value,
            "growth_scenarios": growth_scenario_value
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        breakdown = {}
        
        for methodology in profile.valuation_methodologies:
            if not methodology.use or methodology.weight == 0:
                breakdown[methodology.method_name] = {
                    "value": None,
                    "weight": 0.0,
                    "reason": methodology.reason,
                    "used": False
                }
                continue
            
            value = value_map.get(methodology.method_name)
            
            if value is not None and value > 0:
                # Apply any config adjustments
                if "apply_discount" in methodology.config:
                    discount = methodology.config["apply_discount"]
                    value = value * (1 - discount)
                
                weighted_sum += value * methodology.weight
                total_weight += methodology.weight
                
                breakdown[methodology.method_name] = {
                    "value": value,
                    "weight": methodology.weight,
                    "reason": methodology.reason,
                    "used": True,
                    "contribution": value * methodology.weight
                }
            else:
                breakdown[methodology.method_name] = {
                    "value": None,
                    "weight": methodology.weight,
                    "reason": f"{methodology.reason} (not calculated)",
                    "used": False
                }
        
        # Calculate final weighted average
        if total_weight > 0:
            final_value = weighted_sum / total_weight
        else:
            final_value = 0.0
        
        # Build explanation
        explanation = f"AI-Powered Valuation for {profile.company_name}\n"
        explanation += f"Classification: {profile.company_type.value} | {profile.development_stage.value}\n"
        explanation += f"Confidence: {profile.classification_confidence:.0%}\n\n"
        explanation += "Methodology Weighting:\n"
        
        for method_name, details in breakdown.items():
            if details["used"]:
                explanation += f"  • {method_name.upper()}: {details['weight']:.0%} "
                explanation += f"(${details['value']:,.2f}) = ${details['contribution']:,.2f}\n"
                explanation += f"    Rationale: {details['reason']}\n"
        
        explanation += f"\nWeighted Valuation: ${final_value:,.2f}\n"
        explanation += f"\nKey Value Drivers:\n"
        for driver in profile.key_value_drivers:
            explanation += f"  • {driver}\n"
        
        explanation += f"\nReasoning: {profile.reasoning}"
        
        return final_value, explanation, breakdown


# Example usage for testing
if __name__ == "__main__":
    # Test with various company types
    engine = AIValuationEngine()
    
    # Test 1: Hypergrowth SaaS
    profile_saas = engine.classify_company(
        company_name="HyperGrowth SaaS Inc",
        description="Cloud-based software for enterprise resource planning",
        industry="Software",
        revenue=100_000_000,
        revenue_growth=0.50,
        ebitda=-10_000_000,
        fcf=-15_000_000,
        rd_expense=20_000_000
    )
    
    print("\n" + "="*80)
    print("HYPERGROWTH SAAS CLASSIFICATION")
    print("="*80)
    print(f"Company Type: {profile_saas.company_type.value}")
    print(f"Development Stage: {profile_saas.development_stage.value}")
    print(f"Confidence: {profile_saas.classification_confidence:.0%}")
    print(f"\nKey Value Drivers:")
    for driver in profile_saas.key_value_drivers:
        print(f"  • {driver}")
    print(f"\nValuation Methodologies:")
    for method in profile_saas.valuation_methodologies:
        if method.use:
            print(f"  • {method.method_name.upper()}: {method.weight:.0%} - {method.reason}")
    
    # Calculate weighted valuation
    weighted_val, explanation, breakdown = engine.calculate_weighted_valuation(
        profile=profile_saas,
        dcf_value=10.00,  # Would be near zero for negative FCF
        cca_value=120.00,  # Revenue multiple valuation
        growth_scenario_value=130.00
    )
    
    print(f"\n{explanation}")
    
    # Test 2: Clinical-stage biotech
    profile_biotech = engine.classify_company(
        company_name="BioInnovate Therapeutics",
        description="Clinical-stage biotech developing novel cancer therapies",
        industry="Biotechnology",
        revenue=500_000,  # Pre-revenue
        revenue_growth=0.10,
        ebitda=-50_000_000,
        fcf=-45_000_000,
        rd_expense=48_000_000
    )
    
    print("\n" + "="*80)
    print("CLINICAL-STAGE BIOTECH CLASSIFICATION")
    print("="*80)
    print(f"Company Type: {profile_biotech.company_type.value}")
    print(f"Development Stage: {profile_biotech.development_stage.value}")
    print(f"Confidence: {profile_biotech.classification_confidence:.0%}")
    print(f"\nKey Value Drivers:")
    for driver in profile_biotech.key_value_drivers:
        print(f"  • {driver}")
    print(f"\nValuation Methodologies:")
    for method in profile_biotech.valuation_methodologies:
        if method.use:
            print(f"  • {method.method_name.upper()}: {method.weight:.0%} - {method.reason}")
    
    # Calculate weighted valuation
    weighted_val_biotech, explanation_biotech, breakdown_biotech = engine.calculate_weighted_valuation(
        profile=profile_biotech,
        dcf_value=None,  # Not applicable
        sum_of_parts_value=450_000_000,  # Pipeline valuation
        precedent_tx_value=420_000_000
    )
    
    print(f"\n{explanation_biotech}")
    
    print("\n" + "="*80)
    print("AI VALUATION ENGINE TEST COMPLETE")
    print("="*80)
