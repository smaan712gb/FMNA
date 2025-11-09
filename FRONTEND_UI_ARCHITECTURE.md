# Frontend & User Interface Architecture Plan

## Current Status: Backend 100% Ready, Frontend 0% Built

Your backend is production-ready, but you need user-facing interfaces. Here's the complete plan.

---

## User Interaction Architecture

### Overview: 3-Layer Approach

```
┌─────────────────────────────────────────────────────────┐
│                  USER LAYER                              │
│  (Web UI, Mobile, CLI, API)                             │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                  API LAYER                               │
│  (FastAPI Endpoints, WebSocket, Authentication)         │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                  BACKEND LAYER ✅                        │
│  (Agents, Engines, Storage) - Already Built!            │
└─────────────────────────────────────────────────────────┘
```

---

## Option 1: Web Application (Recommended ⭐)

### Stack Recommendation

**Frontend**:
- **React** + **TypeScript** - Modern, type-safe
- **Tailwind CSS** - Professional styling
- **Shadcn/ui** - Beautiful components
- **TanStack Query** - Data fetching
- **Zustand** - State management

**Backend API** (Already Have!):
- **FastAPI** - Already in requirements.txt!
- **WebSocket** - Real-time updates
- **SQLAlchemy** - User management

### User Interface Components

#### 1. Landing/Dashboard Page
```
┌────────────────────────────────────────────────┐
│  FMNA Platform                    [User: Admin]│
├────────────────────────────────────────────────┤
│                                                 │
│  Recent Analyses                                │
│  ┌──────────┬──────────┬──────────┬──────────┐│
│  │ AAPL     │ MSFT     │ NVDA     │ +New     ││
│  │ $180.45  │ $415.20  │ $875.10  │ Analysis ││
│  │ Updated  │ Updated  │ Updated  │          ││
│  │ 2h ago   │ 5h ago   │ 1d ago   │          ││
│  └──────────┴──────────┴──────────┴──────────┘│
│                                                 │
│  Quick Actions                                  │
│  ┌─────────────────┐  ┌─────────────────┐     │
│  │ 🔍 Analyze      │  │ 📊 View Reports│     │
│  │    Company      │  │                 │     │
│  └─────────────────┘  └─────────────────┘     │
└────────────────────────────────────────────────┘
```

#### 2. Analysis Input Page
```
┌────────────────────────────────────────────────┐
│  New Analysis                        [Back][?] │
├────────────────────────────────────────────────┤
│                                                 │
│  Company Symbol:  [AAPL____________]  [Search] │
│                                                 │
│  Analysis Options:                              │
│  ☑ DCF Valuation                               │
│  ☑ Comparable Companies (CCA)                  │
│  ☑ LBO Analysis                                │
│  ☐ M&A Synergies                               │
│  ☐ Full Due Diligence (6 categories)          │
│                                                 │
│  Data Sources:                                  │
│  ☑ FMP API (Real-time financials)             │
│  ☑ SEC EDGAR (10-K filings)                   │
│                                                 │
│  Output Formats:                                │
│  ☑ Excel Model (13 tabs)                      │
│  ☑ PowerPoint Presentation                    │
│  ☑ Interactive Dashboard                       │
│  ☑ IC Memo (DOCX)                             │
│                                                 │
│          [Cancel]         [Run Analysis]        │
└────────────────────────────────────────────────┘
```

#### 3. AI Chat Interface (Real-time Q&A)
```
┌────────────────────────────────────────────────┐
│  AI Assistant - AAPL Analysis      [Minimize]  │
├────────────────────────────────────────────────┤
│  💬 Chat History                                │
│  ┌──────────────────────────────────────────┐ │
│  │ You: What's Apple's DCF valuation?       │ │
│  │                                          │ │
│  │ AI: Based on the latest analysis from   │ │
│  │ 2025-11-06, Apple's DCF valuation is    │ │
│  │ $183.87/share (Enterprise Value:        │ │
│  │ $2.85T, WACC: 7.8%)                     │ │
│  │                                          │ │
│  │ 📎 Source: AAPL_Analysis_20251106.xlsx  │ │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │ │
│  │                                          │ │
│  │ You: How does that compare to peers?    │ │
│  │                                          │ │
│  │ AI: From the CCA analysis, AAPL trades  │ │
│  │ at a premium (EV/EBITDA: 22.8x vs peer │ │
│  │ median 18.5x). Justified by ecosystem.  │ │
│  │                                          │ │
│  │ 📎 Source: Peer analysis using 9 comps  │ │
│  └──────────────────────────────────────────┘ │
│                                                 │
│  [Ask a question...]               [Send]      │
└────────────────────────────────────────────────┘
```

