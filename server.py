"""
Notion Workflow MCP Server
--------------------------
Personal workflow management via Claude CLI + Notion API.

Usage:
    python server.py

Or register in Claude config:
    claude mcp add notion-workflow -- python /path/to/server.py
"""

from __future__ import annotations

import fastmcp

from tools.aggregations import generate_standup, generate_weekly_review, get_overview, get_today_tasks
from tools.notes import append_note, create_note, get_note, list_notes, search_notes
from tools.relations import get_task_notes, link_note_to_task
from tools.workflow import (
    complete_task,
    create_task,
    get_task,
    list_tasks,
    search_tasks,
    start_task,
    update_task,
)

mcp = fastmcp.FastMCP(
    name="notion-workflow",
    instructions=(
        "你是一个工作流管理助手，帮助用户通过 Notion 管理任务和笔记。\n"
        "工作流库用于追踪任务状态，笔记库用于记录过程和想法。\n"
        "在没有明确 task_id 的情况下，先用 list_tasks 或 search_tasks 找到目标任务。"
    ),
)

# ---------------------------------------------------------------------------
# Register: Workflow tools
# ---------------------------------------------------------------------------
mcp.tool(list_tasks)
mcp.tool(get_task)
mcp.tool(create_task)
mcp.tool(update_task)
mcp.tool(start_task)
mcp.tool(complete_task)
mcp.tool(search_tasks)

# ---------------------------------------------------------------------------
# Register: Notes tools
# ---------------------------------------------------------------------------
mcp.tool(list_notes)
mcp.tool(get_note)
mcp.tool(create_note)
mcp.tool(append_note)
mcp.tool(search_notes)

# ---------------------------------------------------------------------------
# Register: Relations tools
# ---------------------------------------------------------------------------
mcp.tool(link_note_to_task)
mcp.tool(get_task_notes)

# ---------------------------------------------------------------------------
# Register: Aggregation tools
# ---------------------------------------------------------------------------
mcp.tool(get_overview)
mcp.tool(get_today_tasks)
mcp.tool(generate_standup)
mcp.tool(generate_weekly_review)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
