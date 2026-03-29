---
name: capture
description: 快速创建任务。触发：/capture, "创建任务", "新建任务"
---

快速创建一个新任务到工作流库。

## 用法

/capture <任务描述> [-p 项目] [-pri 优先级] [-d 截止日期]

## 示例

/capture 重构Notion MCP -p MCP改造 -d 2026-03-28
/capture 修复登录bug -pri 紧急
/capture 完成需求文档 -p 业务开发 -pri 高 -d 2026-04-01

## 行为

1. 解析用户输入，提取：
   - 任务名称（必填，位置参数）
   - `-p` 项目名称（可选）
   - `-pri` 优先级（可选，默认普通）
   - `-d` 截止日期 YYYY-MM-DD（可选）
2. 优先级关键词识别：
   - 紧急 / urgent / ASAP → 🔴 紧急
   - 高 / high → 🟡 高
   - 普通 / normal（默认）→ 🟢 普通
3. 调用 MCP `create_task(name, project, priority, due_date)` 创建任务
4. 输出格式：

✅ 已创建任务「{名称}」
   ID: {task_id}
   项目: {项目} | 优先级: {优先级} | 截止: {日期}
   💡 用 /subtask {task_id} <名称> 添加子目标
