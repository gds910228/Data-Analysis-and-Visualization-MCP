# 项目任务看板（MCP 数据分析与可视化服务）
更新时间：2025-09-02 12:20

## To Do
- [ ] 亮点功能：交互式图表
  - [ ] 安全与资源：限制数据量/字段白名单、渲染超时
- [ ] 亮点功能：AI 洞察解读
  - [ ] 可靠性文档化：错误码分类与说明（429/5xx、超时、解析失败等）
  - [ ] 单元测试：Mock API、提示词健壮性
- [ ] 平台结合度与发布
  - [ ] README 更新：SSE 使用说明（mcp.run(transport="sse")）、工具清单与示例、错误码约定
  - [ ] 上架蓝耘 MCP 广场发布说明（部署、版本、更新日志）
  - [ ] 演示脚本：从上传到洞察到报告的全链路演示
- [ ] 扩展图表类型（交互优先）
  - [ ] 交互式折线图（时间序列）
  - [ ] 交互式饼图（构成占比）
- [ ] 支持更多数据源
  - [ ] Excel（.xlsx）：pandas.read_excel，列类型推断
  - [ ] JSON：records/columns 两种格式支持与字段映射校验
- [ ] 安全与错误处理强化
  - [ ] 输入校验：文件大小/行数上限、列名合法性、数据类型检测
  - [ ] 权限与隔离：临时文件路径约束、防路径穿越
  - [ ] 统一错误码与错误消息（用户友好/可排查）
  - [ ] 日志与审计：脱敏、采样、请求 ID 贯穿

## Doing
- [ ] README 与使用文档更新（含 report 与 export_report_html 示例、环境变量说明）

## Done
- [x] 初版核心功能（CSV 上传、描述性统计、柱状图、统一错误处理）
- [x] 库选型：Plotly（保留 Seaborn/Matplotlib 静态回退）
- [x] 工具封装：visualize_interactive（交互式柱状图，输出 HTML）
- [x] 输出规范：HTML 保存至 outputs/interactive/{id}.html
- [x] 蓝耘 MaaS 客户端抽离：maas_client.py（/chat/completions 封装）
- [x] 配置管理：.env.example、python-dotenv、.gitignore 忽略 .env
- [x] 客户端健壮性：解析兜底、调试落盘 outputs/maas_last_response.json
- [x] 网络健壮性：超时/重试（指数退避）+ 可配置（LANYUN_TIMEOUT_SECS/LANYUN_RETRIES/LANYUN_BACKOFF_SECS）
- [x] 冒烟测试：交互式柱状图（data/sample_test_data.csv 成功生成 HTML）
- [x] 冒烟测试：AI 洞察（provider=lanyun-maas，fallback=false，model=/maas/kimi/Kimi-K2-Instruct）
- [x] report 集成交互式可视化（interactive_barchart）与 AI 洞察（ai 参数，支持超时配置）
- [x] 整页报告导出：export_report_html（数据摘要 + 交互式图 + AI 洞察，输出到 outputs/reports/*.html）
- [x] 脚本：scripts/smoke_e2e.py、scripts/test_report.py、scripts/gen_report.py（集成与报告验证）