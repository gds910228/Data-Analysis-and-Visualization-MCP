# MCP Data Analysis & Visualization Service — Task Board

## To Do
- [ ] Documentation
  - [ ] README: how to run the MCP server (uv run python main.py)
  - [ ] Usage examples for tools: health, upload_csv, analyze_summary, visualize_barchart, report
- [ ] QA & Testing
  - [ ] Provide sample CSV datasets
  - [ ] Smoke test steps for end-to-end flow
- [ ] Enhancements
  - [ ] Histogram tool (numeric distributions)
  - [ ] Cache per-file metadata (delimiter/encoding/columns) to reduce repeated params
  - [ ] Configurable output directory and chart theme
- [ ] Competition Package
  - [ ] Pitch document and demo flow
  - [ ] MCP usage notes for judges (client invocation)

## Doing
- [ ] — (none)

## Done
- [x] Architecture decision: MCP (FastMCP)
- [x] Environment setup (uv add fastapi uvicorn pandas seaborn matplotlib python-multipart)
- [x] health tool
- [x] upload_csv tool
- [x] analyze_summary tool
- [x] visualize_barchart tool
- [x] report tool
- [x] Unified validation & error handling (tool_guard)
- [x] Update tasks.md to MCP task board