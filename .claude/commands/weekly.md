生成本周工作进展汇总，按项目分组。

## 用法

/weekly

## 行为

1. 调用 MCP `list_tasks(status="完成")` 获取已完成任务，筛选 `last_edited_time` 在本周（周一至今天）的
2. 调用 MCP `list_tasks(status="进行中")` 获取进行中任务
3. 调用 MCP `list_tasks(status="待办")` 获取待办任务
4. 对相关任务调用 MCP `get_subtasks(task_id)` 获取子目标
5. 按项目分组，生成周报：

📊 {年}-W{周数} 周报

## 本周完成
### 项目: {项目名}
- {任务名}: 完成了 {子目标列表}

## 进行中
### 项目: {项目名}
- {任务名} ({done_count}/{total})
  - [~] 进行中子目标
  - [ ] 待办子目标

## 统计
- 本周完成任务: {n} 项
- 进行中任务: {n} 项
- 新增任务: {n} 项

6. 询问用户选择输出方式（同 /daily）：
   - 「仅终端显示」
   - 「保存到 Notion」— 调用 `create_note(title="周报 {年}-W{周数}", content, note_type="速记", tags=["周报"])`
   - 「两者都要」