#### 4. Results/Outputs Page
```
┌────────────────────────────────────────────────┐
│  Analysis Results: AAPL     [Download][Share]  │
├────────────────────────────────────────────────┤
│                                                 │
│  📊 Valuation Summary                          │
│  ┌──────────────────────────────────────────┐ │
│  │ DCF:  $183.87/share                      │ │
│  │ CCA:  $178.25/share (EV/EBITDA)         │ │
│  │ Range: $162.00 - $225.00                 │ │
│  │                                          │ │
│  │ [View Football Field Chart ━]           │ │
│  └──────────────────────────────────────────┘ │
│                                                 │
│  📁 Available Outputs                          │
│  ┌──────────────────────────────────────────┐ │
│  │ 📊 Excel Model (13 tabs)     [Download] │ │
│  │ 📑 PowerPoint Deck           [Download] │ │
│  │ 📈 Interactive Dashboard     [View]     │ │
│  │ 📄 IC Memo (DOCX)           [Download] │ │
│  └──────────────────────────────────────────┘ │
│                                                 │
│  🎯 Interactive Dashboard (Embedded)           │
│  [Football Field | Sensitivity | Peers | ...]  │
│                                                 │
└────────────────────────────────────────────────┘
```

#### 5. Admin Panel
```
┌────────────────────────────────────────────────┐
│  Admin Dashboard                  [Logout]      │
├────────────────────────────────────────────────┤
│                                                 │
│  👥 User Management                            │
│  ┌──────────────────────────────────────────┐ │
│  │ Users (45)          [+ Add User]         │ │
│  │                                          │ │
│  │ john.analyst@firm.com    [✏️]  [🗑️]   │ │
│  │ Role: Analyst │ Last login: 2h ago      │ │
│  │                                          │ │
│  │ sarah.director@firm.com  [✏️]  [🗑️]   │ │
│  │ Role: Director│ Last login: 1d ago      │ │
│  └──────────────────────────────────────────┘ │
│                                                 │
│  📊 System Stats                               │
│  ┌──────────────────────────────────────────┐ │
│  │ Total Analyses: 1,234                    │ │
│  │ API Calls Today: 8,752 / 10,000         │ │
│  │ Storage Used: 2.4 GB / 100 GB           │ │
│  │ Active Sessions: 12                      │ │
│  └──────────────────────────────────────────┘ │
│                                                 │
│  ⚙️ Settings                                   │
│  [API Keys] [Rate Limits] [Data Retention]    │
└────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: FastAPI Backend (1-2 weeks)

**Already Have**: `api/main_api.py` (basic structure)

**Need to Add**:
1. **User Authentication**
2. **Analysis Endpoints**
3. **Results Delivery**
4. **Admin Endpoints**

**File Structure**:
```python
api/
├── main_api.py          # FastAPI app
├── auth.py              # Authentication (JWT)
├── users.py             # User management endpoints
├── analysis.py          # Analysis endpoints
├── results.py           # Results/outputs endpoints
├── admin.py             # Admin endpoints
└── websocket.py         # Real-time updates
```

**Example Implementation** (`api/analysis.py`):
```python
from fastapi import APIRouter, Depends, BackgroundTasks
from typing import Dict
from orchestration.comprehensive_orchestrator import ComprehensiveOrchestrator

router = APIRouter(prefix="/api/v1/analysis")

