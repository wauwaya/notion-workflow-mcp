"""
Notion Workflow MCP Server
--------------------------
Personal workflow management via Claude CLI + Notion API.
"""

from __future__ import annotations

import fastmcp

from tools.aggregations import generate_review, generate_standup, get_overview, get_today_tasks
from tools.notes import append_note, create_note, get_note, list_notes, search_notes
from tools.workflow import (
    append_task,
    complete_task,
    create_task,
    get_subtasks,
    get_task,
    list_tasks,
    search_tasks,
    start_task,
    update_subtask_detail,
    update_subtasks,
    update_task,
)

mcp = fastmcp.FastMCP(
    name="notion-workflow",
    instructions=(
        "你是一个工作流管理助手，帮助用户通过 Notion 管理任务和笔记。\n"
        "工作流库用于追踪任务状态（支持项目分组和子目标管理），笔记库用于记录过程和想法。\n"
        "在没有明确 task_id 的情况下，先用 list_tasks 或 search_tasks 找到目标任务。"
    ),
)

# Workflow tools
mcp.tool(list_tasks)
mcp.tool(get_task)
mcp.tool(create_task)
mcp.tool(update_task)
mcp.tool(start_task)
mcp.tool(complete_task)
mcp.tool(append_task)
mcp.tool(search_tasks)
mcp.tool(get_subtasks)
mcp.tool(update_subtasks)
mcp.tool(update_subtask_detail)

# Notes tools
mcp.tool(list_notes)
mcp.tool(get_note)
mcp.tool(create_note)
mcp.tool(append_note)
mcp.tool(search_notes)

# Aggregation tools
mcp.tool(get_overview)
mcp.tool(get_today_tasks)
mcp.tool(generate_standup)
mcp.tool(generate_review)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
