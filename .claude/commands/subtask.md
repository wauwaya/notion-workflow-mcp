给任务添加一个子目标。

## 用法

/subtask <task_id> <子目标名称> [-pri 优先级] [-desc 详情描述]

## 示例

/subtask abc123 去掉关联功能 -pri 高
/subtask abc123 增加项目字段 -pri 紧急
/subtask abc123 创建skill
/subtask abc123 方案设计 -desc "需要评审整体架构方案"

## 行为

1. 解析参数：task_id、子目标名称、优先级（默认 🟢 普通）、detail（可选）
2. 调用 MCP `get_subtasks(task_id)` 获取现有子目标列表
3. 将新子目标追加到列表末尾：`{name, status: "todo", priority, detail}`
4. 调用 MCP `update_subtasks(task_id, updated_list)` 写回
5. 输出当前所有子目标（表格格式）：

✅ 已添加子目标「{名称}」({优先级}) 到任务「{任务名}」
当前子目标:
| 子目标 | 优先级 | 状态 |
|--------|--------|------|
| 去掉关联功能 | 🟡 高 | ⬜ 待办 |
| 增加项目字段 | 🔴 紧急 | ⬜ 待办 |
| 创建skill | 🟢 普通 | ⬜ 待办 |
