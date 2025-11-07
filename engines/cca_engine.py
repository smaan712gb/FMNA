"""
CCA (Comparable Company Analysis) Engine
Peer selection, multiple calculation, winsorization, and regression-adjusted multiples
"""

from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.neighbors import NearestNeighbors
import statsmodels.api as sm
from loguru import logger


@dataclass
class PeerMetrics:
    """Metrics for a peer company"""
    symbol: str
    company_name: str
    market_cap: float
    enterprise_value: float
    revenue: float
    ebitda: float
    ebit: float
    net_income: float
    revenue_growth: Optional[float] = None
    ebitda_margin: Optional[float] = None
    roic: Optional[float] = None
    
    # Multiples
    ev_revenue: Optional[float] = None
    ev_ebitda: Optional[float] = None
    ev_ebit: Optional[float] = None
    p_e: Optional[float] = None
    
    # Classification
    sector: Optional[str] = None
    industry: Optional[str] = None


@dataclass
class CCAResult:
    """CCA valuation result"""
    target_symbol: str
    implied_ev_revenue: float
    implied_ev_ebitda: float
    implied_ev_ebit: float
    implied_pe: float
    
    # Implied enterprise value
    ev_from_revenue: float
    ev_from_ebitda: float
    ev_from_ebit: float
    
    # Implied equity value
    equity_from_pe: float
    
    # Equity value (from EV multiples)
    equity_from_revenue: float
    equity_from_ebitda: float
    equity_from_ebit: float
    
    # Value per share
    value_per_share_revenue: float
    value_per_share_ebitda: float
    value_per_share_ebit: float
    value_per_share_pe: float
    
    # Statistics
    peer_count: int
    multiples_summary: pd.DataFrame
edges: List[str]


