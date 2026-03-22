将一个任务标记为"完成"。

## 用法

```
/done <task_id 或任务名称关键词> [完成总结]
```

## 示例

```
/done abc123
/done 登录 bug 已修复，通过测试，等待部署
/done 需求文档 文档已提交，待 PM review
```

## 行为

1. 如果传入关键词，先 `search_tasks` 找到任务
2. 调用 `complete_task(task_id, summary)` 更新状态为"完成"
3. 如果有 summary，追加到任务页面 body
4. 输出确认信息：

```
✅ 已完成任务：修复登录 Bug
  完成时间：2026-03-21 18:00 UTC
  总结：已修复，通过测试，等待部署
  🔗 https://notion.so/...
```
