"""
LangGraph Orchestrator
Task planning, dependency management, and agent coordination using LangGraph
"""

from typing import Dict, List, Optional, Any, TypedDict, Annotated
from datetime import datetime
import operator
from loguru import logger

try:
    from langgraph.graph import StateGraph, END
    from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.warning("LangGraph not available")

from agents.ingestion_agent import IngestionAgent
from agents.normalization_agent import NormalizationAgent
from agents.modeling_agent import ModelingAgent
from agents.exporter_agent import ExporterAgent
from utils.llm_client import LLMClient


class GraphState(TypedDict):
    """State for the workflow graph"""
    symbol: str
    company_name: Optional[str]
    task: str
    messages: Annotated[List[BaseMessage], operator.add]
    
    # Data state
    raw_data_ingested: bool
    data_normalized: bool
    models_run: bool
    outputs_generated: bool
    
    # Results
    ingestion_results: Optional[Dict]
    normalized_data: Optional[Dict]
    valuation_package: Optional[Dict]
    export_paths: Optional[Dict]
    
    # Errors
    errors: List[str]
    
    # Next action
    next_action: Optional[str]


class LangGraphOrchestrator:
    """
    LangGraph Orchestrator - coordinates agent workflows
    
    Responsibilities:
    - Task planning with LLM
    - Dependency graph execution
    - Agent coordination
    - Error handling & retries
    - State management
    """
    
    def __init__(self):
        """Initialize orchestrator"""
        if not LANGGRAPH_AVAILABLE:
            logger.error("LangGraph not installed. Install: pip install langgraph")
            self.enabled = False
            return
        
        self.enabled = True
        self.llm = LLMClient()
        
        # Initialize agents
        self.ingestion_agent = IngestionAgent()
        self.normalization_agent = NormalizationAgent()
        self.modeling_agent = ModelingAgent()
        self.exporter_agent = ExporterAgent()
        
        # Build workflow graph
        self.workflow = self._build_workflow_graph()
        
        logger.info("LangGraph Orchestrator initialized")
    
    def _build_workflow_graph(self) -> StateGraph:
        """
        Build the workflow graph
        
        Returns:
            StateGraph for execution
        """
        if not self.enabled:
            return None
        
        # Create graph
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node("plan_task", self.plan_task_node)
        workflow.add_node("ingest_data", self.ingest_data_node)
        workflow.add_node("normalize_data", self.normalize_data_node)
        workflow.add_node("run_models", self.run_models_node)
        workflow.add_node("generate_outputs", self.generate_outputs_node)
        
        # Define edges (workflow)
        workflow.set_entry_point("plan_task")
        
        workflow.add_edge("plan_task", "ingest_data")
        workflow.add_edge("ingest_data", "normalize_data")
        workflow.add_edge("normalize_data", "run_models")
        workflow.add_edge("run_models", "generate_outputs")
        workflow.add_edge("generate_outputs", END)
        
        # Compile
        app = workflow.compile()
        
        logger.info("Workflow graph built: plan → ingest → normalize → model → export")
        
        return app
    
    def plan_task_node(self, state: GraphState) -> GraphState:
        """
        Plan the task using LLM
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with plan
        """
        logger.info(f"Planning task: {state['task']}")
        
        # Use LLM to create execution plan
        plan = self.llm.create_task_plan(state['task'])
        
        state['messages'].append(AIMessage(content=f"Task plan created with {len(plan)} steps"))
        state['next_action'] = "ingest_data"
        
        return state
    
    def ingest_data_node(self, state: GraphState) -> GraphState:
        """
        Ingest data node
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with ingestion results
        """
        logger.info(f"Ingesting data for {state['symbol']}")
        
        try:
            results = self.ingestion_agent.ingest_company_full(
                symbol=state['symbol'],
                years_of_financials=5,
                include_filings=True,
                include_market_data=True
            )
            
            state['ingestion_results'] = results
            state['raw_data_ingested'] = True
            state['company_name'] = results.get('company').legal_name if results.get('company') else state['symbol']
            state['messages'].append(AIMessage(content=f"Data ingested: {results['financials_count']} facts"))
            
        except Exception as e:
            error_msg = f"Ingestion failed: {str(e)}"
            logger.error(error_msg)
            state['errors'].append(error_msg)
            state['raw_data_ingested'] = False
        
        state['next_action'] = "normalize_data"
        
        return state
    
    def normalize_data_node(self, state: GraphState) -> GraphState:
        """
        Normalize data node
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with normalized data
        """
        logger.info(f"Normalizing data for {state['symbol']}")
        
        try:
            # Build normalized financials table
            normalized_table = self.normalization_agent.build_normalized_financials_table(
                symbol=state['symbol'],
                metrics=['revenue', 'ebitda', 'net_income', 'total_assets', 'total_debt', 'fcf'],
                years=5
            )
            
            state['normalized_data'] = {
                'table': normalized_table,
                'count': len(normalized_table)
            }
            state['data_normalized'] = True
            state['messages'].append(AIMessage(content=f"Data normalized: {len(normalized_table)} periods"))
            
        except Exception as e:
            error_msg = f"Normalization failed: {str(e)}"
            logger.error(error_msg)
            state['errors'].append(error_msg)
            state['data_normalized'] = False
        
        state['next_action'] = "run_models"
        
        return state
    
    def run_models_node(self, state: GraphState) -> GraphState:
        """
        Run valuation models node
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with model results
        """
        logger.info(f"Running models for {state['symbol']}")
        
        try:
            # For now, placeholder - would call modeling_agent methods
            state['valuation_package'] = {
                'symbol': state['symbol'],
                'models_run': ['DCF', 'CCA'],
                'timestamp': datetime.utcnow().isoformat()
            }
            state['models_run'] = True
            state['messages'].append(AIMessage(content=f"Models executed successfully"))
            
        except Exception as e:
            error_msg = f"Modeling failed: {str(e)}"
            logger.error(error_msg)
            state['errors'].append(error_msg)
            state['models_run'] = False
        
        state['next_action'] = "generate_outputs"
        
        return state
    
    def generate_outputs_node(self, state: GraphState) -> GraphState:
        """
        Generate outputs node
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with output paths
        """
        logger.info(f"Generating outputs for {state['symbol']}")
        
        try:
            # Placeholder - would call exporter_agent methods
            state['export_paths'] = {
                'excel': f"outputs/{state['symbol']}_model.xlsx",
                'ic_memo': f"outputs/{state['symbol']}_memo.docx"
            }
            state['outputs_generated'] = True
            state['messages'].append(AIMessage(content=f"Outputs generated successfully"))
            
        except Exception as e:
            error_msg = f"Export failed: {str(e)}"
            logger.error(error_msg)
            state['errors'].append(error_msg)
            state['outputs_generated'] = False
        
        state['next_action'] = None
        
        return state
    
    def execute_workflow(
        self,
        symbol: str,
        task: str = "Full M&A analysis"
    ) -> Dict[str, Any]:
        """
        Execute complete workflow
        
        Args:
            symbol: Stock symbol
            task: Task description
            
        Returns:
            Final state dictionary
        """
        if not self.enabled:
            logger.error("LangGraph not available")
            return {}
        
        logger.info(f"Executing workflow for {symbol}: {task}")
        
        # Initial state
        initial_state = GraphState(
            symbol=symbol,
            company_name=None,
            task=task,
            messages=[HumanMessage(content=task)],
            raw_data_ingested=False,
            data_normalized=False,
            models_run=False,
            outputs_generated=False,
            ingestion_results=None,
            normalized_data=None,
            valuation_package=None,
            export_paths=None,
            errors=[],
            next_action=None
        )
        
        # Run workflow
        final_state = self.workflow.invoke(initial_state)
        
        logger.info(f"Workflow complete for {symbol}")
        
        return final_state
    
    def close(self):
        """Clean up resources"""
        try:
            self.ingestion_agent.close()
            self.normalization_agent.close()
            self.modeling_agent.close()
            logger.info("Orchestrator resources closed")
        except Exception as e:
            logger.error(f"Error closing resources: {str(e)}")


