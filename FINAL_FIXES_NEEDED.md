# Final Fixes Needed

## Issue 1: Missing Growth Scenarios Engine (6th engine)

**Root Cause**: Growth Scenarios is disabled by default in the orchestrator
- Frontend checkbox controls it via `analysis_options.get('growth', False)`
- Log shows "5 engines" because growth_scenarios=False

**Solution Options**:
1. Enable growth scenarios checkbox in frontend
2. Change default to `run_growth_scenarios=True` in orchestrator
3. The engine exists and works - just needs to be enabled

**Current Status**: This is expected behavior - Growth Scenarios is optional and controlled by frontend checkbox

## Issue 2: PowerPoint NoneType Error in Integration Slides

**Error Location**: 
```
File "C:\Users\smaan\OneDrive\fmna\agents\exporter_agent_enhanced.py", line 2278
'NoneType' object has no attribute 'text'
```

**Root Cause**: When no integration slides layout exists, `slide.placeholders[1]` returns None

**Fix**: Add proper None checking in `create_integration_slides` method

## Summary

You're seeing 5 engines because:
- ✅ DCF
- ✅ CCA  
- ✅ LBO
- ✅ Merger
- ✅ 3-Statement

Missing:
- ❌ Growth Scenarios (disabled by default via frontend checkbox)

To enable all 6 engines, check the "Growth Scenarios" option in the frontend before running analysis.
