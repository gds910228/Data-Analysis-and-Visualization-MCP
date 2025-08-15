# AI-Powered Data Analysis and Visualization MCP Service

## Core Features

- Natural Language Command Interface (via AI agent)

- CSV Data Upload and Parsing

- Automated Statistical Analysis

- Dynamic Chart Generation (e.g., bar charts, histograms)

## Tech Stack

{
  "Backend": {
    "language": "Python",
    "framework": "MCP (FastMCP)",
    "libraries": [
      "Pandas",
      "Seaborn",
      "Matplotlib",
      "mcp[cli]"
    ]
  }
}

## Design

The service outputs clear analyses and charts (PNG). Emphasis on readability and robustness for agent integration via MCP tools.

## Plan

Note: 

- [ ] is holding
- [/] is doing
- [X] is done

---

[X] Confirm architecture: Keep MCP and implement tools (health, upload_csv, analyze_summary, visualize_barchart, report).

[X] Implement MCP tool: health() returning minimal status/version/timestamp.

[X] Implement MCP tool: upload_csv(data: string, delimiter: ',', encoding: 'utf-8') -> file_id; persist CSV under data/.

[X] Implement MCP tool: analyze_summary(file_id) -> numeric stats (count, mean, std, min, median, max) + columns + row_count.

[X] Implement MCP tool: visualize_barchart(file_id, x, y, agg='sum') -> save PNG under outputs/ and return path.

[X] Implement MCP tool: report(file_id, analysis='summary', viz={kind:'barchart', x, y, agg}) -> combined JSON.

[X] Add validation & error handling (missing columns, bad file_id), consistent error messages.

[X] Update docs/tasks.md to MCP-oriented task board.
