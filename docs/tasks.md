## To Do
- [ ] 交互式饼图（Plotly pie）
  - [ ] 新增工具：visualize_interactive_pie
  - [ ] report.viz.kind 支持：interactive_piechart
  - [ ] export_report_html 支持饼图渲染
- [ ] 更多数据源
  - [ ] Excel（.xlsx）
  - [ ] JSON（records/columns）
- [ ] 安全与错误处理强化
  - [ ] 输入校验（文件大小/行数/列名/类型）
  - [ ] 路径隔离与防穿越
  - [ ] 统一错误码与日志脱敏
- [ ] 平台结合与发布
  - [ ] 上架蓝耘 MCP 广场的发布说明
  - [ ] 端到端演示脚本（上传→分析→交互图→AI洞察→报告）

## Doing
- [ ] 交互式饼图：设计与实现（工具→report→export_report_html）

## Done
- [x] 交互式柱状图（Plotly）
- [x] 交互式折线图（Plotly）+ 时间轴判定修复（数值列不误判为时间戳）
- [x] 新工具：visualize_interactive_line
- [x] report 集成：viz.kind=interactive_linechart + ai 参数超时可配
- [x] export_report_html：整页报告（摘要+交互图+AI洞察），支持 barchart/linechart
- [x] 蓝耘 MaaS 接入（/maas/kimi/Kimi-K2-Instruct）：超时/重试（可配）+ 调试落盘
- [x] e2e 冒烟与报告验证（provider=lanyun-maas, fallback=false）
- [x] README：补充 report/export_report_html 示例与环境变量说明