# MCP 数据分析与可视化服务

专注于特定领域的 MCP 服务器，可将 CSV 数据快速转化为洞察和图表。基于 Python FastMCP、Pandas、Seaborn、Matplotlib 与 Plotly 构建；AI 洞察对接蓝耘 MaaS（/maas/kimi/Kimi-K2-Instruct）。

- 传输方式：服务器发送事件（SSE）
- 工具（核心）：health、upload_csv、upload_excel、analyze_summary、visualize_barchart、visualize_interactive、report、generate_ai_insights、export_report_html
- 输出格式：JSON（分析/洞察）+ PNG（静态图）+ HTML（交互图/整页报告）

## 功能
- 上传 CSV/Excel（.xlsx）内容并以 ID 形式持久化存储（自动识别 .csv/.xlsx；Excel 默认读取首个工作表）
- 数值列的描述性统计分析
- 可视化：
  - 静态柱状图（PNG，Matplotlib/Seaborn）
  - 交互式柱状图（HTML，Plotly）
- AI 洞察：调用蓝耘 MaaS 生成“结论/建议/注意事项”
- 一键生成：
  - 报告（report 工具，支持交互式图与 AI 洞察开关）
  - 整页报告 HTML（export_report_html：数据摘要 + 交互图 + AI 洞察）
- 工具间统一错误处理，MaaS 调用支持超时/重试与调试落盘

