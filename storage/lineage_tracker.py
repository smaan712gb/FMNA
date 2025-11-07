"""
Data Lineage Tracker
Palantir-style lineage tracking for data provenance, audit trail, and governance
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib
import json
from loguru import logger

from config.schemas import ModelLineage
from storage.duckdb_adapter import DuckDBAdapter
from storage.cognee_adapter import CogneeAdapter


class LineageTracker:
    """
    Data Lineage Tracker - Palantir-style provenance tracking
    
    Tracks:
    - Dataset transformations
    - Model versioning
    - Code references
    - User attribution
    - Approval workflows
    """
    
    def __init__(self):
        """Initialize lineage tracker"""
        self.db = DuckDBAdapter()
        self.cognee = CogneeAdapter()
        
        # Initialize lineage table in DuckDB
        self._init_lineage_table()
        
        logger.info("Lineage Tracker initialized")
    
    def _init_lineage_table(self):
        """Create lineage tracking table"""
        self.db.conn.execute("""
            CREATE TABLE IF NOT EXISTS model_lineage (
                lineage_id VARCHAR PRIMARY KEY,
                dataset_name VARCHAR NOT NULL,
                version VARCHAR NOT NULL,
                parent_ids VARCHAR,  -- JSON array
                transformation TEXT,
                code_ref VARCHAR,
                user VARCHAR,
                hash VARCHAR,
                approved BOOLEAN DEFAULT false,
                created_at TIMESTAMP,
                UNIQUE(dataset_name, version)
            )
        """)
        
        logger.debug("Lineage table initialized")
    
    def compute_dataset_hash(self, data: Any) -> str:
        """
        Compute hash of dataset for integrity
        
        Args:
            data: Dataset to hash (DataFrame, dict, etc.)
            
        Returns:
            SHA-256 hash
        """
        # Convert to JSON string
        if hasattr(data, 'to_json'):
            data_str = data.to_json()
        elif isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        # Compute hash
        hash_obj = hashlib.sha256(data_str.encode())
        return hash_obj.hexdigest()
    
    def create_lineage_record(
        self,
        dataset_name: str,
        version: str,
        transformation: str,
        parent_ids: List[str] = None,
        code_ref: Optional[str] = None,
        user: str = "system",
        data_hash: Optional[str] = None
    ) -> ModelLineage:
        """
        Create lineage record
        
        Args:
            dataset_name: Name of dataset/model
            version: Version identifier
            transformation: Description of transformation
            parent_ids: List of parent dataset IDs
            code_ref: Reference to transformation code
            user: User who created this version
            data_hash: Dataset hash (if None, auto-computed)
            
        Returns:
            ModelLineage object
        """
        lineage_id = f"{dataset_name}_{version}_{datetime.now().timestamp()}"
        
        if parent_ids is None:
            parent_ids = []
        
        if data_hash is None:
            data_hash = hashlib.sha256(lineage_id.encode()).hexdigest()
        
        lineage = ModelLineage(
            lineage_id=lineage_id,
            dataset_name=dataset_name,
            version=version,
            parent_ids=parent_ids,
            transformation=transformation,
            code_ref=code_ref,
            user=user,
            hash=data_hash,
            approved=False,
            created_at=datetime.utcnow()
        )
        
        # Store in DuckDB - check if exists first then update or insert
        check_query = "SELECT COUNT(*) as cnt FROM model_lineage WHERE dataset_name = ? AND version = ?"
        exists = self.db.conn.execute(check_query, [lineage.dataset_name, lineage.version]).fetchone()[0] > 0
        
        if exists:
            logger.debug(f"Updating existing lineage record: {dataset_name} v{version}")
            self.db.conn.execute("""
                UPDATE model_lineage 
                SET lineage_id = ?, parent_ids = ?, transformation = ?, 
                    code_ref = ?, user = ?, hash = ?, approved = ?, created_at = ?
                WHERE dataset_name = ? AND version = ?
            """, [
                lineage.lineage_id, json.dumps(lineage.parent_ids), lineage.transformation,
                lineage.code_ref, lineage.user, lineage.hash, lineage.approved,
                lineage.created_at, lineage.dataset_name, lineage.version
            ])
        else:
            self.db.conn.execute("""
                INSERT INTO model_lineage VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                lineage.lineage_id,
                lineage.dataset_name,
                lineage.version,
                json.dumps(lineage.parent_ids),
                lineage.transformation,
                lineage.code_ref,
                lineage.user,
                lineage.hash,
                lineage.approved,
                lineage.created_at
            ])
        
        logger.info(f"Lineage record created: {dataset_name} v{version}")
        
        return lineage
    
    async def create_provenance_graph(
        self,
        dataset_name: str,
        version: str
    ) -> Dict[str, Any]:
        """
        Create provenance graph in Cognee
        
        Args:
            dataset_name: Dataset name
            version: Version
            
        Returns:
            Graph structure
        """
        if not self.cognee.enabled:
            return {}
        
        # Get lineage record
        query = """
            SELECT * FROM model_lineage 
            WHERE dataset_name = ? AND version = ?
        """
        record = self.db.execute_query(query, [dataset_name, version])
        
        if record.empty:
            logger.warning(f"No lineage found for {dataset_name} v{version}")
            return {}
        
        row = record.iloc[0]
        
        # Create node
        await self.cognee.add_node(
            node_id=row['lineage_id'],
            node_type="Dataset",
            properties={
                'name': dataset_name,
                'version': version,
                'transformation': row['transformation'],
                'user': row['user'],
                'created_at': str(row['created_at'])
            }
        )
        
        # Create edges to parents
        parent_ids = json.loads(row['parent_ids']) if row['parent_ids'] else []
        for parent_id in parent_ids:
            await self.cognee.add_edge(
                edge_id=f"{row['lineage_id']}_from_{parent_id}",
                source_node_id=parent_id,
                target_node_id=row['lineage_id'],
                relationship_type="derived_from",
                weight=1.0
            )
        
        logger.info(f"Provenance graph created for {dataset_name}")
        
        return {'nodes': 1, 'edges': len(parent_ids)}
    
    def approve_version(
        self,
        lineage_id: str,
        approver: str
    ) -> bool:
        """
        Approve a dataset version
        
        Args:
            lineage_id: Lineage record ID
            approver: User approving
            
        Returns:
            Success status
        """
        try:
            self.db.conn.execute("""
                UPDATE model_lineage 
                SET approved = true
                WHERE lineage_id = ?
            """, [lineage_id])
            
            logger.info(f"Version approved: {lineage_id} by {approver}")
            return True
            
        except Exception as e:
            logger.error(f"Approval failed: {str(e)}")
            return False
    
    def get_lineage_chain(
        self,
        dataset_name: str,
        version: str,
        max_depth: int = 10
    ) -> List[ModelLineage]:
        """
        Get full lineage chain (recursive)
        
        Args:
            dataset_name: Dataset name
            version: Version
            max_depth: Maximum recursion depth
            
        Returns:
            List of lineage records
        """
        lineage_chain = []
        visited = set()
        
        def traverse(name: str, ver: str, depth: int = 0):
            if depth >= max_depth or (name, ver) in visited:
                return
            
            visited.add((name, ver))
            
            query = """
                SELECT * FROM model_lineage 
                WHERE dataset_name = ? AND version = ?
            """
            record = self.db.execute_query(query, [name, ver])
            
            if not record.empty:
                row = record.iloc[0]
                lineage_chain.append(row.to_dict())
                
                # Traverse parents
                parent_ids = json.loads(row['parent_ids']) if row['parent_ids'] else []
                for parent_id in parent_ids:
                    # Parse parent_id to get name and version
                    parts = parent_id.split('_')
                    if len(parts) >= 2:
                        parent_name = '_'.join(parts[:-2])
                        parent_ver = parts[-2]
                        traverse(parent_name, parent_ver, depth + 1)
        
        traverse(dataset_name, version)
        
        logger.info(f"Retrieved lineage chain: {len(lineage_chain)} records")
        
        return lineage_chain
    
    def close(self):
        """Clean up resources"""
        self.db.close()
        logger.info("Lineage tracker closed")


