切换任务的子目标状态。

## 用法

/status <task_id> <doing|done> <子目标名称>

## 示例

/status abc123 doing 去掉关联功能
/status abc123 done 去掉关联功能

## 行为

1. 调用 MCP `get_subtasks(task_id)` 获取子目标列表
2. 模糊匹配子目标名称（大小写不敏感的子串匹配）：
   - 0 个匹配 → 报错，列出所有子目标名称供选择
   - 多个匹配 → 列出匹配项，请用户输入更精确名称
   - 1 个匹配 → 继续
3. 更新匹配到的子目标状态为 doing 或 done
4. 调用 MCP `update_subtasks(task_id, updated_list)` 写回
5. 如果目标状态是 doing：
   - 调用 MCP `get_task(task_id)` 检查任务状态
   - 仅当任务状态为"待办"时，才调用 MCP `start_task(task_id)`
6. 输出：

✅「{子目标名}」→ {🔄 进行中/✅ 完成}
任务「{任务名}」进度: {done_count}/{total} 完成

7. 如果所有子目标都 done，提示：

🎉 所有子目标已完成！是否将任务「{任务名}」标记为完成？

如果用户确认，调用 MCP `complete_task(task_id)`。