## 要求
- Python 3.13+
- [uv](https://github.com/astral-sh/uv) 用于依赖项管理
- 操作系统：Windows/Linux/macOS

项目依赖项已在 `pyproject.toml` 中声明。

## 安装
```bash
# 同步依赖
uv sync
```

## 环境变量（.env）
请在项目根目录创建 `.env`（已在 .gitignore 中忽略）：
```
LANYUN_API_KEY=your_api_key_here
LANYUN_MAAS_BASE_URL=https://maas-api.lanyun.net/v1
LANYUN_MODEL=/maas/kimi/Kimi-K2-Instruct

# 可选：运行时调优（超时/重试/调试）
LANYUN_TIMEOUT_SECS=40
LANYUN_RETRIES=3
LANYUN_BACKOFF_SECS=1.5
LANYUN_DEBUG=0
```
说明：
- 默认模型已对齐蓝耘路径模型 `/maas/kimi/Kimi-K2-Instruct`。
- 将 `LANYUN_DEBUG=1` 可在 `outputs/maas_last_response.json` 落盘最近一次 MaaS 响应/错误，便于排障。
- 避免将 `.env` 提交到版本库。

## MCP 客户端配置（示例）
```
{
  "mcpServers": {
    "mcp-data-Analysis": {
      "disabled": false,
      "timeout": 60,
      "type": "sse",
      "url": "http://127.0.0.1:8000/sse"
    }
  }
}
```

## 运行
```bash
uv run python main.py
```
默认启动 SSE 服务，控制台会打印监听 URL（实际端口依环境而定）。

## 工具与示例调用
所有工具返回结构化 JSON。错误时统一返回：
```json
{
  "status": "error",
  "error": {"type": "ErrorType", "message": "Explanation"}
}
```

### 1) health
- 参数：无
- 响应（示例）：
```json
{"status":"ok","service":"DataVizMCP","version":"0.1.0","time":"...","python":"3.13.x"}
```

### 2) upload_csv
- 参数：
  - data: string（CSV 内容，必填）
  - delimiter: string（默认 ","）
  - encoding: string（默认 "utf-8"）
- 响应（示例）：
```json
{"status":"saved","file_id":"<id>","path":"data/<id>.csv","size_bytes":123}
```

### 3) analyze_summary
- 参数：file_id, delimiter, encoding
- 响应（节选）：
```json
{
  "status": "ok",
  "row_count": 20,
  "columns": [{"name":"Column1","dtype":"float64"}, ...],
  "numeric_stats": {
    "Column2": {"count":20,"mean":0.48,"std":0.23,"min":0.02,"median":0.48,"max":0.82}
  }
}
```

### 4) visualize_barchart（静态 PNG）
- 参数：file_id, x, y, agg ("sum|mean|median|min|max|count"), delimiter, encoding, figsize
- 响应（示例）：
```json
{
  "status":"ok",
  "chart_path":"outputs/<id>_<x>_<y>_<agg>_...Z.png",
  "categories": 10
}
```

### 5) visualize_interactive（交互 HTML）
- 参数：file_id, kind="barchart", x, y, agg, delimiter, encoding
- 响应（示例）：
```json
{
  "status":"ok",
  "kind":"barchart",
  "html_path":"outputs/interactive/<id>_barchart_<x>_<y>_<agg>_...Z.html",
  "categories": 10
}
```

### 6) generate_ai_insights（AI 洞察）
- 参数：file_id；可选 analysis（结构同 analyze_summary 返回体）、viz（如 {"kind":"barchart","x":"...","y":"...","agg":"sum"}）；delimiter, encoding；timeout_secs（默认 15）
- 依赖：.env 中的 MaaS 配置
- 成功（示例）：
```json
{"status":"ok","provider":"lanyun-maas","model":"/maas/kimi/Kimi-K2-Instruct","insights":"...","used_fallback":false}
```
- 回退（示例，网络/鉴权异常等）：
```json
{"status":"ok","provider":"fallback","insights":"...","used_fallback":true,"maas_error":"ReadTimeout: ..."}
```

### 7) report（一体化调度：分析 + 可视化 + 可选 AI）
- 参数：
  - file_id（必填）
  - analysis: "summary" | "none"（默认 "summary"）
  - viz: 可选
    - kind: "barchart" | "interactive_barchart"
    - x, y, agg（与图表工具一致），可选 figsize（静态图）
  - ai: bool | object（为 true 时调用 AI 洞察；或传 {"timeout_secs": 50.0}）
  - delimiter, encoding
- 响应（节选）：
```json
{
  "status":"ok",
  "analysis": {"row_count":20,"columns":[...],"numeric_stats":{...}},
  "viz": {
    "kind":"interactive_barchart",
    "html_path":"outputs/interactive/....html",
    "categories":20
  },
  "ai_insights": {
    "provider":"lanyun-maas",
    "model":"/maas/kimi/Kimi-K2-Instruct",
    "used_fallback":false,
    "insights":"..."
  }
}
```

### 8) export_report_html（整页报告 HTML）
将“数据摘要 + 交互式图表 + AI 洞察”组合为单页 HTML，便于展示/分享。
- 参数：file_id, x, y, agg（默认 "sum"）, delimiter, encoding, ai（默认 true）
- 输出：`outputs/reports/*.html`
- 成功（示例）：
```json
{
  "status":"ok",
  "report_path":"outputs/reports/<id>_report_<x>_<y>_<agg>_...Z.html",
  "ai_enabled": true
}
```

## 本地端到端脚本（无需 MCP 客户端）
- 交互图 + 洞察（自动链路）：`scripts/smoke_e2e.py`
  ```bash
  python scripts/smoke_e2e.py --csv data/sample_test_data.csv
  # 输出 provider/fallback/model/maas_error 等信息
  ```
- report 集成验证：`scripts/test_report.py`
  ```bash
  python scripts/test_report.py
  # 默认 viz.kind=interactive_barchart，ai={"timeout_secs":50.0}
  ```
- 整页报告导出：`scripts/gen_report.py`
  ```bash
  python scripts/gen_report.py
  # 打印 outputs/reports/*.html
  ```

## 项目结构
```
.
├─ main.py                 # FastMCP 服务器及工具
├─ maas_client.py          # 蓝耘 MaaS 客户端封装（/chat/completions）
├─ data/                   # 上传 CSV/Excel（运行时生成）
├─ outputs/
│  ├─ *.png                # 静态图
│  ├─ interactive/*.html   # 交互式图表
│  └─ reports/*.html       # 整页报告（摘要+交互图+AI洞察）
├─ scripts/
│  ├─ smoke_e2e.py         # 上传→分析→交互图→AI洞察
│  ├─ test_report.py       # report 集成验证
│  └─ gen_report.py        # 整页报告导出
├─ docs/
│  └─ tasks.md             # 任务看板
├─ .env.example            # 环境变量示例（勿提交真实 .env）
├─ .gitignore
├─ pyproject.toml
└─ uv.lock
```

## 故障排除
- 交互图为空白：检查浏览器安全策略或确保 `include_plotlyjs="cdn"` 可访问。
- AI 调用超时/429/5xx：
  - 增大 `LANYUN_TIMEOUT_SECS`，配置 `LANYUN_RETRIES`/`LANYUN_BACKOFF_SECS`
  - 开启 `LANYUN_DEBUG=1` 查看 `outputs/maas_last_response.json`
  - 确保 `.env` 中 `LANYUN_API_KEY`/`LANYUN_MAAS_BASE_URL`/`LANYUN_MODEL` 正确
- 回退为 fallback：多因网络波动或接口限流；可稍后重试或提高超时。
- 安全：文件名/路径已做隔离与校验；避免提交敏感配置与数据。

### 目前功能汇总
- 数据接入
  - 上传 CSV 内容并以 file_id 持久化（data/{file_id}.csv）
  - 数值列描述性统计（行数、列信息、均值/中位数/最值等）
- 可视化
  - visualize_barchart：静态柱状图（保留 Seaborn/Matplotlib 作为回退）
  - visualize_interactive：交互式柱状图（Plotly，outputs/interactive/*.html）
  - visualize_interactive_line：交互式折线图（Plotly，outputs/interactive/*.html）
- 报告
  - report：支持 analysis='summary'|'none'；viz.kind 支持 'interactive_barchart' 与 'interactive_linechart'；ai 可为 true 或对象（如 {'timeout_secs': 50}）
  - export_report_html：一页式 HTML（数据摘要 + 交互式图表 + AI 洞察），输出到 outputs/reports/*.html；参数 kind 支持 'interactive_barchart' 与 'interactive_linechart'
- AI 洞察
  - 对接蓝耘 MaaS 模型 /maas/kimi/Kimi-K2-Instruct
  - 超时/重试可配；开启调试（LANYUN_DEBUG=1）时将最近一次响应落盘 outputs/maas_last_response.json
- 输出目录
  - 交互图：outputs/interactive/*.html
  - 整页报告：outputs/reports/*.html

### 使用示例（Python）
- 交互式柱状图
```python
import main, pathlib
fid = main.upload_csv(pathlib.Path('data/sample_test_data.csv').read_text(encoding='utf-8'))['file_id']
res = main.visualize_interactive(file_id=fid, x='Column1', y='Column2', agg='sum')
print(res['html_path'])
```

- 交互式折线图
```python
import main, pathlib
fid = main.upload_csv(pathlib.Path('data/sample_test_data.csv').read_text(encoding='utf-8'))['file_id']
res = main.visualize_interactive_line(file_id=fid, x='Column1', y='Column2', agg='sum')
print(res['html_path'])
```

- 一页式报告（含 AI 洞察）
```python
import main, pathlib
fid = main.upload_csv(pathlib.Path('data/sample_test_data.csv').read_text(encoding='utf-8'))['file_id']
rep = main.export_report_html(file_id=fid, x='Column1', y='Column2', agg='sum', kind='interactive_barchart', ai={'timeout_secs': 50})
print(rep['report_path'])
```

- report（服务内聚合调用）
```python
import main, pathlib
fid = main.upload_csv(pathlib.Path('data/sample_test_data.csv').read_text(encoding='utf-8'))['file_id']
r = main.report(file_id=fid, analysis='summary', viz={'kind':'interactive_linechart','x':'Column1','y':'Column2','agg':'sum'}, ai=True)
print(r['viz']['html_path'], r['ai_insights'].get('provider'), r['ai_insights'].get('used_fallback'))
```

### 环境变量
- 必填
  - LANYUN_API_KEY=你的密钥
- 可选/默认
  - LANYUN_MAAS_BASE_URL=https://maas-api.lanyun.net/v1
  - LANYUN_MODEL=/maas/kimi/Kimi-K2-Instruct
  - LANYUN_TIMEOUT_SECS=30（请求超时秒数，可调大以避免 ReadTimeout）
  - LANYUN_RETRIES=0~3（失败重试次数）
  - LANYUN_BACKOFF_SECS=1.5（指数退避基数）
  - LANYUN_DEBUG=0|1（1 时落盘最近一次响应到 outputs/maas_last_response.json）

### MCP 说明（SSE）
- 传输：SSE（mcp.run(transport="sse")）
- 工具清单（部分）
  - upload_csv, analyze_summary
  - visualize_barchart, visualize_interactive, visualize_interactive_line
  - report（支持 interactive_barchart/interactive_linechart + ai）
  - export_report_html（一页式报告导出）
  - generate_ai_insights（AI 洞察）

## 许可证
MIT（或按赛事要求调整）## 更新：交互式图表与 AI 洞察（v0.2）

