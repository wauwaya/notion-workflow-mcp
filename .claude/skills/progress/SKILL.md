---
name: progress
description: 汇总任务进度。触发：/progress, "总结进度", "汇总进展"
---

汇总任务当前进度，追加到 Notion 任务页面。

## 用法

/progress <task_id>

## 行为

1. 调用 MCP `get_task(task_id)` 获取任务基本信息
2. 调用 MCP `get_subtasks(task_id)` 获取子目标列表（含 detail 详情）
3. 根据子目标状态、detail 内容和当前对话上下文，AI 生成进展摘要
4. 生成进展报告格式：

---
### 📊 进展更新 ({当前日期时间})
完成度: {done}/{total} ({百分比}%)

| 子目标 | 状态 | 进展 |
|--------|------|------|
| {name} | ✅ 完成 | {detail 摘要或"已完成"} |
| {name} | 🔄 进行中 | {detail 摘要} |
| {name} | ⬜ 待办 | 未开始 |

**总任务进展：**
{AI 根据子目标完成比例 + 各子目标 detail + 对话上下文，生成总任务整体进展描述（2-3句），包括：当前阶段判断、关键进展、下一步重点}

5. 调用 MCP `append_task(task_id, progress_text)` 追加到任务页面
6. 在终端展示进展报告，并确认已保存到 Notion
