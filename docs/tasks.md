## To Do
- [ ] 交互式饼图（Plotly pie）
  - [ ] 新增工具：visualize_interactive_pie
  - [ ] report.viz.kind 支持：interactive_piechart
  - [ ] export_report_html 支持饼图渲染
- [ ] 更多数据源
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
- [x] 更多数据源：Excel（.xlsx）支持（upload_excel + 自动识别 .csv/.xlsx）
- [x] 折线/柱状图支持从 .xlsx 读取（utils/interactive_line.py 适配）
- [x] 依赖：新增 openpyxl
- [x] README：补充 Excel 数据源支持与示例
- [x] 脚本：Excel 测试数据与测试脚本（scripts/gen_excel_sample.py, scripts/test_excel_pipeline.py，含 AI 洞察）