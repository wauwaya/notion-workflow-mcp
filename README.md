# notion-workflow-mcp

Personal workflow management via **Claude CLI + Notion API**, built as an MCP Server.

Inspired by [google-keep-mcp](https://github.com/staryxchen/google-keep-mcp) — turns Notion into a note-free personal task and knowledge system driven by slash commands.

## Features

- **18 MCP tools** covering task lifecycle, note-taking, relations, and aggregations
- **2 Notion databases**: 工作流库 (tasks) + 笔记库 (notes), bidirectionally linked
- **9 slash commands**: `/capture`, `/today`, `/start`, `/done`, `/note`, `/standup`, `/review`, `/find`, `/overview`

## Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Notion account + Integration token

## Setup

### 1. Clone & install

```bash
git clone https://github.com/<your-username>/notion-workflow-mcp
cd notion-workflow-mcp
uv venv --python python3.12
uv pip install -e .
```

### 2. Configure environment

```bash
cp .env.example .env
# Fill in your NOTION_TOKEN, WORKFLOW_DATABASE_ID, NOTES_DATABASE_ID
```

**Getting your IDs:**
- `NOTION_TOKEN`: [notion.so/my-integrations](https://www.notion.so/my-integrations) → New integration → copy token
- Database IDs: Use the init script to auto-discover them (see step 4)

### 3. Share databases with your Integration

In Notion: open each database → `...` → `Connections` → select your integration

### 4. Initialize database schema

```bash
python scripts/init_databases.py
```

This auto-adds all required properties (状态, 优先级, 截止日期, 标签, 备注, 关联笔记/任务) to your existing databases.

### 5. Register MCP Server with Claude CLI

```bash
claude mcp add notion-workflow -- /path/to/.venv/bin/python /path/to/server.py
```

Or add manually to `~/.claude/settings.json`:

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

Restart Claude CLI — the MCP server loads automatically.

## MCP Tools

| Group | Tools |
|---|---|
| Workflow | `list_tasks` `get_task` `create_task` `update_task` `start_task` `complete_task` `search_tasks` |
| Notes | `list_notes` `get_note` `create_note` `append_note` `search_notes` |
| Relations | `link_note_to_task` `get_task_notes` |
| Aggregations | `get_overview` `get_today_tasks` `generate_standup` `generate_weekly_review` |

## Slash Commands

| Command | Description |
|---|---|
| `/capture <task>` | Quick-capture a new task |
| `/today` | Today's due + in-progress tasks |
| `/start <task>` | Move task to in-progress |
| `/done <task> [summary]` | Complete a task with optional summary |
| `/note <content>` | Create a quick note |
| `/standup` | Generate daily standup report |
| `/review` | Weekly review |
| `/find <keyword>` | Search across tasks and notes |
| `/overview` | Task status dashboard |

## Database Schema

**工作流库 (Tasks)**
`名称` · `状态` · `优先级` · `截止日期` · `标签` · `备注` · `关联笔记`

**笔记库 (Notes)**
`名称` · `类型` · `标签` · `关联任务`

## Notes

- Built against **notion-client 3.0** (`data_sources.*` API)
- Notion database IDs in 3.0 differ from URL IDs — use `init_databases.py` to auto-discover correct IDs
