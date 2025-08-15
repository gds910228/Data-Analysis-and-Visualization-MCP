# MCP 数据分析与可视化服务

专注于特定领域的 MCP 服务器，可将 CSV 数据快速转化为洞察和图表。基于 Python FastMCP、Pandas、Seaborn 和 Matplotlib 构建。

- 传输方式：服务器发送事件（SSE）
- 工具：`health`、`upload_csv`、`analyze_summary`、`visualize_barchart`、`report`
- 输出格式：JSON（分析结果）+ PNG（图表）

## 功能

- 上传 CSV 内容并以 ID 形式持久化存储
- 数值列的描述性统计分析
- 通过分组和聚合生成柱状图
- 一键生成结合分析与可视化的报告
- 工具间统一的错误处理机制

## 要求

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) 用于依赖项管理
- 操作系统：Windows/Linux/macOS

项目依赖项已在 `pyproject.toml` 中声明。

## 设置

```bash
# 可选：若未安装，请安装 uv
# Windows（PowerShell）：
irm https://astral.sh/uv/install.ps1 | iex

# 同步 pyproject.toml 中定义的依赖项
uv sync
```

## MCP配置
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

## 运行

```bash
uv run python main.py
```

服务器将启动一个 SSE 端点，并在控制台记录监听 URL。在默认设置下，该地址通常为：
- http://127.0.0.1:3000/sse（实际地址可能因环境而异）

## 快速本地测试（无需 MCP 客户端）

使用内置示例 CSV 和一个直接调用工具函数的本地脚本进行的最小化端到端测试。此测试在不使用 MCP 客户端的情况下验证整个流程。

- 示例数据集：`samples/sales_small.csv`
- 脚本：`smoke_test.py`

运行：

```bash
uv run python smoke_test.py
```

预期输出：
- 按顺序打印四个 JSON 块：`upload_csv`、`analyze_summary`、`visualize_barchart`、`report`
- 在 `outputs/` 目录下保存一个带时间戳的 PNG 图表文件
- 最后一行：`Smoke test finished.`

如需测试不同结果，可编辑 `samples/sales_small.csv` 并重新运行。

## 通过 MCP 客户端连接

您可以使用任何支持 SSE 连接的 MCP 兼容客户端。不同客户端的 CLI 语法有所不同。典型流程：
- 将客户端指向 SSE 端点（例如 `http://127.0.0.1:3000/sse`）
- 列出工具，然后使用 JSON 负载调用工具

以下示例使用通用格式说明参数和预期结果。请根据您的客户端 CLI 进行适配。

## 工具与示例调用

所有工具均返回结构化 JSON。发生错误时，工具返回：
```json
{
  "status": "error",
  "error": {"type": "ErrorType", ‘message’: "Explanation"}
}
```

### 1) health
检查服务器健康状态/版本。

- 参数：无
- 示例调用（概念性）：
  - 客户端：调用工具 `health`
- 示例响应：
```json
{
  "status": "ok",
  "service": "DataVizMCP",
  "version": "0.1.0",
  "时间": "2025-08-15T00:00:00+00:00",
  "Python": "3.13.x"
}
```

### 2) upload_csv
持久化 CSV 内容并获取 `file_id`。

- 参数：
  - data：字符串，必填（CSV内容）
  - delimiter：字符串，默认","
  - encoding：字符串，默认"utf-8"
- 示例负载：
```json
{
  "data": "city,sales\nA,10\nB,20\nA,5\n",
  "delimiter": ",",
  "encoding": "utf-8"
}
```
- 示例响应：
```json
{
  "status": "saved",
  "file_id": "e4b7f9d3c6b44d30a2f58c9c2e6a1a7d",
  "path": "data/e4b7f9d3c6b44d30a2f58c9c2e6a1a7d.csv",
  "size_bytes": 30,
  "delimiter": ",",
  "encoding": "utf-8"
}
```

### 3) analyze_summary
返回行数、列数据类型和数值统计信息。

- 参数：
  - file_id：字符串，必填
  - delimiter：字符串，默认值为 ","
  - encoding：字符串，默认值为 "utf-8"
- 示例负载：
```json
{
  "file_id": "e4b7f9d3c6b44d30a2f58c9c2e6a1a7d",
  "delimiter": ",",
  "encoding": "utf-8"
}
```
- 示例响应（已截取）：
```json
{
  "status": "ok",
  "file_id": "e4b7f9d3c6b44d30a2f58c9c2e6a1a7d",
  "path": "data/e4b7f9d3c6b44d30a2f58c9c2e6a1a7d.csv",
  "行数": 3,
  "列数": [
    {"名称": "城市", ‘数据类型’: "对象"},
    {"名称": "销售额", ‘数据类型’: "整数64位"}
  ],
  "numeric_stats": {
    "sales": {
      "count": 3.0, ‘mean’: 11.6667, "std": 7.6376,
      "min": 5.0, ‘median’: 10.0, "max": 20.0
    }
  }
}
```

