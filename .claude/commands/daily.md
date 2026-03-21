生成今日工作进展汇总，按项目分组。

## 用法

/daily

## 行为

1. 调用 MCP `list_tasks(status="进行中")` 获取进行中任务
2. 调用 MCP `list_tasks(status="完成")` 获取已完成任务，筛选 `last_edited_time` 为今天的
3. 对相关任务调用 MCP `get_subtasks(task_id)` 获取子目标
4. 按项目分组，生成日报：

📊 {日期} 日报

### 项目: {项目名}
- {任务名} ({done_count}/{total})
  - [x] 已完成子目标
  - [~] 进行中子目标

### 项目: {项目名2}
- ...

5. 询问用户选择输出方式：
   - 「仅终端显示」— 仅在终端输出（默认）
   - 「保存到 Notion」— 调用 `create_note(title="日报 {日期}", content, note_type="速记", tags=["日报"])`
   - 「两者都要」— 终端输出 + 保存到 Notion
