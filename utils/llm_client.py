"""
DeepSeek LLM Client
Handles LLM interactions for reasoning, analysis, and text generation
"""

from typing import List, Dict, Any, Optional, Generator
from openai import OpenAI
from loguru import logger

from config.settings import get_settings


class LLMClient:
    """Client for DeepSeek LLM API (OpenAI-compatible)"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize LLM client
        
        Args:
            api_key: DeepSeek API key (optional, will use settings if not provided)
            model: Model name (optional, will use settings if not provided)
        """
        settings = get_settings()
        self.api_key = api_key or settings.deepseek_api_key
        self.model = model or settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
        self.base_url = settings.deepseek_api_url
        
        # Initialize OpenAI client with DeepSeek endpoint
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        logger.info(f"LLM Client initialized with model: {self.model}")
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> str:
        """
        Send chat completion request
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max tokens
            stream: Whether to stream the response
            
        Returns:
            Response text
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                stream=stream
            )
            
            if stream:
                return response  # Return generator for streaming
            
            content = response.choices[0].message.content
            logger.debug(f"LLM response: {content[:100]}...")
            return content
            
        except Exception as e:
            logger.error(f"LLM request failed: {str(e)}")
            raise
    
    def analyze_mda(self, mda_text: str) -> Dict[str, Any]:
        """
        Analyze MD&A section and extract key insights
        
        Args:
            mda_text: MD&A text content
            
        Returns:
            Dictionary with analysis results
        """
        prompt = f"""Analyze the following Management Discussion & Analysis (MD&A) section and provide:

1. Key business trends and developments
2. Revenue drivers and headwinds
3. Profitability analysis (margin trends, cost pressures)
4. Liquidity and capital resources assessment
5. Forward-looking risks and opportunities
6. Red flags or areas of concern

MD&A Text:
{mda_text[:8000]}

Provide a structured JSON response with these sections."""

        messages = [
            {"role": "system", "content": "You are a financial analyst specializing in M&A due diligence. Provide detailed, data-driven analysis."},
            {"role": "user", "content": prompt}
        ]
        
        response = self.chat(messages, temperature=0.1)
        
        try:
            import json
            return json.loads(response)
        except:
            return {"raw_analysis": response}
    
    def extract_clauses(self, text: str, clause_types: List[str]) -> List[Dict[str, Any]]:
        """
        Extract specific clause types from legal text
        
        Args:
            text: Legal document text
            clause_types: Types of clauses to extract (e.g., 'change-of-control', 'indemnity')
            
        Returns:
            List of extracted clauses with metadata
        """
        clause_list = ", ".join(clause_types)
        
        prompt = f"""Extract the following types of clauses from the text: {clause_list}

For each clause found, provide:
1. Clause type
2. Title/description
3. Exact text (quote)
4. Page/section reference if available
5. Risk rating (Low/Medium/High)
6. Brief analysis of implications

Text:
{text[:8000]}

Provide response as a JSON array of clause objects."""

        messages = [
            {"role": "system", "content": "You are a legal analyst specializing in M&A transactions. Extract clauses precisely and assess their risk implications."},
            {"role": "user", "content": prompt}
        ]
        
        response = self.chat(messages, temperature=0.1)
        
        try:
            import json
            return json.loads(response)
        except:
            return [{"raw_extraction": response}]
    
    def explain_anomaly(self, metric: str, context: Dict[str, Any]) -> str:
        """
        Explain financial anomalies or outliers
        
        Args:
            metric: Name of the metric with anomaly
            context: Context data (historical values, peer comparisons, etc.)
            
        Returns:
            Explanation text
        """
        prompt = f"""Analyze the following financial anomaly:

Metric: {metric}
Context: {context}

Provide:
1. Possible explanations for the anomaly
2. Whether it's a red flag or benign
3. Recommended follow-up questions or analyses
4. Impact on valuation considerations"""

        messages = [
            {"role": "system", "content": "You are a financial analyst with deep expertise in quality of earnings analysis."},
            {"role": "user", "content": prompt}
        ]
        
        return self.chat(messages, temperature=0.2)
    
    def generate_peer_rationale(
        self,
        target_company: str,
        peer_candidate: str,
        metrics: Dict[str, Any]
    ) -> str:
        """
        Generate rationale for including/excluding a peer
        
        Args:
            target_company: Target company name
            peer_candidate: Peer company name
            metrics: Comparison metrics
            
        Returns:
            Rationale text
        """
        prompt = f"""Evaluate {peer_candidate} as a peer for {target_company}.

Comparison metrics:
{metrics}