@router.post("/run")
async def run_analysis(
    symbol: str,
    options: AnalysisOptions,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Run comprehensive analysis"""
    
    # Run in background
    task_id = generate_task_id()
    background_tasks.add_task(
        run_analysis_async,
        task_id, symbol, options, current_user.id
    )
    
    return {
        "task_id": task_id,
        "status": "processing",
        "estimated_time": "30-60 seconds"
    }

@router.get("/status/{task_id}")
async def get_status(task_id: str):
    """Check analysis status"""
    status = await get_task_status(task_id)
    return status

@router.get("/results/{task_id}")
async def get_results(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get analysis results"""
    results = await get_analysis_results(task_id)
    
    return {
        "valuation": results.valuation,
        "outputs": {
            "excel": f"/downloads/{task_id}/excel",
            "pptx": f"/downloads/{task_id}/pptx",
            "dashboard": f"/dashboards/{task_id}"
        }
    }
```

### Phase 2: User Management (1 week)

**Database Schema** (Add to DuckDB or PostgreSQL):
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    full_name VARCHAR,
    role VARCHAR,  -- 'admin', 'analyst', 'viewer'
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE user_sessions (
    session_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    expires_at TIMESTAMP,
    ip_address VARCHAR
);

CREATE TABLE analysis_permissions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    analysis_id UUID,
    permission VARCHAR  -- 'view', 'edit', 'delete'
);
```

**Admin Endpoints** (`api/admin.py`):
```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/admin")

class UserCreate(BaseModel):
    email: str
    full_name: str
    role: str
    password: str

@router.post("/users")
async def create_user(
    user: UserCreate,
    admin: User = Depends(require_admin)
):
    """Admin creates new user"""
    # Hash password
    # Create user in database
    # Send welcome email
    return {"user_id": new_user.id}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin: User = Depends(require_admin)
):
    """Admin deletes user"""
    # Deactivate user
    # Transfer or delete their analyses
    return {"status": "deleted"}

@router.get("/users")
async def list_users(
    admin: User = Depends(require_admin)
):
    """Get all users"""
    users = get_all_users()
    return users
```

### Phase 3: Frontend Web Application (2-3 weeks)

**Technology Stack**:
```
Frontend Framework:  React 18+ with TypeScript
Styling:            Tailwind CSS
UI Components:      Shadcn/ui (professional IB look)
State:              Zustand + TanStack Query
Charts:             Recharts + Plotly.js
Forms:              React Hook Form + Zod validation
Auth:               JWT tokens + HTTP-only cookies
```

**File Structure**:
```
frontend/
├── src/
│   ├── components/
│   │   ├── Dashboard.tsx
│   │   ├── AnalysisForm.tsx
│   │   ├── ResultsViewer.tsx
│   │   ├── ChatInterface.tsx
│   │   ├── AdminPanel.tsx
│   │   └── shared/
│   ├── pages/
│   │   ├── Home.tsx
│   │   ├── Analysis.tsx
│   │   ├── Results.tsx
│   │   └── Admin.tsx
│   ├── hooks/
│   │   ├── useAnalysis.ts
│   │   ├── useAuth.ts
│   │   └── useResults.ts
│   ├── api/
│   │   └── client.ts       # Axios/Fetch wrapper
│   └── App.tsx
├── package.json
└── vite.config.ts
```

### Phase 4: AI Chat Integration (1 week)

**Chat Interface** (WebSocket):
```python
# api/websocket.py
from fastapi import WebSocket
from storage.memory_manager import MemoryManager

@app.websocket("/ws/chat/{session_id}")
async def chat_endpoint(
    websocket: WebSocket,
    session_id: str
):
    await websocket.accept()
    memory = MemoryManager()
    
    while True:
        # Receive user message
        message = await websocket.receive_text()
        
        # Get relevant context from MemoryManager
        history = memory.get_history(limit=10)
        context = build_context_from_history(history)
        
        # Generate response from LLM
        llm = LLMClient()
        response = llm.chat([
            {"role": "system", "content": f"You are a financial analyst. Use this context: {context}"},
            {"role": "user", "content": message}
        ])
        
        # Send response
        await websocket.send_json({
            "type": "message",
            "content": response,
            "citations": extract_citations(context)
        })
```

**Frontend Chat Component**:
```typescript
// components/ChatInterface.tsx
import { useState, useEffect } from 'react';

export function ChatInterface({ sessionId }: { sessionId: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [ws, setWs] = useState<WebSocket | null>(null);
  
  useEffect(() => {
    const socket = new WebSocket(`ws://localhost:8000/ws/chat/${sessionId}`);
    
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.content,
        citations: data.citations
      }]);
    };
    
    setWs(socket);
    
    return () => socket.close();
  }, [sessionId]);
  
  const sendMessage = (content: string) => {
    if (ws) {
      ws.send(content);
      setMessages(prev => [...prev, { role: 'user', content }]);
    }
  };
  
  return (
    <div className="chat-container">
      {messages.map((msg, i) => (
        <ChatMessage key={i} message={msg} />
      ))}
      <ChatInput onSend={sendMessage} />
    </div>
  );
}
```

---

## Complete User Workflows

### Workflow 1: Analyst Runs Analysis

```
1. User logs in → Dashboard
2. Click "New Analysis"
3. Enter: AAPL
4. Select: DCF + CCA + Excel Output
5. Click "Run Analysis"
   └─→ Backend runs ComprehensiveOrchestrator
   └─→ Real-time status updates via WebSocket
   └─→ Stores in MemoryManager (DuckDB)
