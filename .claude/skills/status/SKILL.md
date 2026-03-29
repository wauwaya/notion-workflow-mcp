---
name: status
description: 切换任务或子目标状态。触发：/status, "改状态", "标记完成", "开始做"
---

切换任务状态或子目标状态。

## 用法

```
/status <task_id> <状态>                  # 修改任务状态
/status <task_id> <状态> <子目标名称>      # 修改子目标状态
```

## 示例

```
/status abc123 进行中                     # 任务 → 进行中
/status abc123 完成                       # 任务 → 完成
/status abc123 doing 去掉关联功能          # 子目标 → doing
/status abc123 done 去掉关联功能           # 子目标 → done
```

## 行为

### 判断模式

- 有子目标名称参数 → 子目标状态修改
- 无子目标名称参数 → 任务状态修改

### 任务状态修改

1. 校验状态值，仅允许：`待办` / `进行中` / `完成` / `搁置`
   - 不合法 → 报错：`❌ 无效状态「{输入}」，允许值：待办 / 进行中 / 完成 / 搁置`
2. 调用 MCP `update_task(task_id, status=状态)` 修改
3. 输出：

✅ 任务「{任务名}」→ {新状态}

### 子目标状态修改

1. 校验状态值，仅允许：`todo` / `doing` / `done`
   - 不合法 → 报错：`❌ 无效子目标状态「{输入}」，允许值：todo / doing / done`
2. 调用 MCP `get_subtasks(task_id)` 获取子目标列表
3. 模糊匹配子目标名称（大小写不敏感的子串匹配）：
   - 0 个匹配 → 报错，列出所有子目标名称供选择
   - 多个匹配 → 列出匹配项，请用户输入更精确名称
   - 1 个匹配 → 继续
4. 调用 MCP `update_subtask_status(task_id, subtask_name, status)` 原子更新
5. 如果目标状态是 doing：
   - 调用 MCP `get_task(task_id)` 检查任务状态
   - 仅当任务状态为"待办"时，才调用 MCP `update_task(task_id, status=进行中)`
6. 输出：

✅「{子目标名}」→ {🔄 进行中/✅ 完成}
任务「{任务名}」进度: {done_count}/{total} 完成

7. 如果所有子目标都 done，提示：

🎉 所有子目标已完成！是否将任务「{任务名}」标记为完成？

如果用户确认，调用 MCP `update_task(task_id, status=完成)`。