### 4) visualize_barchart
按`x`分组，对`y`进行聚合，并生成PNG条形图。

- 参数：
  - file_id：字符串，必填
  - x：字符串，必填（分类列）
  - y：字符串，必填（用于大多数聚合的数值列）
  - agg: 字符串，取值范围为 ["sum","mean","median","min","max","count"]，默认值为 ‘sum’
  - delimiter: 字符串，默认值为 ","
  - encoding: 字符串，默认值为 "utf-8"
  - figsize: [数字, 数字]，默认值为 [8,6]
- 示例负载：
```json
{
  "file_id": "e4b7f9d3c6b44d30a2f58c9c2e6a1a7d",
  "x": "city",
  "y": "sales",
  "agg": "sum",
  "figsize": [8, 6]
}
```
- 示例响应：
```json
{
  "status": "ok",
  "file_id": "e4b7f9d3c6b44d30a2f58c9c2e6a1a7d",
  "csv_path": "data/e4b7f9d3c6b44d30a2f58c9c2e6a1a7d.csv",
  "chart_path": "outputs/e4b7f9..._city_sales_sum_20250815T000000Z.png",
  "x": "city",
  "y": "sales",
  "agg": "sum",
  "categories": 2
}
```


### 5) 报告
一键式分析调度 + 可选可视化。

- 参数：
  - file_id: 字符串，必填
  - analysis: "summary" 或 ‘none’（默认 "summary"）
  - viz: 可选的可视化对象
    - kind: "barchart"
    - x, y, agg, figsize：与 `visualize_barchart` 相同
  - delimiter, encoding：与其他参数相同默认值
- 示例负载：
```json
{
  "file_id": "e4b7f9d3c6b44d30a2f58c9c2e6a1a7d",
  "analysis": "summary",
  "viz": {
    "kind": "barchart",
    "x": "city",
    "y": "sales",
    "agg": "sum",
    "figsize": [8, 6]
  }
}
```
- 示例响应（已截取）：
```json
{
  "status": "ok",
  "file_id": "e4b7f9d3c6b44d30a2f58c9c2e6a1a7d",
  "csv_path": "data/e4b7f9...csv",
  "analysis": { "...": "摘要负载与analyze_summary相同" },
  "viz": {
    "kind": "barchart",
    "参数": {"x": "城市", "y": "销售额", "聚合方式": ‘求和’, "图例大小": [8, 6]},
    "图表路径": "输出/e4b7f9...png",
    "类别数": 2
  }
}
```

## 端到端烟雾测试

1) 启动服务器：
```bash
uv run python main.py
```

2) 上传 CSV（概念性；根据您的客户端进行调整）：
```json
{"data": "city,sales\nA,10\nB,20\nA,5\n"}
```

3) 分析摘要：
```json
{"file_id": "<file_id_from_upload>"}
```

4) 可视化条形图：
```json
{"file_id": "<file_id>", "x": "city", "y": "sales", ‘agg’: "sum"}
```

5) 报告（合并）：
```json
{
  "file_id": "<file_id>",
  "analysis": "summary",
  "viz": {"kind":"barchart","x":"city","y":"sales",‘agg’:"sum"}
}
```

## 项目结构

```.

├─ main.py                # FastMCP 服务器及工具
├─ data/                  # 上传的 CSV 文件（运行时生成）
├─ outputs/               # 生成的图表（PNG 格式）
├─ samples/
│  └─ sales_small.csv     # 烟雾测试用示例数据集
├─ smoke_test.py          # 本地烟雾测试脚本（不使用MCP客户端）
├─ pyproject.toml         # 依赖项（mcp[cli]、pandas、seaborn、matplotlib等）
├─ uv.lock
└─ docs/
   └─ tasks.md            # 任务板（面向MCP）
```

## 注意事项与故障排除

- 图表保存在`outputs/`目录中，文件名带有时戳。
- 如果您的 CLI 无法连接，请验证服务器启动时打印的 SSE URL。
- 在无头服务器上，Matplotlib 保存 PNG 文件时无需显示后端。
- CSV 分隔符/编码是参数；对于同一文件，请在调用时保持一致。

## 许可证

MIT 许可证（或根据比赛提交需求选择其他许可证）。