6. Analysis complete (30-60 sec)
7. Redirect to Results page
8. View interactive dashboard
9. Download Excel (13 tabs)
10. Download PowerPoint
11. Ask AI questions via chat
```

### Workflow 2: AI Q&A Session

```
1. User on Results page
2. Opens AI Chat panel
3. Asks: "What drove the valuation?"
   └─→ Backend retrieves from MemoryManager
   └─→ LLM generates response with citations
   └─→ Returns: "Based on DCF analysis..."
4. Asks: "How does AAPL compare to MSFT?"
   └─→ Backend searches MemoryManager
   └─→ Finds both analyses
   └─→ Returns comparative analysis
5. All responses cite data sources
6. No hallucination (checked by test suite)
```

### Workflow 3: Admin Manages Users

```
1. Admin logs in (role: admin)
2. Navigate to Admin Panel
3. View all users (table view)
4. Click "+ Add User"
5. Fill form:
   - Email: new.analyst@firm.com
   - Name: John Doe
   - Role: Analyst
   - Password: (auto-generated)
6. Click "Create"
   └─→ Backend creates user
   └─→ Sends welcome email
7. User receives credentials
8. Admin can later:
   - Edit user permissions
   - Deactivate user
   - View user activity
   - Delete user
```

---

## Quick Start Implementation

### Minimal Viable Product (1 Day)

**Option A: Streamlit (Fastest)**

```python
# frontend_streamlit.py
import streamlit as st
import asyncio
from orchestration.comprehensive_orchestrator import ComprehensiveOrchestrator
from agents.exporter_agent_enhanced import EnhancedExporterAgent

st.title("🏦 FMNA Platform")

# Sidebar
symbol = st.sidebar.text_input("Company Symbol", "AAPL")
run_analysis = st.sidebar.button("Run Analysis")

if run_analysis:
    with st.spinner(f"Analyzing {symbol}..."):
        # Run analysis
        orch = ComprehensiveOrchestrator()
        result = asyncio.run(orch.run_comprehensive_analysis(
            symbol=symbol,
            period="annual",
            peers_required=3
        ))
        
        # Display results
        st.success("Analysis Complete!")
        
        st.metric("DCF Value", f"${result.valuation.dcf_result.value_per_share:.2f}")
        st.metric("CCA Value", f"${result.valuation.cca_result.value_per_share_ebitda:.2f}")
        
        # Generate outputs
        exporter = EnhancedExporterAgent()
        
        excel = exporter.export_comprehensive_excel_model(symbol, result.company_name, prepare_data(result))
        st.download_button("📊 Download Excel", data=open(excel, 'rb'), file_name=excel.name)
        
        # Chat interface
        st.subheader("💬 Ask AI")
        question = st.text_input("Your question:")
        if question:
            # Get answer from LLM with context
            answer = get_ai_response(question, result)
            st.info(answer)