# Example usage
if __name__ == "__main__":
    import asyncio
    
    tracker = LineageTracker()
    
    print("\n" + "="*70)
    print("LINEAGE TRACKER - DATA PROVENANCE")
    print("="*70)
    
    # Create lineage for raw data
    raw_lineage = tracker.create_lineage_record(
        dataset_name="AAPL_financials",
        version="v1",
        transformation="Ingested from FMP API",
        parent_ids=[],
        code_ref="ingestion/fmp_client.py",
        user="ingestion_agent"
    )
    print(f"\n✓ Created: {raw_lineage.dataset_name} v{raw_lineage.version}")
    
    # Create lineage for normalized data
    norm_lineage = tracker.create_lineage_record(
        dataset_name="AAPL_financials_normalized",
        version="v1",
        transformation="COA mapping, FX conversion to USD",
        parent_ids=[raw_lineage.lineage_id],
        code_ref="agents/normalization_agent.py",
        user="normalization_agent"
    )
    print(f"✓ Created: {norm_lineage.dataset_name} v{norm_lineage.version}")
    
    # Create lineage for DCF model
    dcf_lineage = tracker.create_lineage_record(
        dataset_name="AAPL_DCF_model",
        version="v1",
        transformation="DCF valuation with WACC=7.8%, g=2.5%",
        parent_ids=[norm_lineage.lineage_id],
        code_ref="engines/dcf_engine.py",
        user="modeling_agent"
    )
    print(f"✓ Created: {dcf_lineage.dataset_name} v{dcf_lineage.version}")
    
    # Approve
    tracker.approve_version(dcf_lineage.lineage_id, "analyst@firm.com")
    print(f"✓ Approved: {dcf_lineage.dataset_name}")
    
    # Get lineage chain
    chain = tracker.get_lineage_chain("AAPL_DCF_model", "v1")
    print(f"\n✓ Lineage Chain ({len(chain)} records):")
    for record in chain:
        print(f"  - {record['dataset_name']} v{record['version']}: {record['transformation']}")
    
    # Create provenance graph
    asyncio.run(tracker.create_provenance_graph("AAPL_DCF_model", "v1"))
    print(f"✓ Provenance graph created in Cognee")
    
    tracker.close()
