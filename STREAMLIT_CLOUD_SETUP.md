# Streamlit Cloud Deployment Guide

## 🔑 API Key Configuration (CRITICAL)

Streamlit Cloud requires API keys to be configured as **Secrets** through the dashboard. Environment variables alone won't work.

### Step 1: Configure Secrets in Streamlit Cloud

1. **Go to your Streamlit Cloud dashboard**: https://share.streamlit.io
2. **Select your app** from the list
3. **Click the ⚙️ (Settings) button** in the bottom right
4. **Navigate to the "Secrets" section**
5. **Add your secrets in TOML format:**

```toml
# .streamlit/secrets.toml format
FMP_API_KEY = "your_fmp_api_key_here"
DEEPSEEK_API_KEY = "your_deepseek_api_key_here"

# Optional but recommended
LLM_MODEL = "deepseek-reasoner"
LLM_MAX_TOKENS = "32000"
DEFAULT_PERIOD = "annual"
```

### Step 2: Get Your FMP API Key

1. Go to https://financialmodelingprep.com/
2. Sign up for a free account
3. Navigate to your dashboard
4. Copy your API key
5. Paste it into Streamlit Cloud secrets (Step 1 above)

**Free tier provides:**
- 250 API calls per day
- Access to all endpoints needed for this platform
- Sufficient for testing and light usage

### Step 3: Get Your DeepSeek API Key (for AI features)

1. Go to https://platform.deepseek.com/
2. Sign up and get your API key
3. Add to Streamlit Cloud secrets

### Step 4: Verify Configuration

After adding secrets:
1. **Restart your Streamlit app** (use the hamburger menu → "Reboot")
2. Go to **Settings** page in the app
3. Check that API keys show as "✅ Configured"
4. Try running a test analysis with a symbol like "AAPL"

---

## 🚨 Common Deployment Errors

### Error: "Cannot proceed without real financial data for [symbol]"

**Cause**: FMP_API_KEY not configured in Streamlit Cloud secrets

**Solution**:
1. Add `FMP_API_KEY` to secrets (see Step 1 above)
2. Reboot the app
3. Verify in Settings page

### Error: "API limit exceeded"

**Cause**: You've hit the daily API call limit (250 for free tier)

**Solution**:
1. Wait 24 hours for reset
2. Upgrade to paid FMP plan for higher limits
3. Reduce the number of peers analyzed (default is 5)

### Error: "Module not found" or import errors

**Cause**: Missing dependencies in requirements.txt

**Solution**:
1. Ensure all dependencies are in requirements.txt
2. Check packages.txt for system dependencies
3. Reboot app after updating

---

## 📝 Local Testing Before Deployment

### Option 1: Using .env file (Recommended for local)

Create a `.env` file in the project root:

```bash
FMP_API_KEY=your_key_here
DEEPSEEK_API_KEY=your_key_here
LLM_MODEL=deepseek-reasoner
LLM_MAX_TOKENS=32000
```

### Option 2: Using .streamlit/secrets.toml (Simulates cloud)

Create `.streamlit/secrets.toml`:

```toml
FMP_API_KEY = "your_key_here"
DEEPSEEK_API_KEY = "your_key_here"
```

Then test locally with:
```bash
streamlit run frontend_app.py
```

---

## 🔧 Debugging Tips

### Check if secrets are loaded:

Add this to your app temporarily:

```python
import streamlit as st

# Debug secrets
st.write("Secrets available:", list(st.secrets.keys()))
st.write("FMP Key configured:", "FMP_API_KEY" in st.secrets)
```

### Check API connectivity:

```python
from ingestion.fmp_client import FMPClient

# Test FMP connection
client = FMPClient()
profile = client.get_company_profile("AAPL")
if profile:
    st.success("✅ FMP API working!")
else:
    st.error("❌ FMP API not responding")
```

---

## 📊 Resource Usage

**Free Tier Limits:**
- FMP: 250 API calls/day
- Streamlit Cloud: 1GB RAM, 1 CPU core
- DeepSeek: Varies by plan

**API Calls Per Analysis:**
- Basic analysis: ~15-20 calls
- With 5 peers: ~40-50 calls
- Full analysis (LBO, Merger, etc.): ~60-80 calls

**Recommendations:**
- Start with 3 peers for testing
- Use annual period (fewer data points)
- Upgrade FMP to paid plan for production use

---

## 🚀 Production Deployment Checklist

- [ ] FMP_API_KEY configured in Streamlit secrets
- [ ] DEEPSEEK_API_KEY configured (if using AI features)
- [ ] Test with a simple symbol (AAPL, MSFT)
- [ ] Verify all outputs generate correctly
- [ ] Check Settings page shows "✅" for all APIs
- [ ] Monitor API usage in FMP dashboard
- [ ] Set up error monitoring (optional)
- [ ] Configure custom domain (optional)

---

## 🆘 Support

If you continue to have issues:

1. **Check Streamlit Cloud logs**: Click "Manage app" → "Logs"
2. **Verify secrets format**: Must be valid TOML syntax
3. **Restart app**: Sometimes secrets don't load until restart
4. **Check FMP dashboard**: Confirm API key is active
5. **Contact support**: smaan2011@gmail.com

---

## 📖 Additional Resources

- **Streamlit Cloud Docs**: https://docs.streamlit.io/streamlit-community-cloud
- **FMP API Docs**: https://site.financialmodelingprep.com/developer/docs
- **DeepSeek API**: https://platform.deepseek.com/docs
- **This Project**: See README.md for full documentation