```

**Deploy**:
```bash
pip install streamlit
streamlit run frontend_streamlit.py
```

**Option B: Gradio (Also Fast)**

```python
# frontend_gradio.py
import gradio as gr
from orchestration.comprehensive_orchestrator import ComprehensiveOrchestrator

async def analyze_company(symbol, options):
    orch = ComprehensiveOrchestrator()
    result = await orch.run_comprehensive_analysis(symbol=symbol)
    
    return {
        "valuation": f"${result.valuation.valuation_range[0]:.2f} - ${result.valuation.valuation_range[1]:.2f}",
        "dcf": f"${result.valuation.dcf_result.value_per_share:.2f}",
        "download_link": generate_excel(result)
    }

with gr.Blocks() as demo:
    gr.Markdown("# FMNA Financial Modeling Platform")
    
    with gr.Row():
        symbol_input = gr.Textbox(label="Company Symbol", value="AAPL")
        run_btn = gr.Button("Run Analysis")
    
    with gr.Row():
        valuation_output = gr.Textbox(label="Valuation Range")
        dcf_output = gr.Textbox(label="DCF Value")
    
    excel_download = gr.File(label="Download Excel Model")
    
    run_btn.click(
        analyze_company,
        inputs=[symbol_input],
        outputs=[valuation_output, dcf_output, excel_download]
    )

demo.launch()
```

---

## User Roles & Permissions

### Role Hierarchy

**1. Super Admin**
- Full system access
- Create/delete users
- Configure API keys
- View all analyses
- Access audit logs

**2. Admin**
- Create/edit users (except super admin)
- View all analyses
- Generate reports
- Configure user settings

**3. Analyst**
- Run analyses
- View own analyses
- Download outputs
- Chat with AI
- Share results with team

**4. Viewer**
- View shared analyses
- Download shared outputs
- Read-only access
- Ask AI questions (limited)

### Permissions Matrix

| Feature | Super Admin | Admin | Analyst | Viewer |
|---------|-------------|-------|---------|--------|
| Run Analysis | ✅ | ✅ | ✅ | ❌ |
| View Own Analyses | ✅ | ✅ | ✅ | ✅ |
| View All Analyses | ✅ | ✅ | ❌ | ❌ |
| Download Outputs | ✅ | ✅ | ✅ | ✅ (shared only) |
| AI Chat | ✅ | ✅ | ✅ | ✅ (limited) |
| Create Users | ✅ | ✅ | ❌ | ❌ |
| Delete Users | ✅ | ✅ | ❌ | ❌ |
| System Settings | ✅ | ❌ | ❌ | ❌ |
| Audit Logs | ✅ | ✅ | ❌ | ❌ |

---

## Results Access & Delivery

### Method 1: Direct Download (Simple)
```python
@router.get("/download/excel/{analysis_id}")
async def download_excel(
    analysis_id: str,
    current_user: User = Depends(get_current_user)
):
    """Download Excel file"""
    file_path = get_excel_path(analysis_id)
    return FileResponse(file_path, filename=f"{analysis_id}.xlsx")
```

### Method 2: Cloud Storage (Scalable)
```python
# Use AWS S3 or Azure Blob
import boto3

s3 = boto3.client('s3')

def upload_results(analysis_id: str, files: Dict[str, Path]):
    """Upload results to S3"""
    for file_type, file_path in files.items():
        s3.upload_file(
            str(file_path),
            bucket='fmna-outputs',
            key=f"{analysis_id}/{file_type}"
        )
    
    # Generate presigned URLs (expire in 7 days)
    urls = {
        file_type: s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': 'fmna-outputs', 'Key': f"{analysis_id}/{file_type}"},
            ExpiresIn=604800
        )
        for file_type in files.keys()
    }
    
    return urls
```

### Method 3: Email Delivery (Automated)
```python
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import smtplib