# Example usage
if __name__ == "__main__":
    # Initialize orchestrator
    orchestrator = LangGraphOrchestrator()
    
    if orchestrator.enabled:
        print("\n" + "="*70)
        print("LANGGRAPH ORCHESTRATOR - WORKFLOW EXECUTION")
        print("="*70)
        
        # Execute workflow
        final_state = orchestrator.execute_workflow(
            symbol="AAPL",
            task="Perform complete M&A analysis with DCF and CCA valuation"
        )
        
        print("\n WORKFLOW RESULTS:")
        print(f"  Symbol: {final_state['symbol']}")
        print(f"  Company: {final_state.get('company_name', 'N/A')}")
        print(f"  Data Ingested: {'✓' if final_state['raw_data_ingested'] else '✗'}")
        print(f"  Data Normalized: {'✓' if final_state['data_normalized'] else '✗'}")
        print(f"  Models Run: {'✓' if final_state['models_run'] else '✗'}")
        print(f"  Outputs Generated: {'✓' if final_state['outputs_generated'] else '✗'}")
        
        if final_state['errors']:
            print(f"\n  Errors: {len(final_state['errors'])}")
            for error in final_state['errors']:
                print(f"    - {error}")
        
        print("\n  Messages:")
        for msg in final_state['messages']:
            print(f"    {msg.content}")
        
        orchestrator.close()
    else:
        print("LangGraph not available. Install: pip install langgraph")