class CCAEngine:
    """Comparable Company Analysis Engine"""
    
    def __init__(self):
        """Initialize CCA engine"""
        logger.info("CCA Engine initialized")
    
    def calculate_multiples(self, peer: PeerMetrics) -> PeerMetrics:
        """
        Calculate valuation multiples for a peer
        
        Args:
            peer: PeerMetrics object
            
        Returns:
            Updated PeerMetrics with calculated multiples
        """
        # EV / Revenue
        if peer.revenue and peer.revenue > 0:
            peer.ev_revenue = peer.enterprise_value / peer.revenue
        
        # EV / EBITDA
        if peer.ebitda and peer.ebitda > 0:
            peer.ev_ebitda = peer.enterprise_value / peer.ebitda
        
        # EV / EBIT
        if peer.ebit and peer.ebit > 0:
            peer.ev_ebit = peer.enterprise_value / peer.ebit
        
        # P / E
        if peer.net_income and peer.net_income > 0:
            peer.p_e = peer.market_cap / peer.net_income
        
        # Margins
        if peer.revenue and peer.revenue > 0:
            if peer.ebitda:
                peer.ebitda_margin = peer.ebitda / peer.revenue
        
        return peer
    
    def filter_outliers_iqr(
        self,
        peers: List[PeerMetrics],
        metric: str,
        multiplier: float = 1.5
    ) -> List[PeerMetrics]:
        """
        Filter outliers using IQR method
        
        Args:
            peers: List of peer companies
            metric: Metric name to filter on
            multiplier: IQR multiplier (default 1.5)
            
        Returns:
            Filtered list of peers
        """
        values = []
        for peer in peers:
            val = getattr(peer, metric, None)
            if val is not None and not np.isnan(val) and not np.isinf(val):
                values.append(val)
        
        if len(values) < 3:
            return peers
        
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - multiplier * iqr
        upper_bound = q3 + multiplier * iqr
        
        filtered = []
        for peer in peers:
            val = getattr(peer, metric, None)
            if val is not None and lower_bound <= val <= upper_bound:
                filtered.append(peer)
        
        logger.debug(f"Filtered {metric}: {len(peers)} -> {len(filtered)} peers")
        return filtered
    
    def winsorize_multiples(
        self,
        peers: List[PeerMetrics],
        metric: str,
        lower_percentile: float = 5,
        upper_percentile: float = 95
    ) -> List[PeerMetrics]:
        """
        Winsorize multiples at specified percentiles
        
        Args:
            peers: List of peer companies
            metric: Multiple to winsorize
            lower_percentile: Lower percentile (default 5)
            upper_percentile: Upper percentile (default 95)
            
        Returns:
            List of peers with winsorized multiples
        """
        values = []
        for peer in peers:
            val = getattr(peer, metric, None)
            if val is not None and not np.isnan(val) and not np.isinf(val):
                values.append(val)
        
        if len(values) < 3:
            return peers
        
        lower_bound = np.percentile(values, lower_percentile)
        upper_bound = np.percentile(values, upper_percentile)
        
        winsorized_peers = []
        for peer in peers:
            peer_copy = peer
            val = getattr(peer, metric, None)
            
            if val is not None:
                if val < lower_bound:
                    setattr(peer_copy, metric, lower_bound)
                elif val > upper_bound:
                    setattr(peer_copy, metric, upper_bound)
            
            winsorized_peers.append(peer_copy)
        
        logger.debug(f"Winsorized {metric} at {lower_percentile}/{upper_percentile} percentiles")
        return winsorized_peers
    
    def calculate_summary_statistics(
        self,
        peers: List[PeerMetrics],
        metrics: List[str]
    ) -> pd.DataFrame:
        """
        Calculate summary statistics for peer multiples
        
        Args:
            peers: List of peer companies
            metrics: List of metrics to summarize
            
        Returns:
            DataFrame with summary statistics
        """
        data = []
        
        for metric in metrics:
            values = []
            for peer in peers:
                val = getattr(peer, metric, None)
                if val is not None and not np.isnan(val) and not np.isinf(val):
                    values.append(val)
            
            if values:
                row = {
                    'Metric': metric,
                    'Count': len(values),
                    'Mean': np.mean(values),
                    'Median': np.median(values),
                    'Min': np.min(values),
                    'Max': np.max(values),
                    'StdDev': np.std(values),
                    'P25': np.percentile(values, 25),
                    'P75': np.percentile(values, 75)
                }
                data.append(row)
        
        df = pd.DataFrame(data)
        return df
    
    def regression_adjusted_multiples(
        self,
        peers: List[PeerMetrics],
        target_growth: float,
        target_roic: float,
        multiple_metric: str = 'ev_ebitda'
    ) -> float:
        """
        Calculate regression-adjusted multiple based on growth and ROIC
        
        Args:
            peers: List of peer companies
            target_growth: Target company revenue growth rate
            target_roic: Target company ROIC
            multiple_metric: Multiple to adjust (ev_ebitda, ev_revenue, etc.)
            
        Returns:
            Regression-adjusted multiple
            
        Raises:
            ValueError: If insufficient data for regression (NO FALLBACKS)
        """
        # Prepare data
        X_data = []
        y_data = []
        
        for peer in peers:
            multiple = getattr(peer, multiple_metric, None)
            growth = peer.revenue_growth
            roic = peer.roic
            
            if multiple and growth is not None and roic is not None:
                if not (np.isnan(multiple) or np.isinf(multiple)):
                    X_data.append([growth, roic])
                    y_data.append(multiple)
        
        # STRICT VALIDATION - NO FALLBACKS
        if len(X_data) < 3:
            error_msg = (
                f"INSUFFICIENT DATA FOR REGRESSION: Only {len(X_data)} peers with complete "
                f"{multiple_metric}, revenue_growth, and ROIC data. Minimum 3 required.\n\n"
                f"AVAILABLE PEERS BREAKDOWN:\n"
            )
            
            for i, peer in enumerate(peers, 1):
                multiple = getattr(peer, multiple_metric, None)
                growth = peer.revenue_growth
                roic = peer.roic
                status = []
                if multiple is None or np.isnan(multiple) or np.isinf(multiple):
                    status.append(f"{multiple_metric}=MISSING")
                if growth is None:
                    status.append("growth=MISSING")
                if roic is None:
                    status.append("ROIC=MISSING")
                
                error_msg += f"  {i}. {peer.symbol}: {', '.join(status) if status else 'COMPLETE'}\n"
            
            error_msg += (
                f"\nRESOLUTION:\n"
                f"1. Fetch more peer companies with complete data\n"
                f"2. Ensure all peers have {multiple_metric}, revenue_growth, and ROIC\n"
                f"3. This platform does NOT use median fallbacks\n"
                f"4. Regression analysis REQUIRES minimum 3 complete data points"
            )
            
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        X = np.array(X_data)
        y = np.array(y_data)
        
        # Add constant
        X = sm.add_constant(X)
        
        # Run regression
        model = sm.OLS(y, X)
        results = model.fit()
        
        # Predict for target
        target_X = np.array([[1, target_growth, target_roic]])
        adjusted_multiple = results.predict(target_X)[0]
        
        logger.info(f"Regression-adjusted {multiple_metric}: {adjusted_multiple:.2f}")
        logger.debug(f"R-squared: {results.rsquared:.3f}")
        logger.success(f"✓ Regression used {len(X_data)} peers with complete data")
        
        return adjusted_multiple
    
    def nearest_neighbor_selection(
        self,
        target_features: Dict[str, float],
        candidate_peers: List[Tuple[str, Dict[str, float]]],
        n_neighbors: int = 10,
        feature_weights: Optional[Dict[str, float]] = None
    ) -> List[str]:
        """
        Select peers using nearest neighbor algorithm
        
        Args:
            target_features: Dictionary of target company features
            candidate_peers: List of (symbol, features_dict) tuples
            n_neighbors: Number of neighbors to select
            feature_weights: Optional weights for each feature
            
        Returns:
            List of selected peer symbols
        """
        # Extract feature names
        feature_names = list(target_features.keys())
        
        # Prepare feature matrix
        target_vector = np.array([target_features[f] for f in feature_names]).reshape(1, -1)
        
        candidate_vectors = []
        candidate_symbols = []
        
        for symbol, features in candidate_peers:
            vector = [features.get(f, 0) for f in feature_names]
            candidate_vectors.append(vector)
            candidate_symbols.append(symbol)
        
        X = np.array(candidate_vectors)
        
        # Apply feature weights if provided
        if feature_weights:
            weights = np.array([feature_weights.get(f, 1.0) for f in feature_names])
            X = X * weights
            target_vector = target_vector * weights
        
        # Normalize features
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        target_scaled = scaler.transform(target_vector)
        
        # Find nearest neighbors
        nbrs = NearestNeighbors(n_neighbors=min(n_neighbors, len(X_scaled)), metric='euclidean')
        nbrs.fit(X_scaled)
        
        distances, indices = nbrs.kneighbors(target_scaled)
        
        # Get selected peers
        selected_peers = [candidate_symbols[i] for i in indices[0]]
        
        logger.info(f"Selected {len(selected_peers)} peers via nearest neighbor")
        
        return selected_peers
    
    def calculate_valuation(
        self,
        target_symbol: str,
        target_metrics: Dict[str, float],
        peers: List[PeerMetrics],
        shares_outstanding: float,
        net_debt: float,
        methods: List[str] = ['median', 'mean', 'regression'],
        use_winsorization: bool = True
    ) -> CCAResult:
        """
        Calculate CCA valuation for target company
        
        Args:
            target_symbol: Target company symbol
            target_metrics: Dict with target's revenue, ebitda, ebit, net_income, etc.
            peers: List of peer company metrics
            shares_outstanding: Target's shares outstanding
            net_debt: Target's net debt
            methods: Valuation methods to use
            use_winsorization: Whether to winsorize multiples
            
        Returns:
            CCAResult with implied valuations
        """
        logger.info(f"Calculating CCA valuation for {target_symbol}")
        
        # Calculate multiples for all peers
        peers = [self.calculate_multiples(peer) for peer in peers]
        
        # Winsorize if enabled
        if use_winsorization:
            peers = self.winsorize_multiples(peers, 'ev_revenue')
            peers = self.winsorize_multiples(peers, 'ev_ebitda')
            peers = self.winsorize_multiples(peers, 'ev_ebit')
            peers = self.winsorize_multiples(peers, 'p_e')
        
        # Calculate summary statistics
        multiples_summary = self.calculate_summary_statistics(
            peers,
            ['ev_revenue', 'ev_ebitda', 'ev_ebit', 'p_e']
        )
        
        # Determine valuation multiples
        if 'regression' in methods and target_metrics.get('revenue_growth') and target_metrics.get('roic'):
            ev_ebitda_multiple = self.regression_adjusted_multiples(
                peers,
                target_metrics['revenue_growth'],
                target_metrics['roic'],
                'ev_ebitda'
            )
            ev_revenue_multiple = self.regression_adjusted_multiples(
                peers,
                target_metrics['revenue_growth'],
                target_metrics['roic'],
                'ev_revenue'
            )
        else:
            # Use median by default
            ev_revenue_vals = [p.ev_revenue for p in peers if p.ev_revenue]
            ev_ebitda_vals = [p.ev_ebitda for p in peers if p.ev_ebitda]
            
            ev_revenue_multiple = np.median(ev_revenue_vals) if ev_revenue_vals else 0
            ev_ebitda_multiple = np.median(ev_ebitda_vals) if ev_ebitda_vals else 0
        
        ev_ebit_vals = [p.ev_ebit for p in peers if p.ev_ebit]
        p_e_vals = [p.p_e for p in peers if p.p_e]
        
        ev_ebit_multiple = np.median(ev_ebit_vals) if ev_ebit_vals else 0
        p_e_multiple = np.median(p_e_vals) if p_e_vals else 0
        
        # Calculate implied enterprise values
        ev_from_revenue = target_metrics.get('revenue', 0) * ev_revenue_multiple
        ev_from_ebitda = target_metrics.get('ebitda', 0) * ev_ebitda_multiple
        ev_from_ebit = target_metrics.get('ebit', 0) * ev_ebit_multiple
        
        # Calculate implied equity values
        equity_from_revenue = ev_from_revenue - net_debt
        equity_from_ebitda = ev_from_ebitda - net_debt
        equity_from_ebit = ev_from_ebit - net_debt
        equity_from_pe = target_metrics.get('net_income', 0) * p_e_multiple
        
        # Value per share
        value_per_share_revenue = equity_from_revenue / shares_outstanding if shares_outstanding > 0 else 0
        value_per_share_ebitda = equity_from_ebitda / shares_outstanding if shares_outstanding > 0 else 0
        value_per_share_ebit = equity_from_ebit / shares_outstanding if shares_outstanding > 0 else 0
        value_per_share_pe = equity_from_pe / shares_outstanding if shares_outstanding > 0 else 0
        
        # Log results
        logger.info(f"EV/Revenue: {ev_revenue_multiple:.2f}x → EV: ${ev_from_revenue:,.0f}")
        logger.info(f"EV/EBITDA: {ev_ebitda_multiple:.2f}x → EV: ${ev_from_ebitda:,.0f}")
        logger.info(f"EV/EBIT: {ev_ebit_multiple:.2f}x → EV: ${ev_from_ebit:,.0f}")
        logger.info(f"P/E: {p_e_multiple:.2f}x → Equity: ${equity_from_pe:,.0f}")
        
        result = CCAResult(
            target_symbol=target_symbol,
            implied_ev_revenue=ev_revenue_multiple,
            implied_ev_ebitda=ev_ebitda_multiple,
            implied_ev_ebit=ev_ebit_multiple,
            implied_pe=p_e_multiple,
            ev_from_revenue=ev_from_revenue,
            ev_from_ebitda=ev_from_ebitda,
            ev_from_ebit=ev_from_ebit,
            equity_from_pe=equity_from_pe,
            equity_from_revenue=equity_from_revenue,
            equity_from_ebitda=equity_from_ebitda,
            equity_from_ebit=equity_from_ebit,
            value_per_share_revenue=value_per_share_revenue,
            value_per_share_ebitda=value_per_share_ebitda,
            value_per_share_ebit=value_per_share_ebit,
            value_per_share_pe=value_per_share_pe,
            peer_count=len(peers),
            multiples_summary=multiples_summary
        )
        
        return result