Provide:
1. Similarity assessment (business model, size, geography, growth)
2. Key differences that matter for valuation
3. Recommendation: Include or Exclude
4. Suggested weighting if included (1-10 scale)
5. Brief justification"""

        messages = [
            {"role": "system", "content": "You are a valuation expert determining appropriate peer companies for comparable company analysis."},
            {"role": "user", "content": prompt}
        ]
        
        return self.chat(messages, temperature=0.2)
    
    def write_ic_memo_section(
        self,
        section: str,
        data: Dict[str, Any],
        citations: Optional[List[str]] = None
    ) -> str:
        """
        Write a section of an Investment Committee memo
        
        Args:
            section: Section name (e.g., 'Executive Summary', 'Strategic Rationale')
            data: Data to include in the section
            citations: Source citations
            
        Returns:
            Formatted section text
        """
        citations_text = ""
        if citations:
            citations_text = f"\n\nCitations:\n" + "\n".join([f"- {c}" for c in citations])
        
        prompt = f"""Write the '{section}' section of an Investment Committee memorandum.

Data and findings:
{data}
{citations_text}

Requirements:
- Professional, concise writing
- Data-driven with specific numbers
- Clear investment thesis
- Balanced (opportunities and risks)
- Proper citations for all key facts"""

        messages = [
            {"role": "system", "content": "You are an investment banker writing an IC memo for a strategic M&A transaction."},
            {"role": "user", "content": prompt}
        ]
        
        return self.chat(messages, temperature=0.3, max_tokens=2000)
    
    def generate_red_flags_summary(
        self,
        financial_data: Dict[str, Any],
        filing_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate a summary of due diligence red flags
        
        Args:
            financial_data: Financial metrics and trends
            filing_data: Data from SEC filings
            
        Returns:
            List of red flag items with severity and impact
        """
        prompt = f"""Conduct a quality of earnings analysis and identify potential red flags.

Financial Data:
{financial_data}

Filing Data:
{filing_data}

For each red flag identified, provide:
1. Category (Revenue Recognition, Working Capital, Debt, Governance, etc.)
2. Severity (Low/Medium/High/Critical)
3. Description
4. Estimated financial impact (if quantifiable)
5. Recommended mitigation or further diligence

Provide response as a JSON array of red flag objects."""

        messages = [
            {"role": "system", "content": "You are a due diligence expert conducting financial quality of earnings analysis for M&A transactions."},
            {"role": "user", "content": prompt}
        ]
        
        response = self.chat(messages, temperature=0.1, max_tokens=3000)
        
        try:
            import json
            return json.loads(response)
        except:
            return [{"raw_analysis": response}]
    
    def create_task_plan(self, task_description: str) -> List[Dict[str, Any]]:
        """
        Create a task execution plan with dependencies
        
        Args:
            task_description: High-level task description
            
        Returns:
            List of task steps with dependencies
        """
        prompt = f"""Create a detailed execution plan for the following task:

{task_description}

For each step, provide:
1. Step number
2. Description
3. Required tools/data sources
4. Dependencies (which steps must complete first)
5. Expected outputs

Provide response as a JSON array of step objects."""

        messages = [
            {"role": "system", "content": "You are a project planner creating detailed execution plans for M&A analysis workflows."},
            {"role": "user", "content": prompt}
        ]
        
        response = self.chat(messages, temperature=0.2)
        
        try:
            import json
            return json.loads(response)
        except:
            # Return a simple fallback plan
            return [{"description": "Execute task", "raw_plan": response}]
    
    def generate_text(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate text from a simple prompt (convenience method)
        
        Args:
            prompt: Text prompt
            temperature: Override default temperature
            max_tokens: Override default max tokens
            
        Returns:
            Generated text
        """
        messages = [
            {"role": "user", "content": prompt}
        ]
        return self.chat(messages, temperature=temperature, max_tokens=max_tokens)
    
    def summarize_for_cognee(
        self,
        content: str,
        content_type: str,
        max_length: int = 500
    ) -> str:
        """
        Create a concise summary optimized for knowledge graph storage
        
        Args:
            content: Original content
            content_type: Type of content (filing, analysis, etc.)
            max_length: Maximum summary length
            
        Returns:
            Summary text
        """
        prompt = f"""Summarize the following {content_type} in {max_length} characters or less.
Focus on:
- Key facts and figures
- Critical decisions or findings
- Relationships to other entities
- Temporal information (dates, periods)

Content:
{content[:5000]}"""

        messages = [
            {"role": "system", "content": "You are creating concise, fact-dense summaries for knowledge graph ingestion."},
            {"role": "user", "content": prompt}
        ]
        
        summary = self.chat(messages, temperature=0.1, max_tokens=200)
        return summary[:max_length]
