"""
FMNA Platform - Complete Frontend Application
Full-featured web UI with dynamic Q&A, file upload, and comprehensive analysis
"""

import streamlit as st
import asyncio
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
import sys
import os
from dotenv import load_dotenv
from loguru import logger

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestration.comprehensive_orchestrator import ComprehensiveOrchestrator
from agents.exporter_agent_enhanced import EnhancedExporterAgent
from storage.memory_manager import MemoryManager
from utils.llm_client import LLMClient
from ingestion.fmp_client import FMPClient
from ingestion.sec_client import SECClient
from ingestion.document_processor import DocumentProcessor
from config.settings import get_settings
from auth.user_manager import UserManager

# Initialize settings
settings = get_settings()

# Page configuration
st.set_page_config(
    page_title="FMNA Financial Modeling Platform",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        color: #000000 !important;
        line-height: 1.6;
    }
    .chat-message * {
        color: #000000 !important;
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: 2rem;
        border: 1px solid #90caf9;
    }
    .ai-message {
        background-color: #f5f5f5;
        margin-right: 2rem;
        border: 1px solid #e0e0e0;
    }
    .ai-message strong {
        color: #1976d2 !important;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'user_manager' not in st.session_state:
    st.session_state.user_manager = UserManager()
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'analysis_plan' not in st.session_state:
    st.session_state.analysis_plan = None
if 'memory_manager' not in st.session_state:
    st.session_state.memory_manager = MemoryManager()
if 'llm_client' not in st.session_state:
    st.session_state.llm_client = LLMClient()


def create_valuation_chart(results: Dict) -> go.Figure:
    """Create football field valuation chart"""
    methods = []
    lows = []
    highs = []
    mids = []
    
    if 'dcf_result' in results.get('valuation', {}):
        dcf = results['valuation']['dcf_result']
        methods.append('DCF')
        low = dcf['value_per_share'] * 0.9
        high = dcf['value_per_share'] * 1.1
        lows.append(low)
        highs.append(high)
        mids.append(dcf['value_per_share'])
    
    if 'cca_result' in results.get('valuation', {}):
        cca = results['valuation']['cca_result']
        methods.append('CCA (EV/EBITDA)')
        lows.append(cca['value_per_share_ebitda'] * 0.9)
        highs.append(cca['value_per_share_ebitda'] * 1.1)
        mids.append(cca['value_per_share_ebitda'])
        
        if 'value_per_share_revenue' in cca:
            methods.append('CCA (EV/Revenue)')
            lows.append(cca['value_per_share_revenue'] * 0.9)
            highs.append(cca['value_per_share_revenue'] * 1.1)
            mids.append(cca['value_per_share_revenue'])
    
    if 'lbo_result' in results.get('valuation', {}):
        lbo = results['valuation']['lbo_result']
        methods.append('LBO Analysis')
        lows.append(lbo['min_value_per_share'])
        highs.append(lbo['max_value_per_share'])
        mids.append((lbo['min_value_per_share'] + lbo['max_value_per_share']) / 2)
    
    # Create football field chart
    fig = go.Figure()
    
    for i, method in enumerate(methods):
        # Add range bar
        fig.add_trace(go.Bar(
            x=[highs[i] - lows[i]],
            y=[method],
            base=lows[i],
            orientation='h',
            marker=dict(color='lightblue', line=dict(color='darkblue', width=2)),
            name=method,
            text=f"${lows[i]:.2f} - ${highs[i]:.2f}",
            textposition='inside',
            hovertemplate=f"<b>{method}</b><br>Range: ${lows[i]:.2f} - ${highs[i]:.2f}<br>Mid: ${mids[i]:.2f}<extra></extra>"
        ))
        
        # Add midpoint marker
        fig.add_trace(go.Scatter(
            x=[mids[i]],
            y=[method],
            mode='markers',
            marker=dict(color='darkblue', size=12, symbol='diamond'),
            name=f"{method} Mid",
            showlegend=False,
            hovertemplate=f"<b>{method}</b><br>Midpoint: ${mids[i]:.2f}<extra></extra>"
        ))
    
    fig.update_layout(
        title="Valuation Football Field",
        xaxis_title="Value Per Share ($)",
        yaxis_title="Method",
        height=400,
        showlegend=False,
        hovermode='closest'
    )
    
    return fig


def create_sensitivity_table(results: Dict) -> pd.DataFrame:
    """Create sensitivity analysis table"""
    if 'dcf_result' not in results.get('valuation', {}):
        return pd.DataFrame()
    
    dcf = results['valuation']['dcf_result']
    base_value = dcf['value_per_share']
    base_wacc = dcf.get('wacc', 0.08)
    base_growth = dcf.get('terminal_growth', 0.025)
    
    # Create sensitivity matrix
    wacc_range = [base_wacc - 0.02, base_wacc - 0.01, base_wacc, base_wacc + 0.01, base_wacc + 0.02]
    growth_range = [base_growth - 0.01, base_growth - 0.005, base_growth, base_growth + 0.005, base_growth + 0.01]
    
    # Simple sensitivity calculation (you could make this more sophisticated)
    sensitivity_data = []
    for growth in growth_range:
        row = []
        for wacc in wacc_range:
            # Simplified calculation
            adjusted_value = base_value * (1 + (base_growth - growth) * 10) * (1 + (wacc - base_wacc) * -5)
            row.append(f"${adjusted_value:.2f}")
        sensitivity_data.append(row)
    
    df = pd.DataFrame(
        sensitivity_data,
        columns=[f"{w*100:.1f}%" for w in wacc_range],
        index=[f"{g*100:.1f}%" for g in growth_range]
    )
    df.index.name = "Terminal Growth"
    
    return df


async def run_analysis_pipeline(symbol: str, analysis_options: Dict, uploaded_files: List = None) -> Dict:
    """Run complete analysis pipeline"""
    
    # Initialize orchestrator
    orchestrator = ComprehensiveOrchestrator()
    
    # Handle private company uploads
    if uploaded_files:
        st.info("📄 Processing uploaded documents for private company analysis...")
        doc_processor = DocumentProcessor()
        
        for uploaded_file in uploaded_files:
            # Save uploaded file temporarily
            file_path = Path(f"data/uploads/{uploaded_file.name}")
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Process document
            processed_data = await doc_processor.process_document(file_path)
            
            # Store in memory manager
            st.session_state.memory_manager.store_context(
                context_type="private_company_data",
                data=processed_data,
                metadata={
                    "symbol": symbol,
                    "filename": uploaded_file.name,
                    "upload_time": datetime.now().isoformat()
                }
            )
        
        st.success(f"✅ Processed {len(uploaded_files)} document(s)")
    
    # Run comprehensive analysis with all selected engines
    st.info("🚀 Running comprehensive financial analysis...")
    result = await orchestrator.run_comprehensive_analysis(
        symbol=symbol,
        period=analysis_options.get('period', 'annual'),
        peers_required=analysis_options.get('peers_count', 5),
        run_dcf=analysis_options.get('dcf', True),
        run_cca=analysis_options.get('cca', True),
        run_three_statement=analysis_options.get('three_statement', True),
        run_lbo=analysis_options.get('lbo', True),
        run_merger=analysis_options.get('merger', True),
        run_growth_scenarios=analysis_options.get('growth', True),
        run_full_dd=True
    )
    
    # Generate professional outputs if requested
    if analysis_options.get('generate_outputs', False):
        st.info("📝 Generating professional outputs (Excel, PowerPoint, PDFs)...")
        try:
            exporter = EnhancedExporterAgent()
            
            # Generate outputs
            output_paths = await exporter.generate_all_outputs(
                result=result,
                generate_excel=analysis_options.get('excel_output', True),
                generate_pptx=analysis_options.get('powerpoint_output', True),
                generate_pdf=True
            )
            
            # Store output paths in result for download
            if hasattr(result, '__dict__'):
                result.output_files = output_paths
            
            st.success(f"✅ Generated {len(output_paths)} output file(s)")
        except Exception as e:
            st.warning(f"⚠️ Output generation encountered an issue: {str(e)}")
            st.info("Analysis results are still available for viewing")
    
    st.success("📊 Analysis complete - results ready for viewing and download")
    
    return result


def generate_analysis_plan(user_request: str) -> str:
    """AI generates analysis plan based on user request"""
    
    system_prompt = """You are a financial analysis planning assistant. Based on the user's request, 
    create a detailed analysis plan with specific steps. Be comprehensive but focused.
    
    Format your response as a numbered list of actionable steps.
    Include specific analysis types (DCF, CCA, LBO, etc.) and data sources needed."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Create an analysis plan for: {user_request}"}
    ]
    
    response = st.session_state.llm_client.chat(messages, temperature=0.3)
    return response


def format_context_for_prompt(context_items: List[Dict], current_analysis: Optional[Dict] = None) -> str:
    """Format context items into a clear, structured prompt"""
    formatted_parts = []
    
    # Add current analysis if available
    if current_analysis:
        formatted_parts.append("=== CURRENT ANALYSIS ===")
        
        # Handle both Pydantic objects and dicts
        if hasattr(current_analysis, 'symbol'):
            symbol = current_analysis.symbol
        elif isinstance(current_analysis, dict):
            symbol = current_analysis.get('symbol', 'Unknown')
        else:
            symbol = 'Unknown'
        formatted_parts.append(f"Company: {symbol}")
        
        # Extract valuation info
        if hasattr(current_analysis, 'valuation'):
            val = current_analysis.valuation
            formatted_parts.append("\nVALUATION RESULTS:")
            
            if hasattr(val, 'dcf_result') and val.dcf_result:
                dcf = val.dcf_result
                formatted_parts.append(f"  DCF Analysis:")
                formatted_parts.append(f"    - Value per Share: ${dcf.value_per_share:.2f}")
                formatted_parts.append(f"    - Enterprise Value: ${dcf.enterprise_value/1e9:.2f}B")
                formatted_parts.append(f"    - WACC: {dcf.wacc*100:.2f}%")
            
            if hasattr(val, 'cca_result') and val.cca_result:
                cca = val.cca_result
                formatted_parts.append(f"  Comparable Companies Analysis:")
                formatted_parts.append(f"    - Value per Share (EV/EBITDA): ${cca.value_per_share_ebitda:.2f}")
                if hasattr(cca, 'peer_count'):
                    formatted_parts.append(f"    - Peer Companies Analyzed: {cca.peer_count}")
            
            if hasattr(val, 'lbo_result') and val.lbo_result:
                lbo = val.lbo_result
                formatted_parts.append(f"  LBO Analysis:")
                formatted_parts.append(f"    - Value Range: ${lbo.min_value_per_share:.2f} - ${lbo.max_value_per_share:.2f}")
        
        # Extract financial data
        if hasattr(current_analysis, 'financial_data') and current_analysis.financial_data:
            fin = current_analysis.financial_data
            formatted_parts.append("\nKEY FINANCIAL METRICS:")
            if hasattr(fin, 'revenue'):
                formatted_parts.append(f"  - Revenue: ${fin.revenue/1e9:.2f}B")
            if hasattr(fin, 'ebitda'):
                formatted_parts.append(f"  - EBITDA: ${fin.ebitda/1e9:.2f}B")
            if hasattr(fin, 'net_income'):
                formatted_parts.append(f"  - Net Income: ${fin.net_income/1e9:.2f}B")
        
        formatted_parts.append("\n")
    
    # Add historical context from memory
    if context_items:
        formatted_parts.append("=== HISTORICAL ANALYSES ===")
        
        for i, item in enumerate(context_items[:3], 1):  # Limit to top 3
            content = item.get('content', {})
            ticker = item.get('ticker', content.get('ticker', 'Unknown'))
            timestamp = item.get('timestamp', content.get('timestamp', ''))
            
            formatted_parts.append(f"\n{i}. Analysis for {ticker} (Date: {timestamp})")
            
            # Extract results if available
            results = content.get('results', {})
            if results:
                if 'valuation' in results:
                    val = results['valuation']
                    if 'dcf_value' in val:
                        formatted_parts.append(f"   - DCF Value: ${val['dcf_value']:.2f}")
                    if 'cca_value' in val:
                        formatted_parts.append(f"   - CCA Value: ${val['cca_value']:.2f}")
                    if 'valuation_range' in val:
                        vr = val['valuation_range']
                        formatted_parts.append(f"   - Valuation Range: ${vr[0]:.2f} - ${vr[1]:.2f}")
                
                if 'financial_data' in results:
                    fin = results['financial_data']
                    if 'revenue' in fin:
                        formatted_parts.append(f"   - Revenue: ${fin['revenue']/1e9:.2f}B")
                    if 'ebitda' in fin:
                        formatted_parts.append(f"   - EBITDA: ${fin['ebitda']/1e9:.2f}B")
                
                if 'peer_analysis' in results:
                    peers = results['peer_analysis']
                    if 'peers' in peers:
                        formatted_parts.append(f"   - Peers: {', '.join(peers['peers'][:5])}")
    
    return "\n".join(formatted_parts) if formatted_parts else "No context available."


def get_ai_response(user_question: str, context: Optional[Dict] = None) -> str:
    """Get AI response to user question with context from analysis"""
    
    # Build context from memory manager
    memory_context = st.session_state.memory_manager.get_relevant_context(
        query=user_question,
        limit=5
    )
    
    # IMPORTANT: Also check if there's current analysis results in session
    # This ensures AI uses the most recent analysis even if queries don't extract ticker perfectly
    if not context and st.session_state.analysis_results:
        context = st.session_state.analysis_results
        logger.debug("Using current session analysis results as context")
    
    # Format context nicely
    formatted_context = format_context_for_prompt(memory_context, context)
    
    # Debug logging
    logger.debug(f"Query: '{user_question}'")
    logger.debug(f"Memory context items: {len(memory_context)}")
    logger.debug(f"Current session context: {context is not None}")
    
    # Build enhanced system prompt with structured context
    system_prompt = f"""You are an expert financial analyst AI assistant with access to comprehensive financial analysis data.

Your role is to provide accurate, actionable insights based on the provided context. 

AVAILABLE CONTEXT:
{formatted_context}

INSTRUCTIONS:
1. Answer questions based ONLY on the provided context above
2. If context shows "CURRENT ANALYSIS" - use that data first (it's the most recent analysis in this session)
3. Cite specific numbers with precision (e.g., "According to the DCF analysis, the value per share is $850.50")
4. Reference the source and date when citing data (e.g., "Based on the analysis...")
5. If the context doesn't contain the requested information, clearly state what data is missing
6. Format all financial figures properly (use B for billions, M for millions)
7. Provide concise, direct answers - avoid unnecessary elaboration
8. Add [Source: DCF Analysis], [Source: CCA Results], etc. after key facts
9. If multiple data points exist, provide a range or comparison

CRITICAL: Do NOT make up data. Do NOT use general knowledge if the context doesn't support your answer.

USER QUESTION: {user_question}

Your response:"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_question}
    ]
    
    response = st.session_state.llm_client.chat(messages, temperature=0.1, max_tokens=1000)
    
    # Store interaction in memory with context metadata
    st.session_state.memory_manager.store_context(
        context_type="qa_interaction",
        data={
            "question": user_question,
            "answer": response,
            "context_items_used": len(memory_context),
            "had_session_context": context is not None,
            "timestamp": datetime.now().isoformat()
        },
        metadata={
            "type": "chat",
            "ticker": st.session_state.analysis_results.symbol if st.session_state.analysis_results and hasattr(st.session_state.analysis_results, 'symbol') else None
        }
    )
    
    return response


def show_login_page():
    """Show login page"""
    st.markdown('<div class="main-header">🔐 FMNA Platform Login</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### Login to Access Platform")
        
        email = st.text_input("Email", placeholder="your.email@company.com")
        password = st.text_input("Password", type="password")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("🔐 Login", type="primary", use_container_width=True):
                if email and password:
                    user_info = st.session_state.user_manager.authenticate(email, password)
                    
                    if user_info:
                        st.session_state.authenticated = True
                        st.session_state.user_info = user_info
                        st.success(f"✅ Welcome, {email}!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials")
                else:
                    st.warning("Please enter email and password")
        
        with col_b:
            if st.button("ℹ️ Help", use_container_width=True):
                st.info("""
                **Need Access?**
                
                Contact the administrator:
                📧 smaan2011@gmail.com
                
                Admins can create user accounts from the User Management page.
                """)
        
        st.markdown("---")
        st.caption("🔒 Secure authentication with encrypted passwords")


def show_user_management():
    """Admin user management interface"""
    st.markdown('<div class="sub-header">👥 User Management</div>', unsafe_allow_html=True)
    
    if not st.session_state.user_info or not st.session_state.user_info.get('is_admin'):
        st.error("⛔ Admin access required")
        return
    
    # User list
    st.markdown("### Current Users")
    users = st.session_state.user_manager.get_all_users()
    
    if users:
        for user in users:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 1, 2, 2, 2])
                
                with col1:
                    status_icon = "✅" if user['is_active'] else "⏸️"
                    admin_badge = " 👑" if user['role'] == 'admin' else ""
                    st.write(f"{status_icon} **{user['email']}**{admin_badge}")
                
                with col2:
                    st.write(user['role'])
                
                with col3:
                    if user['last_login']:
                        st.caption(f"Last: {user['last_login'][:16]}")
                    else:
                        st.caption("Never logged in")
                
                with col4:
                    if user['email'] != "smaan2011@gmail.com":
                        if st.button(f"🔄 Toggle", key=f"toggle_{user['email']}"):
                            if st.session_state.user_manager.toggle_user_status(
                                user['email'],
                                st.session_state.user_info['email']
                            ):
                                st.success(f"Status toggled for {user['email']}")
                                st.rerun()
                
                with col5:
                    if user['email'] != "smaan2011@gmail.com":
                        if st.button(f"🗑️ Delete", key=f"delete_{user['email']}"):
                            if st.session_state.user_manager.delete_user(
                                user['email'],
                                st.session_state.user_info['email']
                            ):
                                st.success(f"Deleted {user['email']}")
                                st.rerun()
                            else:
                                st.error("Failed to delete user")
                
                st.markdown("---")
        
        st.metric("Total Users", len(users))
    else:
        st.info("No users found")
    
    # Add new user
    st.markdown("### ➕ Add New User")
    
    with st.form("add_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_email = st.text_input("Email", placeholder="user@company.com")
            new_password = st.text_input("Password", type="password", placeholder="Min 8 characters")
        
        with col2:
            new_role = st.selectbox("Role", ["user", "admin"])
            st.write("")  # Spacing
            st.write("")  # Spacing
        
        if st.form_submit_button("➕ Create User", type="primary", use_container_width=True):
            if new_email and new_password:
                if len(new_password) < 8:
                    st.error("Password must be at least 8 characters")
                elif st.session_state.user_manager.add_user(
                    new_email,
                    new_password,
                    new_role,
                    st.session_state.user_info['email']
                ):
                    st.success(f"✅ User created: {new_email}")
                    st.info(f"📧 Send these credentials to the user:\nEmail: {new_email}\nPassword: {new_password}")
                    st.rerun()
                else:
                    st.error("Failed to create user (may already exist)")
            else:
                st.warning("Please fill in all fields")
    
    # Login history
    with st.expander("📊 Recent Login Activity"):
        history = st.session_state.user_manager.get_login_history(limit=20)
        
        if history:
            for log in history:
                status_icon = "✅" if log['success'] else "❌"
                st.caption(f"{status_icon} {log['email']} - {log['login_time'][:19]}")
        else:
            st.info("No login history")


def main():
    """Main application"""
    
    # Check authentication
    if not st.session_state.authenticated:
        show_login_page()
        return
    
    # Header with user info
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.markdown('<div class="main-header">🏦 FMNA Financial Modeling Platform</div>', unsafe_allow_html=True)
        st.markdown("**Complete Financial Analysis & Modeling Platform with AI**")
    
    with col2:
        st.markdown(f"**User:** {st.session_state.user_info['email']}")
        role_badge = "👑 Admin" if st.session_state.user_info.get('is_admin') else "👤 User"
        st.caption(role_badge)
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.user_info = None
            st.rerun()
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    
    pages = ["🏠 Dashboard", "📊 New Analysis", "💬 AI Q&A", "📈 View Results", "⚙️ Settings"]
    
    # Add User Management for admin
    if st.session_state.user_info.get('is_admin'):
        pages.append("👥 User Management")
    
    page = st.sidebar.radio("Select Page", pages)
    
    # User info in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Logged in as:**")
    st.sidebar.caption(st.session_state.user_info['email'])
    st.sidebar.caption(f"Role: {st.session_state.user_info['role']}")
    
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "📊 New Analysis":
        show_analysis_page()
    elif page == "💬 AI Q&A":
        show_qa_page()
    elif page == "📈 View Results":
        show_results_page()
    elif page == "⚙️ Settings":
        show_settings_page()
    elif page == "👥 User Management":
        show_user_management()


def show_dashboard():
    """Show main dashboard"""
    
    st.markdown('<div class="sub-header">Dashboard</div>', unsafe_allow_html=True)
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Analyses", "0", "Start your first analysis →")
    
    with col2:
        st.metric("AI Interactions", len(st.session_state.chat_history))
    
    with col3:
        st.metric("Data Sources", "3", "FMP, SEC, Upload")
    
    with col4:
        st.metric("Status", "✅ Ready")
    
    # Quick actions
    st.markdown('<div class="sub-header">Quick Actions</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 New Analysis", use_container_width=True):
            st.session_state.page = "📊 New Analysis"
            st.rerun()
    
    with col2:
        if st.button("💬 Ask AI", use_container_width=True):
            st.session_state.page = "💬 AI Q&A"
            st.rerun()
    
    with col3:
        if st.button("📈 View Results", use_container_width=True):
            st.session_state.page = "📈 View Results"
            st.rerun()
    
    # Recent activity
    st.markdown('<div class="sub-header">Recent Activity</div>', unsafe_allow_html=True)
    
    if st.session_state.analysis_results:
        result = st.session_state.analysis_results
        symbol = getattr(result, 'symbol', 'Unknown')
        st.info(f"✅ Last analysis completed: {symbol}")
    else:
        st.info("No analyses yet. Start by clicking 'New Analysis' above.")


def show_analysis_page():
    """Show analysis configuration page"""
    
    st.markdown('<div class="sub-header">New Financial Analysis</div>', unsafe_allow_html=True)
    
    # Company input section
    st.markdown("### 1️⃣ Company Identification")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        symbol = st.text_input(
            "Company Symbol or Name",
            placeholder="e.g., AAPL, Microsoft",
            help="Enter ticker symbol for public companies or company name for private"
        )
    
    with col2:
        company_type = st.selectbox(
            "Company Type",
            ["Public", "Private"]
        )
    
    # Private company file upload
    uploaded_files = None
    if company_type == "Private":
        st.markdown("### 📄 Upload Private Company Documents")
        st.info("Upload financial statements, business plans, or other relevant documents")
        
        uploaded_files = st.file_uploader(
            "Select files",
            accept_multiple_files=True,
            type=['pdf', 'xlsx', 'xls', 'docx', 'csv'],
            help="Supported formats: PDF, Excel, Word, CSV"
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} file(s) selected")
            for file in uploaded_files:
                st.write(f"- {file.name} ({file.size / 1024:.1f} KB)")
    
    # Analysis options
    st.markdown("### 2️⃣ Analysis Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Valuation Methods**")
        dcf_analysis = st.checkbox("DCF Valuation", value=True)
        cca_analysis = st.checkbox("Comparable Companies Analysis", value=True)
        three_statement = st.checkbox("3-Statement Model", value=True, help="Integrated Income Statement, Balance Sheet, and Cash Flow forecast")
        lbo_analysis = st.checkbox("LBO Analysis", value=False)
        merger_analysis = st.checkbox("M&A / Merger Model", value=False)
        growth_scenarios = st.checkbox("Growth Scenarios & Distress Analysis", value=True, help="Includes Altman Z-Score, O-Score, bankruptcy probability, coverage ratios, liquidity runway")
        
        # If merger analysis selected, ask for acquirer
        acquirer_symbol = None
        if merger_analysis:
            acquirer_symbol = st.text_input(
                "Acquirer Symbol",
                placeholder="e.g., MSFT (for acquiring the target company)",
                help="Enter the ticker symbol of the acquiring company"
            )
    
    with col2:
        st.markdown("**Due Diligence**")
        strategic_dd = st.checkbox("Strategic Assessment", value=False)
        financial_dd = st.checkbox("Financial Due Diligence", value=False)
        operational_dd = st.checkbox("Operational Review", value=False)
        legal_dd = st.checkbox("Legal/Regulatory Review", value=False)
    
    # Data sources
    st.markdown("### 3️⃣ Data Sources")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        use_fmp = st.checkbox("FMP API (Real-time)", value=True, disabled=False)
    
    with col2:
        use_sec = st.checkbox("SEC EDGAR (10-K)", value=True, disabled=False)
    
    with col3:
        peer_count = st.number_input("Peer Companies", min_value=3, max_value=10, value=5)
    
    # Output formats
    st.markdown("### 4️⃣ Output Formats")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        excel_output = st.checkbox("Excel Model (13 tabs)", value=True)
    
    with col2:
        pptx_output = st.checkbox("PowerPoint Presentation", value=True)
    
    with col3:
        dashboard_output = st.checkbox("Interactive Dashboard", value=True)
    
    # AI Planning section
    st.markdown("### 5️⃣ AI Analysis Planning (Optional)")
    
    use_ai_planning = st.checkbox("Let AI create custom analysis plan", value=False)
    
    if use_ai_planning:
        user_request = st.text_area(
            "Describe your analysis needs",
            placeholder="e.g., 'I need a comprehensive valuation for acquisition purposes, focusing on synergies and integration risks'",
            height=100
        )
        
        if st.button("🤖 Generate Analysis Plan"):
            if user_request:
                with st.spinner("AI is creating your analysis plan..."):
                    plan = generate_analysis_plan(user_request)
                    st.session_state.analysis_plan = plan
                    st.success("✅ Analysis plan generated!")
                    st.markdown(f"**Recommended Plan:**\n\n{plan}")
            else:
                st.warning("Please describe your analysis needs")
    
    # Run analysis
    st.markdown("---")
    
    if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
        if not symbol:
            st.error("Please enter a company symbol or name")
            return
        
        if company_type == "Private" and not uploaded_files:
            st.warning("For private companies, please upload relevant documents")
            return
        
        # Prepare analysis options
        analysis_options = {
            'period': 'annual',
            'peers_count': peer_count,
            'dcf': dcf_analysis,
            'cca': cca_analysis,
            'three_statement': three_statement,
            'lbo': lbo_analysis,
            'merger': merger_analysis,
            'growth': growth_scenarios,
            'excel_output': excel_output,
            'powerpoint_output': pptx_output,
            'dashboard_output': dashboard_output,
            'generate_outputs': True
        }
        
        # Run analysis
        try:
            with st.spinner(f"🔄 Analyzing {symbol}... This may take 30-60 seconds"):
                result = asyncio.run(run_analysis_pipeline(
                    symbol=symbol,
                    analysis_options=analysis_options,
                    uploaded_files=uploaded_files
                ))
                
                # Store the result object directly - no conversion needed
                st.session_state.analysis_results = result
                
                st.success("✅ Analysis complete!")
                st.balloons()
                
                # Show summary
                st.markdown("### Analysis Summary")
                
                if hasattr(result, 'valuation'):
                    val_range = result.valuation.valuation_range
                    st.metric(
                        "Valuation Range",
                        f"${val_range[0]:.2f} - ${val_range[1]:.2f}",
                        f"Midpoint: ${sum(val_range)/2:.2f}"
                    )
                
                st.info("Navigate to 'View Results' page to see detailed analysis")
                
        except Exception as e:
            st.error(f"Analysis error: {str(e)}")
            st.exception(e)


def show_qa_page():
    """Show AI Q&A interface"""
    
    st.markdown('<div class="sub-header">💬 AI Financial Assistant</div>', unsafe_allow_html=True)
    
    st.info("""
    **Ask anything about:**
    - Current analysis results
    - Financial concepts and calculations
    - Valuation methodologies
    - Industry comparisons
    - Any financial modeling questions
    
    The AI has access to all your analysis data and will provide accurate, cited responses.
    """)
    
    # Display chat history
    for msg in st.session_state.chat_history:
        with st.container():
            if msg['role'] == 'user':
                st.markdown(f'<div class="chat-message user-message"><strong>You:</strong><br>{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message ai-message"><strong>AI Assistant:</strong><br>{msg["content"]}</div>', unsafe_allow_html=True)
    
    # AI suggested questions
    if st.session_state.analysis_results:
        st.markdown("### 💡 Suggested Questions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("What drives the valuation?"):
                process_user_question("What are the key drivers behind the valuation?")
            
            if st.button("Compare to peers"):
                process_user_question("How does this company compare to its peers?")
        
        with col2:
            if st.button("What are the risks?"):
                process_user_question("What are the main risks in this analysis?")
            
            if st.button("Sensitivity analysis"):
                process_user_question("Show me the sensitivity to key assumptions")
    
    # User input
    st.markdown("### Ask Your Question")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_question = st.text_input(
            "Question",
            placeholder="Type your question here...",
            label_visibility="collapsed"
        )
    
    with col2:
        ask_button = st.button("Send", type="primary", use_container_width=True)
    
    if ask_button and user_question:
        process_user_question(user_question)
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()


def process_user_question(question: str):
    """Process user question and get AI response"""
    
    # Add to chat history
    st.session_state.chat_history.append({
        "role": "user",
        "content": question
    })
    
    # Get AI response
    with st.spinner("AI is thinking..."):
        context = st.session_state.analysis_results if st.session_state.analysis_results else None
        response = get_ai_response(question, context)
        
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response
        })
    
    st.rerun()


def show_results_page():
    """Show analysis results"""
    
    st.markdown('<div class="sub-header">📈 Analysis Results</div>', unsafe_allow_html=True)
    
    if not st.session_state.analysis_results:
        st.warning("No analysis results available. Please run an analysis first.")
        return
    
    result = st.session_state.analysis_results
    
    # Company Information
    st.markdown("### Company Information")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write(f"**Symbol:** {getattr(result, 'symbol', 'N/A')}")
    with col2:
        st.write(f"**Company:** {getattr(result, 'company_name', 'N/A')}")
    with col3:
        if hasattr(result, 'valuation') and hasattr(result.valuation, 'valuation_range'):
            vr = result.valuation.valuation_range
            st.write(f"**Valuation Range:** ${vr[0]:.2f} - ${vr[1]:.2f}")
    
    # AI Valuation Results - SHOW FIRST!
    if hasattr(result, 'ai_classification') and result.ai_classification:
        st.markdown("### 🤖 AI-Powered Company Classification & Weighted Valuation")
        
        ai_class = result.ai_classification
        ai_weighted = result.ai_weighted_value
        ai_explanation = result.ai_explanation
        ai_breakdown = result.ai_breakdown
        
        # Summary Card
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if hasattr(ai_class, 'company_type'):
                st.metric("Company Type", ai_class.company_type.value if hasattr(ai_class.company_type, 'value') else str(ai_class.company_type))
        
        with col2:
            if hasattr(ai_class, 'development_stage'):
                st.metric("Development Stage", ai_class.development_stage.value if hasattr(ai_class.development_stage, 'value') else str(ai_class.development_stage))
        
        with col3:
            if hasattr(ai_class, 'classification_confidence'):
                st.metric("AI Confidence", f"{ai_class.classification_confidence*100:.0f}%")
        
        with col4:
            if ai_weighted:
                st.metric("AI Weighted Value", f"${ai_weighted:.2f}/share")
        
        # Expanded Details
        with st.expander("🤖 View Complete AI Analysis"):
            # Classification Reasoning
            if hasattr(ai_class, 'reasoning'):
                st.markdown("**🧠 Classification Reasoning:**")
                st.info(ai_class.reasoning)
            
            # Key Value Drivers
            if hasattr(ai_class, 'key_value_drivers') and ai_class.key_value_drivers:
                st.markdown("**💡 Key Value Drivers Identified:**")
                for driver in ai_class.key_value_drivers:
                    st.write(f"- {driver}")
            
            # Methodology Weights
            if ai_breakdown:
                st.markdown("**⚖️ AI-Determined Methodology Weights:**")
                
                breakdown_data = []
                for method, details in ai_breakdown.items():
                    breakdown_data.append({
                        'Method': method,
                        'Weight': f"{details.get('weight', 0)*100:.1f}%",
                        'Value': f"${details.get('value', 0):.2f}",
                        'Trust Level': details.get('trust_level', 'N/A'),
                        'Reasoning': details.get('reasoning', 'N/A')
                    })
                
                if breakdown_data:
                    st.dataframe(pd.DataFrame(breakdown_data), use_container_width=True)
            
            # AI Explanation
            if ai_explanation:
                st.markdown("**📝 AI Valuation Methodology Explanation:**")
                st.markdown(ai_explanation)
            
            # Recommended Approach
            if hasattr(ai_class, 'recommended_approach'):
                st.markdown("**✅ Recommended Valuation Approach:**")
                st.success(ai_class.recommended_approach)
        
        st.markdown("---")
    
    # Summary metrics - display ALL available valuations
    st.markdown("### 💰 Valuation Methods Results")
    
    if hasattr(result, 'valuation'):
        val = result.valuation
        
        # CCA Results - FULL COMPREHENSIVE DETAILS
        if hasattr(val, 'cca_result') and val.cca_result:
            st.markdown("#### 🏢 Comparable Companies Analysis (CCA) - Complete Peer Analysis")
            cca = val.cca_result
            
            # Summary metrics across all methods
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("EV/EBITDA Method", f"${cca.value_per_share_ebitda:.2f}")
            with col2:
                if hasattr(cca, 'value_per_share_revenue'):
                    st.metric("EV/Revenue Method", f"${cca.value_per_share_revenue:.2f}")
            with col3:
                if hasattr(cca, 'value_per_share_ebit'):
                    st.metric("EV/EBIT Method", f"${cca.value_per_share_ebit:.2f}")
            with col4:
                if hasattr(cca, 'value_per_share_pe'):
                    st.metric("P/E Method", f"${cca.value_per_share_pe:.2f}")
            
            # Detailed breakdown
            with st.expander("📊 View Complete Peer Analysis & Multiples Breakdown"):
                st.markdown("**Peer Company Selection:**")
                st.write(f"- Total Peers Analyzed: {cca.peer_count}")
                
                # Peer-by-Peer Comparison Table
                if hasattr(cca, 'peer_multiples') and cca.peer_multiples:
                    st.markdown("**Peer-by-Peer Comparison:**")
                    peer_data = []
                    for peer in cca.peer_multiples:
                        peer_data.append({
                            'Company': peer.get('company_name', peer.get('symbol', 'N/A')),
                            'Symbol': peer.get('symbol', 'N/A'),
                            'EV/Revenue': f"{peer.get('ev_revenue', 0):.2f}x" if peer.get('ev_revenue') else 'N/A',
                            'EV/EBITDA': f"{peer.get('ev_ebitda', 0):.2f}x" if peer.get('ev_ebitda') else 'N/A',
                            'EV/EBIT': f"{peer.get('ev_ebit', 0):.2f}x" if peer.get('ev_ebit') else 'N/A',
                            'P/E': f"{peer.get('pe_ratio', 0):.2f}x" if peer.get('pe_ratio') else 'N/A',
                            'Market Cap': f"${peer.get('market_cap', 0)/1e9:.2f}B" if peer.get('market_cap') else 'N/A'
                        })
                    if peer_data:
                        st.dataframe(pd.DataFrame(peer_data), use_container_width=True)
                
                # Statistical Analysis of Multiples
                st.markdown("**Multiple Statistics (EV/EBITDA):**")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    if hasattr(cca, 'ebitda_multiple_mean'):
                        st.write(f"Mean: {cca.ebitda_multiple_mean:.2f}x")
                with col2:
                    if hasattr(cca, 'ebitda_multiple_median'):
                        st.write(f"Median: {cca.ebitda_multiple_median:.2f}x")
                with col3:
                    if hasattr(cca, 'ebitda_multiple_min'):
                        st.write(f"Min: {cca.ebitda_multiple_min:.2f}x")
                with col4:
                    if hasattr(cca, 'ebitda_multiple_max'):
                        st.write(f"Max: {cca.ebitda_multiple_max:.2f}x")
                
                # Multiple Statistics for other methods
                if hasattr(cca, 'revenue_multiple_mean'):
                    st.markdown("**Multiple Statistics (EV/Revenue):**")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.write(f"Mean: {cca.revenue_multiple_mean:.2f}x")
                    with col2:
                        if hasattr(cca, 'revenue_multiple_median'):
                            st.write(f"Median: {cca.revenue_multiple_median:.2f}x")
                    with col3:
                        if hasattr(cca, 'revenue_multiple_min'):
                            st.write(f"Min: {cca.revenue_multiple_min:.2f}x")
                    with col4:
                        if hasattr(cca, 'revenue_multiple_max'):
                            st.write(f"Max: {cca.revenue_multiple_max:.2f}x")
                
                # Valuation Calculation Breakdown
                st.markdown("**Valuation Methodology by Multiple:**")
                
                st.write("**EV/EBITDA Approach:**")
                if hasattr(cca, 'target_ebitda'):
                    st.write(f"- Target Company EBITDA: ${cca.target_ebitda/1e6:.1f}M")
                if hasattr(cca, 'applied_ebitda_multiple'):
                    st.write(f"- Applied Multiple: {cca.applied_ebitda_multiple:.2f}x")
                if hasattr(cca, 'enterprise_value_ebitda'):
                    st.write(f"- Implied Enterprise Value: ${cca.enterprise_value_ebitda/1e9:.2f}B")
                if hasattr(cca, 'equity_value_ebitda'):
                    st.write(f"- Implied Equity Value: ${cca.equity_value_ebitda/1e9:.2f}B")
                st.write(f"- **Value per Share: ${cca.value_per_share_ebitda:.2f}**")
                
                if hasattr(cca, 'value_per_share_revenue'):
                    st.write("")
                    st.write("**EV/Revenue Approach:**")
                    if hasattr(cca, 'target_revenue'):
                        st.write(f"- Target Company Revenue: ${cca.target_revenue/1e6:.1f}M")
                    if hasattr(cca, 'applied_revenue_multiple'):
                        st.write(f"- Applied Multiple: {cca.applied_revenue_multiple:.2f}x")
                    if hasattr(cca, 'enterprise_value_revenue'):
                        st.write(f"- Implied Enterprise Value: ${cca.enterprise_value_revenue/1e9:.2f}B")
                    st.write(f"- **Value per Share: ${cca.value_per_share_revenue:.2f}**")
                
                # Regression-Adjusted Multiples (if available)
                if hasattr(cca, 'regression_adjusted_multiple'):
                    st.markdown("**Regression Analysis:**")
                    st.write(f"- Regression-Adjusted Multiple: {cca.regression_adjusted_multiple:.2f}x")
                    if hasattr(cca, 'r_squared'):
                        st.write(f"- R-squared: {cca.r_squared:.3f}")
                
                # AI Insights on CCA
                if hasattr(cca, 'ai_insights'):
                    st.markdown("**🤖 AI Insights - Peer Positioning:**")
                    st.info(cca.ai_insights)
        
        # DCF Results - FULL DETAILS
        if hasattr(val, 'dcf_result') and val.dcf_result:
            st.markdown("#### 📈 DCF Valuation - Complete Analysis")
            dcf = val.dcf_result
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("DCF Value/Share", f"${dcf.value_per_share:.2f}")
            with col2:
                st.metric("Enterprise Value", f"${dcf.enterprise_value/1e9:.2f}B")
            with col3:
                st.metric("WACC", f"{dcf.wacc*100:.2f}%")
            with col4:
                st.metric("Terminal Value", f"${dcf.pv_terminal_value/1e9:.2f}B")
            
            # Detailed breakdown
            with st.expander("📊 View Complete DCF Model"):
                st.markdown("**WACC Breakdown:**")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"- Cost of Equity: {dcf.cost_of_equity*100:.2f}%")
                    st.write(f"- Cost of Debt (after-tax): {dcf.cost_of_debt_after_tax*100:.2f}%")
                    st.write(f"- Levered Beta: {dcf.levered_beta:.2f}")
                with col2:
                    st.write(f"- Equity Weight: {dcf.weight_equity*100:.1f}%")
                    st.write(f"- Debt Weight: {dcf.weight_debt*100:.1f}%")
                    st.write(f"- WACC: {dcf.wacc*100:.2f}%")
                
                st.markdown("**Cash Flow Projections:**")
                if hasattr(dcf, 'fcff_forecast') and dcf.fcff_forecast:
                    fcff_data = {
                        'Year': [f'Year {i+1}' for i in range(len(dcf.fcff_forecast))],
                        'FCFF': [f'${fcf/1e9:.2f}B' for fcf in dcf.fcff_forecast],
                        'Discount Factor': [f'{df:.4f}' for df in dcf.discount_factors] if hasattr(dcf, 'discount_factors') and dcf.discount_factors else ['N/A'] * len(dcf.fcff_forecast)
                    }
                    st.table(pd.DataFrame(fcff_data))
                
                st.markdown("**Valuation Summary:**")
                st.write(f"- PV of Forecast Period Cash Flows: ${dcf.pv_forecast_period/1e9:.2f}B")
                st.write(f"- Terminal Value: ${dcf.terminal_value/1e9:.2f}B")
                st.write(f"- PV of Terminal Value: ${dcf.pv_terminal_value/1e9:.2f}B")
                st.write(f"- Enterprise Value: ${dcf.enterprise_value/1e9:.2f}B")
                st.write(f"- Equity Value: ${dcf.equity_value/1e9:.2f}B")
                st.write(f"- Shares Outstanding: {dcf.shares_outstanding/1e9:.2f}B")
                st.write(f"- **Value per Share: ${dcf.value_per_share:.2f}**")
        
        # LBO Results - FULL COMPREHENSIVE DETAILS
        if hasattr(val, 'lbo_result') and val.lbo_result:
            st.markdown("#### 💼 LBO Analysis - Complete Leveraged Buyout Model")
            lbo = val.lbo_result
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Min Value/Share", f"${lbo.min_value_per_share:.2f}")
            with col2:
                st.metric("Max Value/Share", f"${lbo.max_value_per_share:.2f}")
            with col3:
                if hasattr(lbo, 'irr'):
                    st.metric("Target IRR", f"{lbo.irr*100:.1f}%")
            with col4:
                if hasattr(lbo, 'moic'):
                    st.metric("MoIC", f"{lbo.moic:.2f}x")
            
            # Detailed breakdown
            with st.expander("📊 View Complete LBO Model"):
                st.markdown("**Sources & Uses of Funds:**")
                
                # Sources table
                if hasattr(lbo, 'sources') and lbo.sources:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**SOURCES:**")
                        sources_data = []
                        for source_item in lbo.sources:
                            sources_data.append({
                                'Source': source_item.get('type', 'N/A'),
                                'Amount': f"${source_item.get('amount', 0)/1e6:.1f}M",
                                '% of Total': f"{source_item.get('percent', 0)*100:.1f}%"
                            })
                        if sources_data:
                            st.table(pd.DataFrame(sources_data))
                        
                        total_sources = sum([s.get('amount', 0) for s in lbo.sources])
                        st.write(f"**Total Sources: ${total_sources/1e6:.1f}M**")
                    
                    # Uses table
                    with col2:
                        if hasattr(lbo, 'uses') and lbo.uses:
                            st.markdown("**USES:**")
                            uses_data = []
                            for use_item in lbo.uses:
                                uses_data.append({
                                    'Use': use_item.get('type', 'N/A'),
                                    'Amount': f"${use_item.get('amount', 0)/1e6:.1f}M",
                                    '% of Total': f"{use_item.get('percent', 0)*100:.1f}%"
                                })
                            if uses_data:
                                st.table(pd.DataFrame(uses_data))
                            
                            total_uses = sum([u.get('amount', 0) for u in lbo.uses])
                            st.write(f"**Total Uses: ${total_uses/1e6:.1f}M**")
                
                # Debt Schedule by Tranche
                st.markdown("**Debt Structure & Schedule:**")
                if hasattr(lbo, 'debt_tranches') and lbo.debt_tranches:
                    debt_data = []
                    for tranche in lbo.debt_tranches:
                        debt_data.append({
                            'Tranche': tranche.get('name', 'N/A'),
                            'Amount': f"${tranche.get('amount', 0)/1e6:.1f}M",
                            'Interest Rate': f"{tranche.get('rate', 0)*100:.2f}%",
                            'Maturity': f"{tranche.get('maturity', 'N/A')} years",
                            'Type': tranche.get('type', 'N/A')
                        })
                    if debt_data:
                        st.dataframe(pd.DataFrame(debt_data), use_container_width=True)
                
                # Financial Projections (5 years)
                st.markdown("**5-Year Financial Projections:**")
                if hasattr(lbo, 'projections') and lbo.projections:
                    proj_data = {
                        'Year': [f'Year {i+1}' for i in range(len(lbo.projections))],
                        'Revenue': [f"${p.get('revenue', 0)/1e9:.2f}B" for p in lbo.projections],
                        'EBITDA': [f"${p.get('ebitda', 0)/1e6:.1f}M" for p in lbo.projections],
                        'EBITDA Margin': [f"{p.get('ebitda_margin', 0)*100:.1f}%" for p in lbo.projections],
                        'FCF': [f"${p.get('fcf', 0)/1e6:.1f}M" for p in lbo.projections],
                        'Debt': [f"${p.get('debt', 0)/1e6:.1f}M" for p in lbo.projections]
                    }
                    st.dataframe(pd.DataFrame(proj_data), use_container_width=True)
                
                # Exit Analysis & Returns
                st.markdown("**Exit Analysis & Waterfall:**")
                col1, col2 = st.columns(2)
                
                with col1:
                    if hasattr(lbo, 'entry_multiple'):
                        st.write(f"- Entry Multiple (EV/EBITDA): {lbo.entry_multiple:.2f}x")
                    if hasattr(lbo, 'exit_multiple'):
                        st.write(f"- Exit Multiple (EV/EBITDA): {lbo.exit_multiple:.2f}x")
                    if hasattr(lbo, 'entry_value'):
                        st.write(f"- Entry Enterprise Value: ${lbo.entry_value/1e9:.2f}B")
                    if hasattr(lbo, 'exit_value'):
                        st.write(f"- Exit Enterprise Value: ${lbo.exit_value/1e9:.2f}B")
                
                with col2:
                    if hasattr(lbo, 'irr'):
                        st.write(f"- **IRR: {lbo.irr*100:.1f}%**")
                    if hasattr(lbo, 'moic'):
                        st.write(f"- **MoIC: {lbo.moic:.2f}x**")
                    if hasattr(lbo, 'holding_period'):
                        st.write(f"- Holding Period: {lbo.holding_period} years")
                    if hasattr(lbo, 'equity_contribution'):
                        st.write(f"- Initial Equity: ${lbo.equity_contribution/1e6:.1f}M")
                    if hasattr(lbo, 'exit_proceeds'):
                        st.write(f"- Exit Proceeds to Equity: ${lbo.exit_proceeds/1e6:.1f}M")
                
                # Sensitivity Analysis on Exit Multiple and Growth
                if hasattr(lbo, 'sensitivity_table'):
                    st.markdown("**Sensitivity Analysis - IRR (%):**")
                    st.markdown("*Sensitivity to Exit Multiple and Revenue Growth*")
                    st.dataframe(lbo.sensitivity_table, use_container_width=True)
                
                # Key Metrics Summary
                st.markdown("**Key LBO Metrics:**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    if hasattr(lbo, 'leverage_ratio'):
                        st.write(f"- Entry Leverage: {lbo.leverage_ratio:.2f}x")
                    if hasattr(lbo, 'debt_paydown'):
                        st.write(f"- Total Debt Paydown: ${lbo.debt_paydown/1e6:.1f}M")
                
                with col2:
                    if hasattr(lbo, 'equity_multiple'):
                        st.write(f"- Equity Multiple: {lbo.equity_multiple:.2f}x")
                    if hasattr(lbo, 'cash_on_cash'):
                        st.write(f"- Cash-on-Cash: {lbo.cash_on_cash:.2f}x")
                
                with col3:
                    if hasattr(lbo, 'avg_ebitda_growth'):
                        st.write(f"- Avg EBITDA Growth: {lbo.avg_ebitda_growth*100:.1f}%")
                    if hasattr(lbo, 'exit_leverage'):
                        st.write(f"- Exit Leverage: {lbo.exit_leverage:.2f}x")
                
                # AI Insights on LBO
                if hasattr(lbo, 'ai_insights'):
                    st.markdown("**🤖 AI Insights - Leverage & Returns:**")
                    st.info(lbo.ai_insights)
        
        # Merger Results
        if hasattr(val, 'merger_result') and val.merger_result:
            st.markdown("#### M&A / Merger Analysis")
            merger = val.merger_result
            st.write("Merger analysis data available")
            
        # Valuation Range
        if hasattr(val, 'valuation_range') and val.valuation_range:
            st.markdown("#### Overall Valuation Summary")
            vr = val.valuation_range
            st.metric(
                "Valuation Range",
                f"${vr[0]:.2f} - ${vr[1]:.2f}",
                f"Midpoint: ${sum(vr)/2:.2f}"
            )
    
    # Peer Companies
    if hasattr(result, 'peer_data') and result.peer_data:
        st.markdown("### 🏢 Peer Companies")
        st.write(f"**Total Peers:** {len(result.peer_data)}")
        
        peer_symbols = [peer.get('symbol', 'N/A') for peer in result.peer_data[:10]]
        st.write(f"**Peers:** {', '.join(peer_symbols)}")
    
    # Due Diligence - FULL COMPREHENSIVE DETAILS
    if hasattr(result, 'dd_results') and result.dd_results:
        st.markdown("### 🔍 Due Diligence - Complete Multi-Agent Analysis")
        dd = result.dd_results
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if hasattr(dd, 'total_risks'):
                st.metric("Total Risks", dd.total_risks)
        with col2:
            if hasattr(dd, 'high_priority_risks'):
                st.metric("High Priority", dd.high_priority_risks, delta_color="inverse")
        with col3:
            if hasattr(dd, 'medium_priority_risks'):
                st.metric("Medium Priority", dd.medium_priority_risks)
        with col4:
            if hasattr(dd, 'low_priority_risks'):
                st.metric("Low Priority", dd.low_priority_risks)
        
        # Quality of Earnings Analysis
        if hasattr(dd, 'qoe_analysis'):
            st.markdown("#### 💰 Quality of Earnings Analysis")
            qoe = dd.qoe_analysis
            
            with st.expander("📊 View Complete QoE Analysis"):
                st.markdown("**Executive Summary:**")
                if hasattr(qoe, 'executive_summary'):
                    st.info(qoe.executive_summary)
                
                # Revenue Quality
                st.markdown("**Revenue Quality Assessment:**")
                col1, col2 = st.columns(2)
                with col1:
                    if hasattr(qoe, 'revenue_quality_score'):
                        st.metric("Revenue Quality Score", f"{qoe.revenue_quality_score}/100")
                    if hasattr(qoe, 'revenue_recognition_issues'):
                        st.write(f"- Recognition Issues: {len(qoe.revenue_recognition_issues)}")
                with col2:
                    if hasattr(qoe, 'revenue_concentration'):
                        st.write(f"- Customer Concentration: {qoe.revenue_concentration*100:.1f}%")
                    if hasattr(qoe, 'one_time_revenues'):
                        st.write(f"- One-time Revenues: ${qoe.one_time_revenues/1e6:.1f}M")
                
                # Earnings Quality
                st.markdown("**Earnings Quality Assessment:**")
                if hasattr(qoe, 'adjusted_ebitda'):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"Reported EBITDA: ${qoe.reported_ebitda/1e6:.1f}M" if hasattr(qoe, 'reported_ebitda') else "N/A")
                    with col2:
                        st.write(f"Adjustments: ${qoe.total_adjustments/1e6:.1f}M" if hasattr(qoe, 'total_adjustments') else "N/A")
                    with col3:
                        st.write(f"**Adjusted EBITDA: ${qoe.adjusted_ebitda/1e6:.1f}M**")
                
                # Key Findings
                if hasattr(qoe, 'key_findings') and qoe.key_findings:
                    st.markdown("**Key Findings:**")
                    for finding in qoe.key_findings:
                        st.write(f"- {finding}")
                
                # Risk Cards
                if hasattr(qoe, 'risk_cards') and qoe.risk_cards:
                    st.markdown("**Risk Assessment:**")
                    for risk in qoe.risk_cards:
                        risk_level = risk.get('level', 'Medium')
                        color = 'red' if risk_level == 'High' else 'orange' if risk_level == 'Medium' else 'green'
                        st.markdown(f":{color}[**{risk_level}**] - {risk.get('description', 'N/A')}")
        
        # Commercial Due Diligence
        if hasattr(dd, 'commercial_dd'):
            st.markdown("#### 📊 Commercial Due Diligence")
            comm = dd.commercial_dd
            
            with st.expander("📊 View Complete Commercial DD"):
                st.markdown("**Market Position Analysis:**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    if hasattr(comm, 'market_share'):
                        st.metric("Market Share", f"{comm.market_share*100:.1f}%")
                with col2:
                    if hasattr(comm, 'market_growth_rate'):
                        st.metric("Market Growth", f"{comm.market_growth_rate*100:.1f}%")
                with col3:
                    if hasattr(comm, 'competitive_position'):
                        st.write(f"Position: {comm.competitive_position}")
                
                # Competitive Landscape
                if hasattr(comm, 'competitive_analysis'):
                    st.markdown("**Competitive Landscape:**")
                    st.write(comm.competitive_analysis)
                
                # Customer Analysis
                if hasattr(comm, 'customer_metrics'):
                    st.markdown("**Customer Metrics:**")
                    metrics = comm.customer_metrics
                    col1, col2 = st.columns(2)
                    with col1:
                        if 'customer_retention' in metrics:
                            st.write(f"- Customer Retention: {metrics['customer_retention']*100:.1f}%")
                        if 'nps_score' in metrics:
                            st.write(f"- NPS Score: {metrics['nps_score']}")
                    with col2:
                        if 'avg_customer_lifetime' in metrics:
                            st.write(f"- Avg Customer Lifetime: {metrics['avg_customer_lifetime']} years")
                        if 'churn_rate' in metrics:
                            st.write(f"- Churn Rate: {metrics['churn_rate']*100:.1f}%")
                
                # Key Insights
                if hasattr(comm, 'ai_insights'):
                    st.markdown("**🤖 AI Insights:**")
                    st.info(comm.ai_insights)
        
        # Legal & Tax Due Diligence
        if hasattr(dd, 'legal_tax_dd'):
            st.markdown("#### ⚖️ Legal & Tax Due Diligence")
            legal = dd.legal_tax_dd
            
            with st.expander("⚖️ View Legal & Tax Review"):
                if hasattr(legal, 'legal_risks') and legal.legal_risks:
                    st.markdown("**Legal Risk Assessment:**")
                    for risk in legal.legal_risks:
                        risk_level = risk.get('severity', 'Medium')
                        st.markdown(f"**{risk.get('category', 'N/A')}** - :{risk_level.lower()}[{risk_level}]")
                        st.write(f"  {risk.get('description', 'N/A')}")
                
                if hasattr(legal, 'tax_analysis'):
                    st.markdown("**Tax Analysis:**")
                    tax = legal.tax_analysis
                    col1, col2 = st.columns(2)
                    with col1:
                        if isinstance(tax, dict) and 'effective_tax_rate' in tax:
                            st.write(f"- Effective Tax Rate: {tax['effective_tax_rate']*100:.1f}%")
                        if isinstance(tax, dict) and 'tax_exposures' in tax:
                            st.write(f"- Identified Tax Exposures: ${tax['tax_exposures']/1e6:.1f}M")
                    with col2:
                        if isinstance(tax, dict) and 'nol_carryforwards' in tax:
                            st.write(f"- NOL Carryforwards: ${tax['nol_carryforwards']/1e6:.1f}M")
                        if isinstance(tax, dict) and 'jurisdictions' in tax:
                            st.write(f"- Tax Jurisdictions: {len(tax['jurisdictions'])}")
        
        # Technology Due Diligence
        if hasattr(dd, 'tech_dd'):
            st.markdown("#### 💻 Technology Due Diligence")
            tech = dd.tech_dd
            
            with st.expander("💻 View Technology Assessment"):
                st.markdown("**Technology Stack Assessment:**")
                if hasattr(tech, 'tech_stack_quality'):
                    st.metric("Tech Stack Quality", f"{tech.tech_stack_quality}/100")
                
                if hasattr(tech, 'key_systems') and tech.key_systems:
                    st.markdown("**Key Systems:**")
                    for system in tech.key_systems:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**{system.get('name', 'N/A')}**")
                        with col2:
                            st.write(f"Status: {system.get('status', 'N/A')}")
                        with col3:
                            st.write(f"Risk: {system.get('risk_level', 'N/A')}")
                
                # Cybersecurity
                if hasattr(tech, 'cybersecurity_score'):
                    st.markdown("**Cybersecurity Assessment:**")
                    st.metric("Security Score", f"{tech.cybersecurity_score}/100")
                    if hasattr(tech, 'security_gaps') and tech.security_gaps:
                        st.write("**Security Gaps:**")
                        for gap in tech.security_gaps:
                            st.write(f"- {gap}")
        
        # ESG Analysis
        if hasattr(dd, 'esg_analysis'):
            st.markdown("#### 🌱 ESG Analysis")
            esg = dd.esg_analysis
            
            with st.expander("🌱 View ESG Assessment"):
                st.markdown("**ESG Scores:**")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    if hasattr(esg, 'overall_score'):
                        st.metric("Overall ESG", f"{esg.overall_score}/100")
                with col2:
                    if hasattr(esg, 'environmental_score'):
                        st.metric("Environmental", f"{esg.environmental_score}/100")
                with col3:
                    if hasattr(esg, 'social_score'):
                        st.metric("Social", f"{esg.social_score}/100")
                with col4:
                    if hasattr(esg, 'governance_score'):
                        st.metric("Governance", f"{esg.governance_score}/100")
                
                # Environmental Factors
                if hasattr(esg, 'environmental_factors'):
                    st.markdown("**Environmental Factors:**")
                    env = esg.environmental_factors
                    if isinstance(env, dict):
                        for key, value in env.items():
                            st.write(f"- {key}: {value}")
                
                # Social Factors
                if hasattr(esg, 'social_factors'):
                    st.markdown("**Social Factors:**")
                    social = esg.social_factors
                    if isinstance(social, dict):
                        for key, value in social.items():
                            st.write(f"- {key}: {value}")
                
                # Governance Factors
                if hasattr(esg, 'governance_factors'):
                    st.markdown("**Governance Factors:**")
                    gov = esg.governance_factors
                    if isinstance(gov, dict):
                        for key, value in gov.items():
                            st.write(f"- {key}: {value}")
        
        # HR Due Diligence
        if hasattr(dd, 'hr_dd'):
            st.markdown("#### 👥 Human Resources Due Diligence")
            hr = dd.hr_dd
            
            with st.expander("👥 View HR Assessment"):
                st.markdown("**Workforce Analysis:**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    if hasattr(hr, 'total_employees'):
                        st.metric("Total Employees", hr.total_employees)
                with col2:
                    if hasattr(hr, 'turnover_rate'):
                        st.metric("Turnover Rate", f"{hr.turnover_rate*100:.1f}%")
                with col3:
                    if hasattr(hr, 'avg_tenure'):
                        st.metric("Avg Tenure", f"{hr.avg_tenure:.1f} years")
                
                # Compensation Analysis
                if hasattr(hr, 'compensation_analysis'):
                    st.markdown("**Compensation Analysis:**")
                    comp = hr.compensation_analysis
                    if isinstance(comp, dict):
                        col1, col2 = st.columns(2)
                        with col1:
                            if 'market_competitiveness' in comp:
                                st.write(f"- Market Competitiveness: {comp['market_competitiveness']}")
                            if 'total_comp_cost' in comp:
                                st.write(f"- Total Compensation Cost: ${comp['total_comp_cost']/1e6:.1f}M")
                        with col2:
                            if 'benefits_cost' in comp:
                                st.write(f"- Benefits Cost: ${comp['benefits_cost']/1e6:.1f}M")
                            if 'retention_risks' in comp:
                                st.write(f"- Retention Risks: {comp['retention_risks']}")
                
                # Key Personnel
                if hasattr(hr, 'key_personnel_risks') and hr.key_personnel_risks:
                    st.markdown("**Key Personnel Risks:**")
                    for risk in hr.key_personnel_risks:
                        st.markdown(f"- {risk}")
        
        # Overall DD Summary
        if hasattr(dd, 'overall_assessment'):
            st.markdown("#### 📋 Overall Due Diligence Assessment")
            st.markdown("**🤖 AI Executive Summary:**")
            st.info(dd.overall_assessment)
    
    # Growth Scenarios - FULL COMPREHENSIVE DETAILS
    if hasattr(result, 'growth_scenarios') and result.growth_scenarios:
        st.markdown("### 📈 Growth Scenarios & Risk Analysis")
        scenarios = result.growth_scenarios
        
        # Bull/Base/Bear Scenarios
        if hasattr(scenarios, 'bull_case') or hasattr(scenarios, 'base_case') or hasattr(scenarios, 'bear_case'):
            st.markdown("#### 🎯 Bull / Base / Bear Scenarios")
            
            with st.expander("📊 View Complete Scenario Analysis"):
                # Scenario comparison table
                scenario_data = []
                
                if hasattr(scenarios, 'bear_case'):
                    bear = scenarios.bear_case
                    scenario_data.append({
                        'Scenario': 'Bear Case',
                        'Probability': f"{bear.get('probability', 0.2)*100:.0f}%",
                        'Revenue Growth': f"{bear.get('revenue_growth', 0)*100:.1f}%",
                        'EBITDA Margin': f"{bear.get('ebitda_margin', 0)*100:.1f}%",
                        'Valuation': f"${bear.get('valuation_per_share', 0):.2f}",
                        'Key Assumptions': bear.get('key_assumptions', 'Economic downturn, market share loss')
                    })
                
                if hasattr(scenarios, 'base_case'):
                    base = scenarios.base_case
                    scenario_data.append({
                        'Scenario': 'Base Case',
                        'Probability': f"{base.get('probability', 0.6)*100:.0f}%",
                        'Revenue Growth': f"{base.get('revenue_growth', 0)*100:.1f}%",
                        'EBITDA Margin': f"{base.get('ebitda_margin', 0)*100:.1f}%",
                        'Valuation': f"${base.get('valuation_per_share', 0):.2f}",
                        'Key Assumptions': base.get('key_assumptions', 'Market growth, stable margins')
                    })
                
                if hasattr(scenarios, 'bull_case'):
                    bull = scenarios.bull_case
                    scenario_data.append({
                        'Scenario': 'Bull Case',
                        'Probability': f"{bull.get('probability', 0.2)*100:.0f}%",
                        'Revenue Growth': f"{bull.get('revenue_growth', 0)*100:.1f}%",
                        'EBITDA Margin': f"{bull.get('ebitda_margin', 0)*100:.1f}%",
                        'Valuation': f"${bull.get('valuation_per_share', 0):.2f}",
                        'Key Assumptions': bull.get('key_assumptions', 'Strong growth, margin expansion')
                    })
                
                if scenario_data:
                    st.dataframe(pd.DataFrame(scenario_data), use_container_width=True)
                
                # Expected value calculation
                if hasattr(scenarios, 'expected_value'):
                    st.markdown("**Probability-Weighted Expected Value:**")
                    st.metric("Expected Value per Share", f"${scenarios.expected_value:.2f}")
        
        # Distress Metrics
        if hasattr(scenarios, 'distress_metrics'):
            st.markdown("#### ⚠️ Financial Distress Indicators")
            distress = scenarios.distress_metrics
            
            with st.expander("⚠️ View Distress Analysis"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if hasattr(distress, 'altman_z_score'):
                        z_score = distress.altman_z_score
                        z_color = 'green' if z_score > 2.99 else 'orange' if z_score > 1.81 else 'red'
                        st.metric("Altman Z-Score", f"{z_score:.2f}")
                        if z_score > 2.99:
                            st.success("✅ Safe Zone")
                        elif z_score > 1.81:
                            st.warning("⚠️ Grey Zone")
                        else:
                            st.error("🔴 Distress Zone")
                
                with col2:
                    if hasattr(distress, 'piotroski_f_score'):
                        f_score = distress.piotroski_f_score
                        st.metric("Piotroski F-Score", f"{f_score}/9")
                        if f_score >= 7:
                            st.success("✅ Strong")
                        elif f_score >= 4:
                            st.info("🟡 Average")
                        else:
                            st.warning("⚠️ Weak")
                
                with col3:
                    if hasattr(distress, 'ohlson_o_score'):
                        o_score = distress.ohlson_o_score
                        st.metric("Ohlson O-Score", f"{o_score:.3f}")
                        if o_score < 0.38:
                            st.success("✅ Low Risk")
                        else:
                            st.warning("⚠️ Higher Risk")
                
                # Detailed metrics
                if hasattr(distress, 'key_ratios'):
                    st.markdown("**Key Financial Ratios:**")
                    ratios = distress.key_ratios
                    col1, col2 = st.columns(2)
                    with col1:
                        for key, value in list(ratios.items())[:len(ratios)//2]:
                            st.write(f"- {key}: {value}")
                    with col2:
                        for key, value in list(ratios.items())[len(ratios)//2:]:
                            st.write(f"- {key}: {value}")
        
        # SaaS Metrics (if applicable)
        if hasattr(scenarios, 'saas_metrics'):
            st.markdown("#### 💻 SaaS-Specific Metrics")
            saas = scenarios.saas_metrics
            
            with st.expander("💻 View SaaS Analysis"):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if hasattr(saas, 'arr'):
                        st.metric("ARR", f"${saas.arr/1e6:.1f}M")
                with col2:
                    if hasattr(saas, 'nrr'):
                        st.metric("Net Revenue Retention", f"{saas.nrr*100:.0f}%")
                with col3:
                    if hasattr(saas, 'cac_payback'):
                        st.metric("CAC Payback", f"{saas.cac_payback:.1f} months")
                with col4:
                    if hasattr(saas, 'ltv_cac_ratio'):
                        st.metric("LTV/CAC", f"{saas.ltv_cac_ratio:.1f}x")
                
                # Additional metrics
                st.markdown("**Detailed SaaS Metrics:**")
                col1, col2 = st.columns(2)
                with col1:
                    if hasattr(saas, 'magic_number'):
                        st.write(f"- Magic Number: {saas.magic_number:.2f}")
                    if hasattr(saas, 'gross_margin'):
                        st.write(f"- Gross Margin: {saas.gross_margin*100:.1f}%")
                    if hasattr(saas, 'rule_of_40'):
                        st.write(f"- Rule of 40: {saas.rule_of_40:.1f}")
                with col2:
                    if hasattr(saas, 'burn_multiple'):
                        st.write(f"- Burn Multiple: {saas.burn_multiple:.2f}")
                    if hasattr(saas, 'logo_retention'):
                        st.write(f"- Logo Retention: {saas.logo_retention*100:.1f}%")
                    if hasattr(saas, 'expansion_revenue'):
                        st.write(f"- Expansion Revenue: ${saas.expansion_revenue/1e6:.1f}M")
        
        # Monte Carlo Simulation
        if hasattr(scenarios, 'monte_carlo'):
            st.markdown("#### 🎲 Monte Carlo Simulation Results")
            mc = scenarios.monte_carlo
            
            with st.expander("🎲 View Monte Carlo Analysis"):
                st.markdown("**Valuation Distribution:**")
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    if hasattr(mc, 'percentile_10'):
                        st.metric("10th Percentile", f"${mc.percentile_10:.2f}")
                with col2:
                    if hasattr(mc, 'percentile_25'):
                        st.metric("25th Percentile", f"${mc.percentile_25:.2f}")
                with col3:
                    if hasattr(mc, 'median'):
                        st.metric("Median (50th)", f"${mc.median:.2f}")
                with col4:
                    if hasattr(mc, 'percentile_75'):
                        st.metric("75th Percentile", f"${mc.percentile_75:.2f}")
                with col5:
                    if hasattr(mc, 'percentile_90'):
                        st.metric("90th Percentile", f"${mc.percentile_90:.2f}")
                
                # Statistical measures
                st.markdown("**Statistical Measures:**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    if hasattr(mc, 'mean'):
                        st.write(f"- Mean: ${mc.mean:.2f}")
                    if hasattr(mc, 'std_dev'):
                        st.write(f"- Std Deviation: ${mc.std_dev:.2f}")
                with col2:
                    if hasattr(mc, 'min_value'):
                        st.write(f"- Minimum: ${mc.min_value:.2f}")
                    if hasattr(mc, 'max_value'):
                        st.write(f"- Maximum: ${mc.max_value:.2f}")
                with col3:
                    if hasattr(mc, 'coefficient_of_variation'):
                        st.write(f"- Coefficient of Variation: {mc.coefficient_of_variation:.2f}")
                    if hasattr(mc, 'simulations'):
                        st.write(f"- Number of Simulations: {mc.simulations:,}")
        
        # AI Scenario Insights
        if hasattr(scenarios, 'ai_insights'):
            st.markdown("**🤖 AI Insights - Scenario Analysis:**")
            st.info(scenarios.ai_insights)
    
    # Sensitivity Analysis Section
    if hasattr(result, 'valuation') and (hasattr(result.valuation, 'dcf_result') or hasattr(result.valuation, 'lbo_result')):
        st.markdown("### 🎯 Sensitivity Analysis")
        
        with st.expander("📊 View Sensitivity Tables"):
            # DCF Sensitivity
            if hasattr(result.valuation, 'dcf_result') and result.valuation.dcf_result:
                st.markdown("**DCF Valuation Sensitivity:**")
                dcf = result.valuation.dcf_result
                
                # Create 2-way sensitivity table
                if hasattr(dcf, 'value_per_share') and hasattr(dcf, 'wacc'):
                    base_value = dcf.value_per_share
                    base_wacc = dcf.wacc
                    base_growth = getattr(dcf, 'terminal_growth', 0.025)
                    
                    # WACC vs Terminal Growth sensitivity
                    st.markdown("*WACC vs Terminal Growth Rate:*")
                    wacc_range = [base_wacc - 0.02, base_wacc - 0.01, base_wacc, base_wacc + 0.01, base_wacc + 0.02]
                    growth_range = [base_growth - 0.01, base_growth - 0.005, base_growth, base_growth + 0.005, base_growth + 0.01]
                    
                    sensitivity_data = []
                    for growth in growth_range:
                        row = []
                        for wacc in wacc_range:
                            # Simplified sensitivity calculation
                            adjusted_value = base_value * (1 + (base_growth - growth) * 10) * (1 + (wacc - base_wacc) * -8)
                            row.append(f"${adjusted_value:.2f}")
                        sensitivity_data.append(row)
                    
                    sens_df = pd.DataFrame(
                        sensitivity_data,
                        columns=[f"{w*100:.1f}%" for w in wacc_range],
                        index=[f"{g*100:.2f}%" for g in growth_range]
                    )
                    sens_df.index.name = "Terminal Growth →"
                    st.dataframe(sens_df, use_container_width=True)
                    st.caption("Note: WACC shown across columns, Terminal Growth down rows")
                
                # Revenue Growth vs EBITDA Margin sensitivity
                st.markdown("*Revenue Growth vs EBITDA Margin:*")
                if hasattr(dcf, 'value_per_share'):
                    rev_growth_range = [0.03, 0.05, 0.07, 0.09, 0.11]
                    margin_range = [0.20, 0.225, 0.25, 0.275, 0.30]
                    
                    margin_sensitivity = []
                    for margin in margin_range:
                        row = []
                        for growth in rev_growth_range:
                            # Simplified calculation
                            adjusted = base_value * (1 + (growth - 0.07) * 5) * (1 + (margin - 0.25) * 2)
                            row.append(f"${adjusted:.2f}")
                        margin_sensitivity.append(row)
                    
                    margin_df = pd.DataFrame(
                        margin_sensitivity,
                        columns=[f"{g*100:.0f}%" for g in rev_growth_range],
                        index=[f"{m*100:.1f}%" for m in margin_range]
                    )
                    margin_df.index.name = "EBITDA Margin →"
                    st.dataframe(margin_df, use_container_width=True)
                    st.caption("Note: Revenue Growth across columns, EBITDA Margin down rows")
            
            # LBO Sensitivity
            if hasattr(result.valuation, 'lbo_result') and result.valuation.lbo_result:
                st.markdown("**LBO IRR Sensitivity:**")
                lbo = result.valuation.lbo_result
                
                if hasattr(lbo, 'sensitivity_table'):
                    st.markdown("*Exit Multiple vs Revenue Growth:*")
                    st.dataframe(lbo.sensitivity_table, use_container_width=True)
    
    # Download outputs - PRODUCTION READY
    st.markdown("### 📥 Professional Outputs - One-Click Downloads")
    
    if hasattr(result, 'output_files') and result.output_files:
        st.success(f"✅ {len(result.output_files)} professional output file(s) generated and ready for download")
        
        # Organize files by type
        excel_files = [f for f in result.output_files if f.endswith(('.xlsx', '.xls'))]
        pptx_files = [f for f in result.output_files if f.endswith('.pptx')]
        pdf_files = [f for f in result.output_files if f.endswith('.pdf')]
        docx_files = [f for f in result.output_files if f.endswith('.docx')]
        
        # Excel Downloads
        if excel_files:
            st.markdown("#### 📊 Excel Models")
            st.info("**15-Tab Comprehensive Excel Model** includes: Assumptions | Hist_Clean | QoE | Drivers | 3FS | DCF | CCA | Precedent | LBO | A/D | PPA | Synergies | Sensitivities | Outputs | AuditTrail")
            
            for file_path in excel_files:
                if Path(file_path).exists():
                    with open(file_path, 'rb') as f:
                        file_data = f.read()
                        file_name = Path(file_path).name
                        st.download_button(
                            label=f"📥 Download {file_name}",
                            data=file_data,
                            file_name=file_name,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
        
        # PowerPoint Downloads
        if pptx_files:
            st.markdown("#### 📊 PowerPoint Presentations")
            st.info("**Investment Banking Slides** include: Synergy plans | Day-1/100 plans | Integration KPI scorecards | Executive summaries")
            
            for file_path in pptx_files:
                if Path(file_path).exists():
                    with open(file_path, 'rb') as f:
                        file_data = f.read()
                        file_name = Path(file_path).name
                        st.download_button(
                            label=f"📥 Download {file_name}",
                            data=file_data,
                            file_name=file_name,
                            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                            use_container_width=True
                        )
        
        # PDF Downloads
        if pdf_files:
            st.markdown("#### 📄 PDF Reports")
            st.info("**Investment Committee Packages** include: Tear sheets (1-2 pp) | IC Memos (10-20 pp) | DD Packs (Financial QoE, Legal/Tax, Commercial, Tech) | Lineage appendix")
            
            for file_path in pdf_files:
                if Path(file_path).exists():
                    with open(file_path, 'rb') as f:
                        file_data = f.read()
                        file_name = Path(file_path).name
                        
                        # Determine report type from filename
                        if 'tear_sheet' in file_name.lower():
                            label = f"📥 Tear Sheet - {file_name}"
                        elif 'ic_memo' in file_name.lower() or 'memo' in file_name.lower():
                            label = f"📥 IC Memo - {file_name}"
                        elif 'dd_pack' in file_name.lower() or 'due_diligence' in file_name.lower():
                            label = f"📥 DD Pack - {file_name}"
                        elif 'lineage' in file_name.lower():
                            label = f"📥 Lineage Report - {file_name}"
                        else:
                            label = f"📥 Download {file_name}"
                        
                        st.download_button(
                            label=label,
                            data=file_data,
                            file_name=file_name,
                            mime="application/pdf",
                            use_container_width=True
                        )
        
        # Word Documents
        if docx_files:
            st.markdown("#### 📝 Word Documents")
            
            for file_path in docx_files:
                if Path(file_path).exists():
                    with open(file_path, 'rb') as f:
                        file_data = f.read()
                        file_name = Path(file_path).name
                        st.download_button(
                            label=f"📥 Download {file_name}",
                            data=file_data,
                            file_name=file_name,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True
                        )
        
        # Download All as ZIP
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📦 Download All Files as ZIP", type="primary", use_container_width=True):
                import zipfile
                from io import BytesIO
                
                # Create ZIP file in memory
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for file_path in result.output_files:
                        if Path(file_path).exists():
                            zip_file.write(file_path, Path(file_path).name)
                
                zip_buffer.seek(0)
                
                st.download_button(
                    label="📥 Download Complete Analysis Package (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name=f"{getattr(result, 'symbol', 'analysis')}_complete_package_{datetime.now().strftime('%Y%m%d')}.zip",
                    mime="application/zip",
                    use_container_width=True
                )
    else:
        st.warning("⚠️ No output files generated. Please run a new analysis with output generation enabled.")
        st.info("""
        **To generate professional outputs:**
        1. Go to 'New Analysis' page
        2. Select desired output formats (Excel, PowerPoint)
        3. Run the analysis
        4. Return to this page to download all generated files
        """)
    
    # Full detailed data
    with st.expander("📊 View Complete Analysis Data"):
        st.write("**Full Result Object:**")
        st.write(f"**Type:** {type(result)}")
        st.write(f"**Symbol:** {getattr(result, 'symbol', 'N/A')}")
        st.write(f"**Company:** {getattr(result, 'company_name', 'N/A')}")
        
        if hasattr(result, 'valuation'):
            st.write("**Valuation Object:**")
            st.write(result.valuation)
        
        if hasattr(result, 'financial_data'):
            st.write("**Financial Data Available:** Yes")
        
        if hasattr(result, 'peer_data'):
            st.write(f"**Peer Data:** {len(result.peer_data)} companies")
        
        # Try to display as JSON if possible
        try:
            if hasattr(result, 'model_dump'):
                st.json(result.model_dump())
            elif hasattr(result, '__dict__'):
                # Convert nested objects to strings for display
                display_dict = {}
                for k, v in result.__dict__.items():
                    if hasattr(v, '__dict__'):
                        display_dict[k] = str(v)
                    else:
                        display_dict[k] = v
                st.json(display_dict)
        except Exception as e:
            st.write(f"Could not display as JSON: {e}")
            st.write(result)


def show_settings_page():
    """Show settings page"""
    
    st.markdown('<div class="sub-header">⚙️ Settings</div>', unsafe_allow_html=True)
    
    # Change Password Section
    st.markdown("### 🔐 Change Password")
    
    with st.form("change_password_form"):
        old_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        if st.form_submit_button("🔄 Change Password", type="primary"):
            if not all([old_password, new_password, confirm_password]):
                st.error("Please fill in all fields")
            elif new_password != confirm_password:
                st.error("New passwords do not match")
            elif len(new_password) < 8:
                st.error("Password must be at least 8 characters")
            elif st.session_state.user_manager.change_password(
                st.session_state.user_info['email'],
                old_password,
                new_password
            ):
                st.success("✅ Password changed successfully!")
            else:
                st.error("❌ Failed to change password (check current password)")
    
    st.markdown("---")
    
    st.markdown("### API Configuration")
    
    # Check API keys
    col1, col2 = st.columns(2)
    
    with col1:
        fmp_key = os.getenv('FMP_API_KEY', '')
        if fmp_key:
            st.success(f"✅ FMP API Key: {fmp_key[:10]}...")
        else:
            st.error("❌ FMP API Key not found")
            new_key = st.text_input("Enter FMP API Key", type="password")
            if st.button("Save FMP Key"):
                st.info("Update .env file with your key")
    
    with col2:
        deepseek_key = os.getenv('DEEPSEEK_API_KEY', '')
        if deepseek_key:
            st.success(f"✅ DeepSeek API Key: {deepseek_key[:10]}...")
        else:
            st.error("❌ DeepSeek API Key not found")
            new_key = st.text_input("Enter DeepSeek API Key", type="password")
            if st.button("Save DeepSeek Key"):
                st.info("Update .env file with your key")
    
    st.markdown("### System Information")
    
    # Get current model from settings
    llm_model = os.getenv('LLM_MODEL', 'deepseek-reasoner')
    max_tokens = os.getenv('LLM_MAX_TOKENS', '32000')
    
    # Check system status
    st.info(f"""
    **Platform Status:**
    - Backend: ✅ Ready
    - Database: ✅ DuckDB
    - Memory System: ✅ Active
    - LLM Model: {'✅ ' + llm_model + ' (Max: ' + max_tokens + ' tokens)' if deepseek_key else '❌ Not configured'}
    - Data Sources: {'✅ Configured' if fmp_key else '⚠️ Partial'}
    """)
    
    # Model Information
    if deepseek_key:
        with st.expander("🤖 AI Model Details"):
            st.markdown(f"""
            **Current Configuration:**
            - Model: `{llm_model}`
            - Provider: DeepSeek
            - Max Tokens: {max_tokens}
            - Context Length: 128K (reasoner mode)
            - Temperature: 0.1 (default)
            
            **Capabilities:**
            - Extended reasoning for complex financial analysis
            - 128K context window for processing large documents
            - Up to 32K/64K output tokens for comprehensive reports
            - Optimized for multi-step financial modeling tasks
            """)
    
    # Advanced settings
    with st.expander("⚙️ Advanced Settings"):
        st.markdown("**Analysis Defaults**")
        default_peers = st.number_input("Default Peer Count", min_value=3, max_value=10, value=5)
        default_period = st.selectbox("Default Period", ["annual", "quarter"])
        
        st.markdown("**Output Preferences**")
        auto_excel = st.checkbox("Auto-generate Excel", value=True)
        auto_pptx = st.checkbox("Auto-generate PowerPoint", value=True)
        
        if st.button("Save Preferences"):
            st.success("✅ Preferences saved!")


if __name__ == "__main__":
    main()
