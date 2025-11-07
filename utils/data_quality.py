"""
Data Quality Validation Framework
ZERO TOLERANCE for incomplete data - Fail fast and fail loud
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
from loguru import logger


class FieldCriticality(Enum):
    """Criticality level for data fields"""
    CRITICAL = "critical"  # Must exist, non-null, non-zero
    REQUIRED = "required"  # Must exist and non-null
    OPTIONAL = "optional"  # Nice to have


@dataclass
class FieldRequirement:
    """Definition of a required field"""
    name: str
    criticality: FieldCriticality
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[Any]] = None
    description: str = ""


@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    missing_critical: List[str]
    missing_required: List[str]
    invalid_values: List[str]
    warnings: List[str]
    
    def get_error_message(self) -> str:
        """Get comprehensive error message"""
        errors = []
        
        if self.missing_critical:
            errors.append(f"CRITICAL FIELDS MISSING: {', '.join(self.missing_critical)}")
        
        if self.missing_required:
            errors.append(f"REQUIRED FIELDS MISSING: {', '.join(self.missing_required)}")
        
        if self.invalid_values:
            errors.append(f"INVALID VALUES: {', '.join(self.invalid_values)}")
        
        return " | ".join(errors) if errors else "No errors"


class DataQualityException(Exception):
    """Raised when data quality is insufficient"""
    
    def __init__(self, message: str, validation_result: ValidationResult):
        super().__init__(message)
        self.validation_result = validation_result


class DataQualityValidator:
    """
    Strict data quality validator - NO FALLBACKS
    
    Philosophy:
    - Better to FAIL than to produce incorrect analysis
    - Every missing field is explicitly reported
    - No silent degradation
    - No default values or medians
    """
    
    # Required fields for different analysis types
    PEER_COMPANY_FIELDS = [
        FieldRequirement("symbol", FieldCriticality.CRITICAL, description="Company ticker"),
        FieldRequirement("market_cap", FieldCriticality.CRITICAL, min_value=0, description="Market capitalization"),
        FieldRequirement("enterprise_value", FieldCriticality.CRITICAL, min_value=0, description="Enterprise value"),
        FieldRequirement("revenue", FieldCriticality.CRITICAL, min_value=0, description="Annual revenue"),
        FieldRequirement("ebitda", FieldCriticality.CRITICAL, description="EBITDA"),
        FieldRequirement("ebit", FieldCriticality.CRITICAL, description="EBIT"),
        FieldRequirement("net_income", FieldCriticality.REQUIRED, description="Net income"),
        FieldRequirement("revenue_growth", FieldCriticality.REQUIRED, description="Revenue growth rate"),
        FieldRequirement("ebitda_margin", FieldCriticality.REQUIRED, description="EBITDA margin"),
    ]
    
    DCF_FIELDS = [
        FieldRequirement("fcff", FieldCriticality.CRITICAL, description="Free cash flow to firm"),
        FieldRequirement("wacc", FieldCriticality.CRITICAL, min_value=0.01, max_value=0.50, description="WACC"),
        FieldRequirement("terminal_growth", FieldCriticality.CRITICAL, min_value=-0.10, max_value=0.15, description="Terminal growth rate"),
        FieldRequirement("shares_outstanding", FieldCriticality.CRITICAL, min_value=0, description="Shares outstanding"),
        FieldRequirement("cash", FieldCriticality.REQUIRED, description="Cash and equivalents"),
        FieldRequirement("debt", FieldCriticality.REQUIRED, description="Total debt"),
    ]
    
    MERGER_FIELDS = [
        FieldRequirement("acquirer_shares", FieldCriticality.CRITICAL, min_value=0, description="Acquirer shares outstanding"),
        FieldRequirement("target_shares", FieldCriticality.CRITICAL, min_value=0, description="Target shares outstanding"),
        FieldRequirement("acquirer_eps", FieldCriticality.CRITICAL, description="Acquirer EPS"),
        FieldRequirement("target_eps", FieldCriticality.CRITICAL, description="Target EPS"),
        FieldRequirement("exchange_ratio", FieldCriticality.CRITICAL, min_value=0, description="Exchange ratio or cash price"),
    ]
    
    LBO_FIELDS = [
        FieldRequirement("purchase_price", FieldCriticality.CRITICAL, min_value=0, description="Purchase price"),
        FieldRequirement("debt_financing_pct", FieldCriticality.CRITICAL, min_value=0, max_value=1, description="Debt financing %"),
        FieldRequirement("exit_multiple", FieldCriticality.CRITICAL, min_value=0, description="Exit multiple"),
        FieldRequirement("ebitda", FieldCriticality.CRITICAL, min_value=0, description="EBITDA"),
    ]
    
    FINANCIAL_STATEMENT_FIELDS = [
        FieldRequirement("revenue", FieldCriticality.CRITICAL, min_value=0, description="Revenue"),
        FieldRequirement("cost_of_goods_sold", FieldCriticality.REQUIRED, description="COGS"),
        FieldRequirement("operating_expenses", FieldCriticality.REQUIRED, description="Operating expenses"),
        FieldRequirement("total_assets", FieldCriticality.CRITICAL, min_value=0, description="Total assets"),
        FieldRequirement("total_liabilities", FieldCriticality.REQUIRED, description="Total liabilities"),
        FieldRequirement("shareholders_equity", FieldCriticality.CRITICAL, description="Shareholders equity"),
        FieldRequirement("operating_cash_flow", FieldCriticality.REQUIRED, description="Operating cash flow"),
    ]
    
    @staticmethod
    def validate_data(
        data: Dict[str, Any],
        field_requirements: List[FieldRequirement],
        context: str = "data"
    ) -> ValidationResult:
        """
        Validate data against field requirements
        
        Args:
            data: Data dictionary to validate
            field_requirements: List of required fields
            context: Context description for error messages
            
        Returns:
            ValidationResult with detailed findings
            
        Raises:
            DataQualityException if critical/required fields missing
        """
        missing_critical = []
        missing_required = []
        invalid_values = []
        warnings = []
        
        for requirement in field_requirements:
            field_name = requirement.name
            value = data.get(field_name)
            
            # Check if field exists
            if value is None:
                if requirement.criticality == FieldCriticality.CRITICAL:
                    missing_critical.append(f"{field_name} ({requirement.description})")
                elif requirement.criticality == FieldCriticality.REQUIRED:
                    missing_required.append(f"{field_name} ({requirement.description})")
                else:
                    warnings.append(f"Optional field '{field_name}' is missing")
                continue
            
            # Check for numeric fields that are zero when they shouldn't be
            if requirement.criticality == FieldCriticality.CRITICAL:
                if isinstance(value, (int, float)) and value == 0:
                    missing_critical.append(f"{field_name} is zero ({requirement.description})")
                    continue
            
            # Check min/max bounds
            if isinstance(value, (int, float)):
                if requirement.min_value is not None and value < requirement.min_value:
                    invalid_values.append(
                        f"{field_name}={value} is below minimum {requirement.min_value}"
                    )
                
                if requirement.max_value is not None and value > requirement.max_value:
                    invalid_values.append(
                        f"{field_name}={value} exceeds maximum {requirement.max_value}"
                    )
            
            # Check allowed values
            if requirement.allowed_values and value not in requirement.allowed_values:
                invalid_values.append(
                    f"{field_name}={value} not in allowed values {requirement.allowed_values}"
                )
        
        is_valid = not (missing_critical or missing_required or invalid_values)
        
        result = ValidationResult(
            is_valid=is_valid,
            missing_critical=missing_critical,
            missing_required=missing_required,
            invalid_values=invalid_values,
            warnings=warnings
        )
        
        # Log results
        if not is_valid:
            logger.error(f"❌ DATA QUALITY FAILURE in {context}:")
            logger.error(f"   {result.get_error_message()}")
        else:
            logger.success(f"✓ Data quality validated for {context}")
        
        return result
    
    @classmethod
    def validate_peer_data(cls, peer_data: Dict[str, Any], symbol: str) -> ValidationResult:
        """Validate peer company data"""
        return cls.validate_data(
            peer_data,
            cls.PEER_COMPANY_FIELDS,
            context=f"Peer Company {symbol}"
        )
    
    @classmethod
    def validate_dcf_inputs(cls, dcf_data: Dict[str, Any]) -> ValidationResult:
        """Validate DCF input data"""
        return cls.validate_data(
            dcf_data,
            cls.DCF_FIELDS,
            context="DCF Analysis"
        )
    
    @classmethod
    def validate_merger_inputs(cls, merger_data: Dict[str, Any]) -> ValidationResult:
        """Validate merger model inputs"""
        return cls.validate_data(
            merger_data,
            cls.MERGER_FIELDS,
            context="Merger Analysis"
        )
    
    @classmethod
    def validate_lbo_inputs(cls, lbo_data: Dict[str, Any]) -> ValidationResult:
        """Validate LBO inputs"""
        return cls.validate_data(
            lbo_data,
            cls.LBO_FIELDS,
            context="LBO Analysis"
        )
    
    @classmethod
    def validate_financial_statements(cls, statements: Dict[str, Any]) -> ValidationResult:
        """Validate financial statement data"""
        return cls.validate_data(
            statements,
            cls.FINANCIAL_STATEMENT_FIELDS,
            context="Financial Statements"
        )
    
    @classmethod
    def validate_peer_list_for_regression(
        cls,
        peers: List[Dict[str, Any]],
        minimum_peers: int = 5,
        require_growth_roic: bool = True
    ) -> ValidationResult:
        """
        Validate peer list is sufficient for regression analysis
        
        Args:
            peers: List of peer data dictionaries
            minimum_peers: Minimum number of valid peers required
            require_growth_roic: Whether growth and ROIC are required
            
        Returns:
            ValidationResult
        """
        missing_critical = []
        missing_required = []
        invalid_values = []
        warnings = []
        
        # Check minimum count
        if len(peers) < minimum_peers:
            missing_critical.append(
                f"Only {len(peers)} peers provided, minimum {minimum_peers} required for regression"
            )
        
        # Validate each peer
        valid_peer_count = 0
        peers_with_growth_roic = 0
        
        for i, peer in enumerate(peers):
            peer_symbol = peer.get('symbol', f'Peer_{i}')
            
            # Validate basic peer data
            peer_validation = cls.validate_peer_data(peer, peer_symbol)
            
            if peer_validation.is_valid:
                valid_peer_count += 1
                
                # Check for growth and ROIC if required
                if require_growth_roic:
                    has_growth = peer.get('revenue_growth') is not None
                    has_roic = peer.get('roic') is not None
                    
                    if has_growth and has_roic:
                        peers_with_growth_roic += 1
                    else:
                        missing_fields = []
                        if not has_growth:
                            missing_fields.append('revenue_growth')
                        if not has_roic:
                            missing_fields.append('roic')
                        warnings.append(
                            f"{peer_symbol} missing: {', '.join(missing_fields)}"
                        )
            else:
                invalid_values.append(f"{peer_symbol}: {peer_validation.get_error_message()}")
        
        # Check if we have enough valid peers for regression
        if require_growth_roic and peers_with_growth_roic < 3:
            missing_critical.append(
                f"Only {peers_with_growth_roic} peers with growth & ROIC data, "
                f"minimum 3 required for regression analysis"
            )
        
        is_valid = not (missing_critical or missing_required or invalid_values)
        
        result = ValidationResult(
            is_valid=is_valid,
            missing_critical=missing_critical,
            missing_required=missing_required,
            invalid_values=invalid_values,
            warnings=warnings
        )
        
        if not is_valid:
            logger.error("❌ PEER LIST VALIDATION FAILED:")
            logger.error(f"   Total peers: {len(peers)}")
            logger.error(f"   Valid peers: {valid_peer_count}")
            logger.error(f"   Peers with growth & ROIC: {peers_with_growth_roic}")
            logger.error(f"   {result.get_error_message()}")
        else:
            logger.success(f"✓ Peer list validated: {valid_peer_count} valid peers")
        
        return result
    
    @staticmethod
    def fail_if_invalid(validation_result: ValidationResult, context: str = "Analysis"):
        """
        Raise exception if validation failed
        
        Args:
            validation_result: Validation result to check
            context: Context for error message
            
        Raises:
            DataQualityException if validation failed
        """
        if not validation_result.is_valid:
            error_msg = (
                f"DATA QUALITY FAILURE: {context} cannot proceed.\n"
                f"{validation_result.get_error_message()}\n\n"
                f"RESOLUTION:\n"
                f"1. Ensure all required data fields are available\n"
                f"2. Check data source completeness\n"
                f"3. Verify data is not null/zero for critical fields\n"
                f"4. This platform does NOT use fallbacks or defaults\n"
                f"5. Analysis REQUIRES complete, high-quality data"
            )
            raise DataQualityException(error_msg, validation_result)


# Example usage and testing
if __name__ == "__main__":
    validator = DataQualityValidator()
    
    # Test peer validation - VALID data
    print("\n=== TEST 1: Valid Peer Data ===")
    valid_peer = {
        'symbol': 'MSFT',
        'market_cap': 2_800_000_000_000,
        'enterprise_value': 2_750_000_000_000,
        'revenue': 211_900_000_000,
        'ebitda': 101_000_000_000,
        'ebit': 88_500_000_000,
        'net_income': 72_400_000_000,
        'revenue_growth': 0.12,
        'ebitda_margin': 0.48
    }
    
    result = validator.validate_peer_data(valid_peer, 'MSFT')
    print(f"Valid: {result.is_valid}")
    
    # Test peer validation - INVALID data (missing critical fields)
    print("\n=== TEST 2: Invalid Peer Data (missing fields) ===")
    invalid_peer = {
        'symbol': 'XYZ',
        'market_cap': 1_000_000_000,
        # Missing: enterprise_value, revenue, ebitda, etc.
    }
    
    result = validator.validate_peer_data(invalid_peer, 'XYZ')
    print(f"Valid: {result.is_valid}")
    print(f"Error: {result.get_error_message()}")
    
    # Test peer list validation - INSUFFICIENT for regression
    print("\n=== TEST 3: Insufficient Peer List ===")
    peer_list = [valid_peer, invalid_peer]  # Only 1 valid peer
    
    result = validator.validate_peer_list_for_regression(peer_list, minimum_peers=5)
    print(f"Valid: {result.is_valid}")
    print(f"Error: {result.get_error_message()}")
    
    # Test fail_if_invalid
    print("\n=== TEST 4: Fail Fast ===")
    try:
        validator.fail_if_invalid(result, "CCA Regression Analysis")
    except DataQualityException as e:
        print(f"Exception raised (as expected):\n{str(e)}")