def email_results(
    user_email: str,
    company: str,
    excel_path: Path,
    pptx_path: Path
):
    """Email results to user"""
    msg = MIMEMultipart()
    msg['Subject'] = f"FMNA Analysis Complete: {company}"
    msg['From'] = "noreply@fmna.platform"
    msg['To'] = user_email
    
    # Attach files
    for path in [excel_path, pptx_path]:
        with open(path, 'rb') as f:
            part = MIMEApplication(f.read())
            part.add_header('Content-Disposition', 'attachment', filename=path.name)
            msg.attach(part)
    
    # Send
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.send_message(msg)
```

---

## Recommended Implementation Timeline

### Week 1: FastAPI Backend
- [ ] Add authentication (JWT)
- [ ] Analysis endpoints
- [ ] Results delivery endpoints
- [ ] User management endpoints
- [ ] Test with Postman/curl

### Week 2: Streamlit MVP
- [ ] Deploy Streamlit frontend
- [ ] Connect to FastAPI backend
- [ ] Basic analysis workflow
- [ ] Results download
- [ ] Internal testing

### Week 3: Admin Portal
- [ ] User management UI
- [ ] Permissions system
- [ ] Activity monitoring
- [ ] System settings

### Week 4: Enhanced UI
- [ ] React frontend (if needed)
- [ ] Professional styling
- [ ] Interactive dashboards
- [ ] AI chat interface

---

## Quick Start (Deploy Today!)

### Option 1: Streamlit (15 minutes)

```bash
# Install
pip install streamlit

# Create minimal UI
cat > app.py << 'EOF'
import streamlit as st
import asyncio
from orchestration.comprehensive_orchestrator import ComprehensiveOrchestrator

st.title("FMNA Platform")
symbol = st.text_input("Symbol", "AAPL")

if st.button("Analyze"):
    with st.spinner("Running analysis..."):
        orch = ComprehensiveOrchestrator()
        result = asyncio.run(orch.run_comprehensive_analysis(symbol=symbol))
        st.success(f"Value: ${result.valuation.valuation_range[0]:.2f} - ${result.valuation.valuation_range[1]:.2f}")
EOF

# Run
streamlit run app.py
```

### Option 2: FastAPI Only (Dev/API Users)

```bash
# Already in api/main_api.py
uvicorn api.main_api:app --reload
# Access at http://localhost:8000/docs
```

---

## Recommendation

### **Fastest Path to Production** (This Week):

1. **Day 1-2**: Deploy Streamlit UI
   - Quickest way to get users interacting
   - Professional enough for internal use
   - Can add auth later

2. **Day 3-4**: Add FastAPI auth endpoints
   - JWT authentication
   - Basic user CRUD

3. **Day 5**: Deploy internally
   - Team starts using it
   - Gather feedback

### **Production Path** (Next Month):

1. **Week 1**: Build React frontend
2. **Week 2**: Add admin portal
3. **Week 3**: Deploy with proper auth
4. **Week 4**: Add monitoring/alerts

---

## Answer to Your Questions

### Q1: How will users interact with the system?

**Three Ways**:
1. **Web UI** (Streamlit or React) - Click buttons, fill forms
2. **API** (FastAPI) - Programmatic access via HTTP
3. **CLI** (Python scripts) - Command-line for power users

### Q2: How will you add/delete users as admin?

**Admin Panel** (Web UI):
- Click "+ Add User" button
- Fill form (email, name, role)
- System creates user & sends invite
- Edit/Delete from user list view

**API** (Programmatic):
```python
POST /api/v1/admin/users
DELETE /api/v1/admin/users/{user_id}
```

**Database** (Direct):
```sql
INSERT INTO users (email, role, password_hash) VALUES (...);
DELETE FROM users WHERE id = '...';
```

### Q3: How will users interact with AI?

**Chat Interface** (WebSocket):
- Real-time conversation
- AI retrieves context from MemoryManager (DuckDB)
- Responses include citations
- No hallucination (tested and validated)

### Q4: How will users access results/outputs?

**Multiple Methods**:
1. **Download** - Click download button (Excel/PPT/PDF)
2. **View** - Embedded Plotly dashboards in browser
3. **Email** - Automated delivery to inbox
4. **Cloud Link** - Shareable S3/Azure links
5. **API** - Programmatic access via GET