# Example usage
if __name__ == "__main__":
    # Initialize engine
    engine = CCAEngine()
    
    # Define sample peers
    peers = [
        PeerMetrics(
            symbol="MSFT",
            company_name="Microsoft",
            market_cap=2_800_000_000_000,
            enterprise_value=2_750_000_000_000,
            revenue=211_900_000_000,
            ebitda=101_000_000_000,
            ebit=88_500_000_000,
            net_income=72_400_000_000,
            revenue_growth=0.12,
            roic=0.30,
            sector="Technology"
        ),
        PeerMetrics(
            symbol="GOOGL",
            company_name="Alphabet",
            market_cap=1_700_000_000_000,
            enterprise_value=1_650_000_000_000,
            revenue=307_400_000_000,
            ebitda=107_000_000_000,
            ebit=96_000_000_000,
            net_income=73_800_000_000,
            revenue_growth=0.09,
            roic=0.28,
            sector="Technology"
        ),
        # Add more peers...
    ]
    
    # Target company metrics
    target_metrics = {
        'revenue': 383_300_000_000,
        'ebitda': 123_000_000_000,
        'ebit': 114_000_000_000,
        'net_income': 97_000_000_000,
        'revenue_growth': 0.08,
        'roic': 0.45
    }
    
    # Calculate valuation
    result = engine.calculate_valuation(
        target_symbol="AAPL",
        target_metrics=target_metrics,
        peers=peers,
        shares_outstanding=15_500_000_000,
        net_debt=-50_000_000_000  # Net cash position
    )
    
    print(f"Value per Share (EV/Revenue): ${result.value_per_share_revenue:.2f}")
    print(f"Value per Share (EV/EBITDA): ${result.value_per_share_ebitda:.2f}")
    print(f"Value per Share (P/E): ${result.value_per_share_pe:.2f}")
    print("\nMultiples Summary:")
    print(result.multiples_summary)
