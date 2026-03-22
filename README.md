# notion-workflow-mcp

Personal workflow management via **Claude CLI + Notion API**, built as an MCP Server.

Inspired by [google-keep-mcp](https://github.com/staryxchen/google-keep-mcp) — turns Notion into a personal task and knowledge system driven by slash commands.

## Features

- **20 MCP tools** covering task lifecycle, note-taking, subtask management, and aggregations
- **2 independent Notion databases**: 工作流库 (tasks, with project & subtasks) + 笔记库 (notes)
- **12 slash commands**: `/capture`, `/subtask`, `/task_list`, `/status`, `/progress`, `/note`, `/review`, `/standup`, `/overview`, `/detail`, `/done`, `/find`
- **Project-based task management**: tasks belong to projects, with embedded subtasks (priority + status)
- **Conversation-to-note**: `/note` auto-summarizes AI conversations into structured notes

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

This auto-adds all required properties (状态, 优先级, 项目, 截止日期, 标签, 备注) to your existing databases.

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

### 6. Install slash command skills

Slash commands (like `/capture`, `/note`, `/review`) are Claude Code skills defined in `.claude/commands/`. They need to be accessible from your working directory.

**Option A: Work inside this project directory**

If you run `claude` from the `notion-workflow-mcp/` directory, skills are automatically available — Claude Code reads `.claude/commands/` from the current directory.

**Option B: Make skills globally available**

To use the slash commands from **any directory**, copy them to your global Claude Code commands folder:

```bash
# Create global commands dir if it doesn't exist
mkdir -p ~/.claude/commands

# Copy all skills
cp notion-workflow-mcp/.claude/commands/*.md ~/.claude/commands/
```

**Option C: Symlink (auto-sync with updates)**

```bash
mkdir -p ~/.claude/commands
ln -sf $(pwd)/notion-workflow-mcp/.claude/commands/*.md ~/.claude/commands/
```

After installation, restart Claude CLI. Verify by typing `/capture` — it should be recognized as a slash command.

## Workflow

```
# 1. Create a task under a project
/capture 重构Notion MCP -p MCP改造 -d 2026-03-28

# 2. Add subtasks
/subtask abc123 去掉关联功能 -pri 高
/subtask abc123 增加项目字段 -pri 紧急
/subtask abc123 创建skill

# 3. View all incomplete tasks
/task_list

# 4. Start working on a subtask
/status abc123 doing 去掉关联功能

# 5. Ask AI a question, then save the answer as a note
> Go 的 context 包怎么用？
> [AI explains...]
/note

# 6. Mark subtask done
/status abc123 done 去掉关联功能

# 7. Update progress
/progress abc123

# 8. End of day review
/review today

# 9. Friday weekly report
/review this week
```

## MCP Tools

| Group | Tools |
|---|---|
| Workflow | `list_tasks` `get_task` `create_task` `update_task` `start_task` `complete_task` `append_task` `search_tasks` |
| Subtasks | `get_subtasks` `update_subtasks` `update_subtask_detail` |
| Notes | `list_notes` `get_note` `create_note` `append_note` `search_notes` |
| Aggregations | `get_overview` `get_today_tasks` `generate_standup` `generate_review` |

## Slash Commands

| Command | Description |
|---|---|
| `/capture <task> [-p project] [-pri priority] [-d date]` | Quick-create a task |
| `/subtask <task_id> <name> [-pri priority]` | Add a subtask to a task |
| `/task_list [-p project] [-s status]` | View incomplete tasks grouped by project |
| `/status <task_id> <状态> [子目标名]` | Change task or subtask status |
| `/progress <task_id>` | Summarize & save progress to Notion |
| `/note` | Summarize current conversation into a note |
| `/review [时间范围]` | Review report (today/yesterday/this week/last week/date range) |
| `/standup` | Daily standup (yesterday done / today plan / blockers) |
| `/overview` | Task status dashboard |
| `/detail <task_id> <子目标名>` | Update subtask detail description |
| `/done <task_id>` | Mark a task as completed |
| `/find <keyword>` | Search tasks and notes |

## Database Schema

**工作流库 (Tasks)**
`名称` · `状态` · `优先级` · `项目` · `截止日期` · `标签` · `备注`

Subtasks are embedded in the task page body as structured Markdown:
```markdown
## 子目标
- [ ] 待办子目标 (🟢 普通)
- [~] 进行中子目标 (🟡 高)
- [x] 已完成子目标 (🔴 紧急)
```

**笔记库 (Notes)**
`名称` · `类型` · `标签`

## Notes

- Built against **notion-client 3.0** (`data_sources.*` API)
- Two databases are **independent** — no bidirectional relation between tasks and notes
- Subtasks use three states: `[ ]` todo, `[~]` doing, `[x]` done
