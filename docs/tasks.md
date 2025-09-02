# 项目任务看板（MCP 数据分析与可视化服务）
更新时间：2025-09-02 00:00

## To Do
- [ ] 亮点功能：交互式图表（High Priority）
  - [ ] 库选型与集成：优先 Plotly（Python 友好），保留 Seaborn/Matplotlib 作为静态回退
  - [ ] 工具封装：generate_interactive_chart(dataset_id, chart_type, x, y, groupby, agg, options) -> HTML 字符串 + 元数据
  - [ ] 交互式柱状图：支持分组/聚合、tooltip、缩放拖拽、导出为 HTML
  - [ ] 输出规范：将 HTML 保存至 outputs/interactive/{id}.html，并返回可嵌入片段
  - [ ] 安全与资源：限制数据量/字段白名单、渲染超时
  - [ ] 测试与样例：使用 data/ 与 samples/ 示例数据生成演示（可选生成截图）
- [ ] 亮点功能：AI 洞察解读（蓝耘 MaaS Kimi-K2-instruct）（High Priority）
  - [ ] 文档研读与鉴权流程确认，抽象 HTTP 客户端
  - [ ] 配置管理：LANYUN_API_KEY、模型名、超时与重试策略（env 变量）
  - [ ] Prompt 设计：结合描述性统计与图表语义，输出结构化洞察（要点/结论/建议）
  - [ ] 工具封装：generate_ai_insights(stats, chart_spec, sample_rows) -> bullets + summary
  - [ ] 报告集成：一键报告新增“AI 洞察”段落（含风险与局限提示）
  - [ ] 可靠性：超时/429 重试、失败回退为规则驱动的简要洞察
  - [ ] 单元测试：Mock API、提示词健壮性测试
- [ ] 平台结合度与发布
  - [ ] SSE 连接与使用说明更新 README（mcp.run(transport="sse")）
  - [ ] MCP 工具清单与示例：工具签名、调用示例、错误码约定
  - [ ] 上架蓝耘 MCP 广场流程与发布说明（部署、版本、更新日志）
  - [ ] 演示脚本：从上传到洞察的全链路演示
- [ ] 扩展图表类型（次级，交互优先）
  - [ ] 交互式折线图（时间序列）
  - [ ] 交互式饼图（构成占比）
- [ ] 支持更多数据源（次级）
  - [ ] Excel（.xlsx）：pandas.read_excel，列类型推断
  - [ ] JSON：records/columns 两种格式支持与字段映射校验
- [ ] 安全与错误处理强化
  - [ ] 输入校验：文件大小/行数上限、列名合法性、数据类型检测
  - [ ] 权限与隔离：临时文件路径约束、防路径穿越
  - [ ] 统一错误码与错误消息（用户友好/开发可排查）
  - [ ] 日志与审计：脱敏、采样、请求 ID 贯穿
- [ ] 文档与演示材料
  - [ ] README：功能矩阵、用法、交互式图表预览截图
  - [ ] API 使用示例：调用片段与返回结构
  - [ ] 决赛 PPT Markdown（逐页大纲与示例图）
  - [ ] 决赛 Q&A 速查（评审维度映射答案）
  - [ ] PRD 文档：docs/PRD.md（范围、非功能、风险、里程碑）

## Doing
- [ ] 决赛功能规划与评估

## Done
- [x] 初版核心功能（CSV 上传、描述性统计、柱状图、统一错误处理）