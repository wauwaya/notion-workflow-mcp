# notion-workflow-mcp

Personal workflow management via **Claude CLI + Notion API**, built as an MCP Server.

## Features

- **19 MCP tools** — task lifecycle, subtask management, note-taking, aggregations
- **12 skills** — slash commands + natural language triggers, globally installable
- **2 Notion databases** — 工作流库 (tasks) + 笔记库 (notes), independent
- **Project-based task management** — tasks belong to projects, with embedded subtasks (priority + status)
- **Conversation-to-note** — `/note` auto-summarizes AI conversations into structured notes
- **Ebbinghaus review** — `/recall` schedules spaced repetition based on note creation dates

## Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Notion account + Integration token

## Setup

### 1. Clone & install

```bash
git clone <repo-url>
cd notion-workflow-mcp
uv venv --python python3.12
uv pip install -e .
```

### 2. Configure environment

```bash
cp .env.example .env
# Fill in: NOTION_TOKEN, WORKFLOW_DATABASE_ID, NOTES_DATABASE_ID
```

- `NOTION_TOKEN`: [notion.so/my-integrations](https://www.notion.so/my-integrations) → New integration → copy token
- Database IDs: Open database in Notion → URL 中 `notion.so/<database_id>?v=...`

### 3. Share databases with Integration

In Notion: open each database → `...` → `Connections` → select your integration.

### 4. Initialize database schema

```bash
python scripts/init_databases.py
```

Auto-adds required properties (状态, 优先级, 项目, 截止日期, 标签, 备注) to existing databases.

### 5. Register MCP Server

```bash
claude mcp add notion-workflow -- /path/to/.venv/bin/python /path/to/server.py
```

Or add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "notion-workflow": {
      "command": "/path/to/notion-workflow-mcp/.venv/bin/python",
      "args": ["/path/to/notion-workflow-mcp/server.py"]
    }
  }
}
```

### 6. Install skills

Skills defined in `.claude/skills/` provide slash commands and natural language triggers. In-repo they're auto-discovered; to use from **any directory**, run:

```bash
bash scripts/install-skills.sh
```

This copies all skills to `~/.claude-internal/skills/`. Restart Claude Code session to take effect.

## Workflow

```
# Create a task
/capture 重构Notion MCP -p MCP改造 -d 2026-03-28

# Add subtasks
/subtask abc123 去掉关联功能 -pri 高
/subtask abc123 增加项目字段

# View tasks
/task_list

# Start working
/status abc123 doing 去掉关联功能

# Save conversation knowledge
/note

# Mark done
/status abc123 done 去掉关联功能

# Update progress
/progress abc123

# Daily standup
/standup

# Weekly review
/review this week

# Ebbinghaus review
/recall
```

## Skills

| Skill | Trigger | Description |
|---|---|---|
| `capture` | `/capture`, "创建任务" | Quick-create a task |
| `subtask-add` | `/subtask`, "添加子目标" | Add subtask to a task |
| `task-list` | `/task_list`, "任务列表" | View incomplete tasks by project |
| `status` | `/status`, "标记完成" | Change task/subtask status (atomic) |
| `detail` | `/detail`, "写进展" | Update subtask detail |
| `progress` | `/progress`, "汇总进展" | Summarize & save progress |
| `note` | `/note`, "记笔记" | Summarize conversation to note |
| `find` | `/find`, "搜索" | Search tasks and notes |
| `standup` | `/standup`, "站会" | Daily standup report |
| `review` | `/review`, "复盘" | Date-range review report |
| `recall` | `/recall`, "复习" | Ebbinghaus spaced repetition |
| `decompose-task` | `/decompose`, "拆解任务" | Extract task + subtasks from conversation |

## MCP Tools

| Group | Tools |
|---|---|
| Workflow | `list_tasks` `get_task` `create_task` `update_task` `append_task` `search_tasks` |
| Subtasks | `get_subtasks` `update_subtasks` `update_subtask_detail` `update_subtask_status` |
| Notes | `list_notes` `get_note` `create_note` `append_note` `search_notes` |
| Aggregations | `get_overview` `get_today_tasks` `generate_standup` `generate_review` |

## Database Schema

**工作流库 (Tasks)**
`名称` · `状态` · `优先级` · `项目` · `截止日期` · `标签` · `备注`

Subtasks are embedded in task page body as a table:

| 子目标 | 优先级 | 状态 |
|--------|--------|------|
| 功能A | 🟡 高 | ⬜ 待办 |
| 功能B | 🟢 普通 | 🔄 进行中 |
| 功能C | 🔴 紧急 | ✅ 完成 |

Each subtask can have a detail section (heading_3 + paragraphs) below the table.

**笔记库 (Notes)**
`名称` · `类型` (会议记录/想法/参考/速记) · `标签`

## Project Structure

```
├── server.py              # FastMCP server entry
├── notion/
│   ├── client.py          # Notion API client
│   └── models.py          # Pydantic models & enums
├── tools/
│   ├── workflow.py        # Task management tools
│   ├── notes.py           # Note tools
│   └── aggregations.py    # Standup, review, overview
├── .claude/skills/        # 12 skills (source of truth)
└── scripts/
    ├── init_databases.py  # Database schema setup
    └── install-skills.sh  # Install skills globally
```
