给任务添加一个子目标。

## 用法

/subtask <task_id> <子目标名称> [-pri 优先级]

## 示例

/subtask abc123 去掉关联功能 -pri 高
/subtask abc123 增加项目字段 -pri 紧急
/subtask abc123 创建skill

## 行为

1. 解析参数：task_id、子目标名称、优先级（默认 🟢 普通）
2. 调用 MCP `get_subtasks(task_id)` 获取现有子目标列表
3. 将新子目标追加到列表末尾：`{name, status: "todo", priority}`
4. 调用 MCP `update_subtasks(task_id, updated_list)` 写回
5. 输出当前所有子目标：

✅ 已添加子目标「{名称}」({优先级}) 到任务「{任务名}」
当前子目标:
- [ ] 去掉关联功能 (🟡 高)
- [ ] 增加项目字段 (🔴 紧急)
- [ ] 创建skill (🟢 普通)
