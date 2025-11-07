"""
Interactive M&A Q&A Agent
Allows you to ask questions about a completed M&A analysis

Usage:
    python interactive_ma_qa.py

Or import and use programmatically:
    from interactive_ma_qa import InteractiveMergerQA
    qa = InteractiveMergerQA(session_id="your_session_id")
    answer = qa.ask("What are the main synergies?")
"""

import json
from typing import Dict, Any, Optional
from loguru import logger
from utils.llm_client_production import get_llm_client
from storage import get_memory_manager


class InteractiveMergerQA:
    """
    Interactive Q&A agent for M&A analysis
    Uses production LLM with full context of the analysis
    """
    
    def __init__(self, session_id: Optional[str] = None, analysis_results: Optional[Dict] = None):
        """
        Initialize Q&A agent
        
        Args:
            session_id: Session ID of completed analysis (to load from memory)
            analysis_results: Or provide analysis results directly
        """
        self.llm = get_llm_client()
        self.memory = get_memory_manager()
        self.analysis_results = analysis_results
        self.session_id = session_id
        self.conversation_history = []
        
        # Load analysis if session_id provided
        if session_id and not analysis_results:
            self._load_analysis(session_id)
        
        logger.info("Interactive M&A Q&A Agent initialized")
    
    def _load_analysis(self, session_id: str):
        """Load analysis from memory"""
        try:
            history = self.memory.get_history(session_id=session_id, limit=1)
            if history:
                self.analysis_results = json.loads(history[0]['results'])
                logger.success(f"Loaded analysis for session: {session_id}")
            else:
                logger.warning(f"No analysis found for session: {session_id}")
        except Exception as e:
            logger.error(f"Failed to load analysis: {str(e)}")
    
    def ask(self, question: str, include_context: bool = True) -> str:
        """
        Ask a question about the M&A analysis
        
        Args:
            question: Your question about the merger
            include_context: Whether to include analysis context
            
        Returns:
            Answer from the LLM
        """
        logger.info(f"Question: {question}")
        
        # Build context
        context = ""
        if include_context and self.analysis_results:
            context = self._build_context()
        
        # Build conversation messages
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert M&A advisor with deep knowledge of this specific transaction. "
                    "Answer questions based on the analysis provided. Be specific, use data from the "
                    "analysis, and provide actionable insights. If you don't have enough information, "
                    "say so and suggest what additional analysis would be helpful."
                )
            }
        ]
        
        # Add context
        if context:
            messages.append({
                "role": "system",
                "content": f"Analysis Context:\n{context}"
            })
        
        # Add conversation history (last 5 exchanges)
        for msg in self.conversation_history[-10:]:
            messages.append(msg)
        
        # Add current question
        messages.append({
            "role": "user",
            "content": question
        })
        
        # Get answer
        try:
            answer = self.llm.chat(messages, temperature=0.2, max_tokens=2000)
            
            # Store in conversation history
            self.conversation_history.append({
                "role": "user",
                "content": question
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": answer
            })
            
            return answer
            
        except Exception as e:
            logger.error(f"Question failed: {str(e)}")
            return f"Error: {str(e)}"
    
    def _build_context(self) -> str:
        """Build context string from analysis results"""
        try:
            context_parts = []
            
            # Deal overview
            if self.analysis_results:
                context_parts.append(f"DEAL: {self.analysis_results.get('acquirer')} acquiring {self.analysis_results.get('target')}")
                context_parts.append(f"Session: {self.analysis_results.get('session_id')}")
                context_parts.append("")
            
            # Strategic rationale
            if self.analysis_results.get('insights', {}).get('strategic_rationale'):
                context_parts.append("STRATEGIC RATIONALE:")
                context_parts.append(self.analysis_results['insights']['strategic_rationale'][:1000])
                context_parts.append("")
            
            # Valuations
            if self.analysis_results.get('valuations'):
                context_parts.append("VALUATIONS:")
                context_parts.append(json.dumps(self.analysis_results['valuations'], indent=2)[:1000])
                context_parts.append("")
            
            # Due diligence
            if self.analysis_results.get('insights', {}).get('due_diligence'):
                context_parts.append("DUE DILIGENCE ITEMS:")
                context_parts.append(self.analysis_results['insights']['due_diligence'][:1000])
                context_parts.append("")
            
            # Recommendations
            if self.analysis_results.get('recommendations', {}).get('final'):
                context_parts.append("RECOMMENDATIONS:")
                context_parts.append(self.analysis_results['recommendations']['final'][:1000])
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Context building failed: {str(e)}")
            return "Analysis context unavailable"
    
    def get_suggested_questions(self) -> list:
        """Get suggested questions based on the analysis"""
        return [
            "What are the key synergies in this deal?",
            "What is the fair valuation range for the target?",
            "What are the main integration risks?",
            "How does this compare to similar transactions?",
            "What are the regulatory concerns?",
            "What should be the negotiation priorities?",
            "How long should the integration take?",
            "What are the deal breakers we should watch for?",
            "How will this impact the acquirer's financials?",
            "What are the talent retention considerations?"
        ]
    
    def interactive_session(self):
        """Start an interactive Q&A session"""
        print("\n" + "="*80)
        print("INTERACTIVE M&A Q&A SESSION")
        print("="*80)
        
        if self.analysis_results:
            print(f"\nDeal: {self.analysis_results.get('acquirer')} acquiring {self.analysis_results.get('target')}")
            print(f"Session: {self.analysis_results.get('session_id')}")
        
        print("\nAsk me anything about this merger!")
        print("Type 'suggestions' to see suggested questions")
        print("Type 'context' to see analysis summary")
        print("Type 'metrics' to see LLM usage")
        print("Type 'quit' or 'exit' to end session")
        print("="*80 + "\n")
        
        while True:
            try:
                # Get question from user
                question = input("\n🤔 Your Question: ").strip()
                
                if not question:
                    continue
                
                # Handle commands
                if question.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Ending Q&A session. Goodbye!")
                    break
                
                elif question.lower() == 'suggestions':
                    print("\n💡 Suggested Questions:")
                    for i, q in enumerate(self.get_suggested_questions(), 1):
                        print(f"   {i}. {q}")
                    continue
                
                elif question.lower() == 'context':
                    print("\n📄 Analysis Context:")
                    print("-" * 80)
                    print(self._build_context()[:2000])
                    print("-" * 80)
                    continue
                
                elif question.lower() == 'metrics':
                    metrics = self.llm.get_metrics()
                    print("\n📊 LLM Usage Metrics:")
                    print(f"   Total requests: {metrics['metrics']['total_requests']}")
                    print(f"   Total tokens: {metrics['metrics']['total_tokens']:,}")
                    print(f"   Total cost: ${metrics['metrics']['total_cost_usd']:.4f}")
                    print(f"   Success rate: {metrics['metrics']['success_rate']:.1%}")
                    continue
                
                # Ask the question
                print("\n🤖 AI M&A Advisor:\n")
                answer = self.ask(question)
                print(answer)
                print("\n" + "-"*80)
                
            except KeyboardInterrupt:
                print("\n\n👋 Session interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                logger.error(f"Interactive session error: {str(e)}")


def main():
    """Main function for interactive mode"""
    import sys
    
    print("\n" + "="*80)
    print("M&A ANALYSIS Q&A AGENT - PRODUCTION MODE")
    print("="*80)
    
    # Check if session ID provided as argument
    session_id = None
    if len(sys.argv) > 1:
        session_id = sys.argv[1]
    else:
        # Try to find most recent session
        memory = get_memory_manager()
        recent = memory.get_history(limit=1)
        if recent:
            session_id = recent[0]['session_id']
            print(f"\n✓ Found recent analysis: {session_id}")
    
    if not session_id:
        print("\n⚠️  No analysis found. Please run an analysis first:")
        print("   python run_comprehensive_ma_analysis.py")
        print("\nOr provide a session ID:")
        print("   python interactive_ma_qa.py <session_id>")
        return
    
    # Initialize Q&A agent
    qa = InteractiveMergerQA(session_id=session_id)
    
    # Check if analysis loaded
    if not qa.analysis_results:
        print(f"\n❌ Could not load analysis for session: {session_id}")
        return
    
    # Start interactive session
    qa.interactive_session()
    
    # Show final metrics
    metrics = qa.llm.get_metrics()
    print("\n" + "="*80)
    print("SESSION SUMMARY")
    print("="*80)
    print(f"Questions asked: {len(qa.conversation_history) // 2}")
    print(f"LLM requests: {metrics['metrics']['total_requests']}")
    print(f"Tokens used: {metrics['metrics']['total_tokens']:,}")
    print(f"Total cost: ${metrics['metrics']['total_cost_usd']:.4f}")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
