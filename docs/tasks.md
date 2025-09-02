# 项目任务看板（MCP 数据分析与可视化服务）
更新时间：2025-09-02 10:40

## To Do
- [ ] 亮点功能：交互式图表
  - [ ] 安全与资源：限制数据量/字段白名单、渲染超时
  - [ ] 报告联动：在 report 流程中支持交互式开关（如 viz.kind 支持 'interactive_barchart'）
- [ ] 亮点功能：AI 洞察解读
  - [ ] 报告集成：在 report 输出中新增“AI 洞察”段落
  - [ ] 可靠性：429/5xx 重试、指数退避；错误码分类
  - [ ] 单元测试：Mock API、提示词健壮性
- [ ] 平台结合度与发布
  - [ ] README 更新：SSE 连接与使用说明（mcp.run(transport="sse")）
  - [ ] MCP 工具清单与示例：签名、调用示例、错误码约定
  - [ ] 上架蓝耘 MCP 广场发布说明（部署、版本、更新日志）
  - [ ] 演示脚本：从上传到洞察的全链路演示
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
- [ ] AI 洞察冒烟测试（使用本地 .env，模型 /maas/kimi/Kimi-K2-Instruct）

## Done
- [x] 初版核心功能（CSV 上传、描述性统计、柱状图、统一错误处理）
- [x] 库选型：Plotly（保留 Seaborn/Matplotlib 静态回退）
- [x] 工具封装：visualize_interactive（交互式柱状图，输出 HTML）
- [x] 输出规范：HTML 保存至 outputs/interactive/{id}.html
- [x] 蓝耘 MaaS 客户端抽离：maas_client.py（/chat/completions 封装）
- [x] 配置管理：.env.example、python-dotenv、.gitignore 忽略 .env
- [x] 工具封装：generate_ai_insights（.env 配置；失败回退为规则洞察）
- [x] 冒烟测试：交互式柱状图（data/sample_test_data.csv 成功生成 HTML）
- [x] MaaS 模型默认值与示例：默认 /maas/kimi/Kimi-K2-Instruct（与 .env.example 对齐）
- [x] 新增脚本：scripts/smoke_e2e.py（上传→分析→交互图→AI 洞察）