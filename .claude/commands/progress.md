汇总任务当前进度，追加到 Notion 任务页面。

## 用法

/progress <task_id>

## 行为

1. 调用 MCP `get_task(task_id)` 获取任务基本信息
2. 调用 MCP `get_subtasks(task_id)` 获取子目标列表
3. 根据子目标状态和当前对话上下文，AI 生成进展摘要
4. 生成进展报告格式：

---
### 📊 进展更新 ({当前日期时间})
完成度: {done}/{total} ({百分比}%)
- [x] 已完成子目标1
- [~] 进行中子目标2 — {具体进展描述}
- [ ] 待办子目标3

今日进展: {AI 根据对话上下文生成的 1-2 句总结}

5. 调用 MCP `append_task(task_id, progress_text)` 追加到任务页面
6. 在终端展示进展报告，并确认已保存到 Notion
