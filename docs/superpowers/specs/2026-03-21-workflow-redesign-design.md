# Notion Workflow MCP 改造设计文档

## 概述

改造现有 `notion-workflow-mcp` 系统，实现两个核心目标：
1. **MCP 端**：简化数据模型（去掉笔记-任务关联），增加项目和子目标管理能力
2. **Skill 端**：创建 8 个 Claude Code skill，提供流畅的命令行工作流

## 设计决策

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 子目标存储 | 嵌套在任务页面 body（结构化 Markdown） | 不需要新数据库，简单直接 |
| 项目字段 | 工作流库 Select 字段 | 轻量，支持按项目筛选 |
| 笔记-任务关联 | 删除 | 两个库独立运作，降低复杂度 |
| 命令交互 | Skill 编排 MCP 工具调用 | MCP 负责数据，skill 负责交互流程 |
| 汇总输出 | 用户自选（终端 / 保存 Notion / 两者） | 灵活适配不同场景 |
| 子目标 Notion 存储 | `paragraph` blocks（原始 Markdown 文本） | 唯一支持三态 `[ ]/[~]/[x]` 的方案，`to_do` blocks 只有 checked bool 无法表达"进行中" |
| 关联字段迁移 | 代码侧删除，Notion 中保留（可手动归档） | Notion API 不易删属性，代码不读写即可 |
| Skill 文件位置 | 项目内 `.claude/commands/` | 与此 MCP 紧耦合，项目级 skill 更合理 |
| 聚合工具处理 | `tools/aggregations.py` 保留但更新 | 增加 project 分组支持，skill 可复用这些工具 |

---

## 第一部分：MCP 端改造

### 1.1 数据库 Schema 变更

#### 工作流库（任务）

**新增字段：**
- `项目` (select)：项目名称，可选值动态创建

**删除字段：**
- `关联笔记` (relation)：移除与笔记库的双向关联

**保留字段（不变）：**
- `名称` (title)、`状态` (select)、`优先级` (select)、`截止日期` (date)、`标签` (multi_select)、`备注` (rich_text)

#### 笔记库

**删除字段：**
- `关联任务` (relation)：移除与工作流库的双向关联

**保留字段（不变）：**
- `名称` (title)、`类型` (select)、`标签` (multi_select)

### 1.2 子目标 Markdown 格式

任务页面 body 中的子目标使用固定格式，便于解析。

**Notion block 类型**：使用 `heading_2` block + `paragraph` blocks（原始 Markdown 文本行）。选择 `paragraph` 而非 `to_do` blocks，因为 `to_do` 只有 `checked: bool`，无法表达"进行中"三态。

```markdown
## 子目标
- [ ] 去掉关联功能 (🔴 紧急)
- [~] 增加项目字段 (🟡 高)
- [x] 修复bug (🟢 普通)
```

状态约定：
- `[ ]` — 待办 (todo)
- `[~]` — 进行中 (doing)
- `[x]` — 已完成 (done)

优先级格式（emoji + 空格 + 文字，与任务优先级枚举一致）：
- `🔴 紧急`
- `🟡 高`
- `🟢 普通`（默认）

解析规则：
- 以 `## 子目标` 标题开始（Notion `heading_2` block，纯文本值为 `子目标`）
- 每行一个 `paragraph` block，格式：`- [状态] 名称 (优先级)`
- 优先级可选，默认 `🟢 普通`
- 子目标区块到下一个 `heading_2` block 或 blocks 末尾结束
- 解析正则：`r'^- \[( |~|x)\] (.+?)(?:\s*\((🔴 紧急|🟡 高|🟢 普通)\))?\s*$'`

**页面 body 布局约定**（block 顺序）：
1. `## 子目标` 区块 — 始终在最前面
2. 时间戳记录（`start_task` 的 `▶ 开始时间` 等）
3. 进展更新记录（`/progress` 追加的内容）

首次创建子目标时，在 body 最前面插入 `## 子目标` heading + subtask blocks。

### 1.3 工具变更

#### 删除的工具（2 个）

| 工具 | 原文件 |
|------|--------|
| `link_note_to_task` | `tools/relations.py` |
| `get_task_notes` | `tools/relations.py` |

删除 `tools/relations.py` 文件，从 `server.py` 移除注册。

#### 修改的工具（3 个）

**`create_task`** — 新增 `project` 参数
```python
def create_task(
    name: str,
    project: str | None = None,    # 新增
    priority: str = "🟢 普通",
    due_date: str | None = None,
    tags: list[str] | None = None,
    note: str | None = None,
) -> dict
```

**`update_task`** — 新增 `project` 参数
```python
def update_task(
    task_id: str,
    status: str | None = None,
    priority: str | None = None,
    due_date: str | None = None,
    tags: list[str] | None = None,
    note: str | None = None,
    project: str | None = None,     # 新增
) -> dict
```

**`list_tasks`** — 新增 `project` 筛选
```python
def list_tasks(
    status: str | None = None,
    priority: str | None = None,
    tag: str | None = None,
    project: str | None = None,     # 新增
    limit: int = 20,
) -> dict
```

#### 新增的工具（2 个）

**`get_subtasks(task_id: str) -> dict`**
- 读取任务页面 body，解析子目标 Markdown
- 返回结构化列表：`[{name, status, priority}]`
- status 枚举：`todo` / `doing` / `done`

**`update_subtasks(task_id: str, subtasks: list[dict]) -> dict`**
- 接收完整子目标列表，重写 body 中的子目标区块
- 保留 body 中子目标区块以外的内容（如进展记录、时间戳等）
- 输入格式：`[{name: str, status: str, priority: str}]`
- **替换算法**：
  1. 调用 `blocks.children.list(task_id)` 读取所有子 blocks（分页处理，每次最多 100）
  2. 定位子目标区块边界：从 `heading_2` text=`子目标` 的 block 开始，到下一个 `heading_2` block 或 blocks 末尾
  3. 逐个删除该范围内的所有 blocks（`blocks.delete(block_id)`）
  4. 在原位置插入新的 `heading_2` block + `paragraph` blocks（`blocks.children.append(task_id, children=[...])`，使用 `after` 参数定位插入点）
  5. 若 `## 子目标` 区块不存在（首次创建），在 body 最前面插入（`blocks.children.append(task_id, children=[...])`，不指定 `after`）

### 1.4 模型变更

#### `models.py`

**Task 模型新增字段：**
```python
class Task(BaseModel):
    # ... 现有字段 ...
    project: str | None = None              # 新增
    last_edited_time: str | None = None     # 新增，用于 /daily 筛选今日完成任务
    subtasks: list[Subtask] | None = None   # 新增，仅 get_subtasks 返回时填充

class Subtask(BaseModel):
    name: str
    status: str   # "todo" | "doing" | "done"
    priority: str  # "🔴 紧急" | "🟡 高" | "🟢 普通"
```

**TaskCreate / TaskUpdate 新增 project 字段：**
```python
class TaskCreate(BaseModel):
    name: str
    project: str | None = None   # 新增
    # ... 其余不变 ...

class TaskUpdate(BaseModel):
    project: str | None = None   # 新增
    # ... 其余不变 ...
```

**Note 模型删除关联字段：**
```python
class Note(BaseModel):
    # 删除: linked_task_ids
    # 其余不变

class NoteCreate(BaseModel):
    # 删除: task_id
    # 其余不变
```

### 1.5 client.py 变更

- `_parse_task()`：新增解析 `项目` 字段逻辑，新增解析 `last_edited_time`
- `_build_task_properties()`：新增构建 `项目` Select 属性
- `_build_task_filter()`：新增 `project` 筛选条件
- 新增 `get_subtasks(task_id)`：读取页面 body blocks → 解析 Markdown → 返回 `list[Subtask]`
- 新增 `update_subtasks(task_id, subtasks)`：读取页面 body → 替换子目标区块 → 写回
- 删除 `link_note_to_task()` 方法
- 删除 `get_task_notes()` 方法
- `_parse_note()`：移除 `linked_task_ids` 解析
- `create_note()`：移除 `task_id` 参数和自动关联逻辑

### 1.6 init_databases.py 变更

- 工作流库：新增 `项目` Select 属性创建
- 工作流库：删除 `关联笔记` relation 属性创建
- 笔记库：删除 `关联任务` relation 属性创建

---

## 第二部分：Skill 端设计

### 2.1 Skill 清单（8 个）

| Skill | 命令 | 功能 |
|-------|------|------|
| capture | `/capture <名称> [-p 项目] [-pri 优先级] [-d 日期]` | 快速创建任务 |
| subtask | `/subtask <task_id> <子目标名> [-pri 优先级]` | 给任务添加子目标 |
| task_list | `/task_list [-p 项目] [-s 状态]` | 查看未完成任务，按项目分组 |
| status | `/status <task_id> <doing\|done> <子目标名>` | 切换子目标状态 |
| progress | `/progress <task_id>` | 汇总任务当前进度，更新到 Notion |
| note | `/note` | 汇总当前对话，选标签，保存笔记 |
| daily | `/daily` | 今日各项目进展汇总 |
| weekly | `/weekly` | 本周各项目进展汇总 |

### 2.2 各 Skill 详细设计

#### `/capture` — 快速创建任务

**触发**：用户输入 `/capture`
**参数解析**：
- 位置参数：任务名称（必填）
- `-p`：项目名称
- `-pri`：优先级（紧急/高/普通，默认普通）
- `-d`：截止日期（YYYY-MM-DD）

**流程**：
1. 解析参数
2. 调用 MCP `create_task(name, project, priority, due_date)`
3. 输出创建结果，提示用 `/subtask` 添加子目标

**示例**：
```
你: /capture 重构Notion MCP -p MCP改造 -d 2026-03-28
AI: ✅ 已创建任务「重构Notion MCP」
    ID: abc123
    项目: MCP改造 | 优先级: 🟢普通 | 截止: 2026-03-28
    💡 用 /subtask abc123 <名称> 添加子目标
```

#### `/subtask` — 添加子目标

**触发**：用户输入 `/subtask`
**参数**：
- task_id（必填）
- 子目标名称（必填）
- `-pri`：优先级（默认普通）

**流程**：
1. 调用 MCP `get_subtasks(task_id)` 获取现有子目标
2. 追加新子目标到列表
3. 调用 MCP `update_subtasks(task_id, updated_list)`
4. 输出当前全部子目标

#### `/task_list` — 查看未完成任务

**触发**：用户输入 `/task_list`
**参数**：
- `-p`：按项目筛选（可选）
- `-s`：按状态筛选（可选）

**流程**：
1. 调用 MCP `list_tasks(status, project)` 获取任务列表（排除已完成）
2. 对每个任务调用 `get_subtasks(task_id)` 获取子目标（注：N 个任务需 N+1 次 API 调用，可能耗时数秒，skill 应提示"加载中..."）
3. 按项目分组渲染输出：
   - 项目名称作为二级标题
   - 每个任务显示名称、ID、优先级、截止日期
   - 缩进显示子目标及其状态

#### `/status` — 切换子目标状态

**触发**：用户输入 `/status`
**参数**：task_id, 目标状态 (doing/done), 子目标名称

**流程**：
1. 调用 MCP `get_subtasks(task_id)` 获取子目标列表
2. 模糊匹配子目标名称（大小写不敏感的子串匹配）
   - 0 个匹配：报错，列出所有子目标名称供用户选择
   - 多个匹配：列出匹配项，请用户输入更精确的名称
   - 1 个匹配：继续
3. 更新匹配到的子目标状态
4. 调用 MCP `update_subtasks(task_id, updated_list)`
5. 如果目标状态是 `doing`：先调用 `get_task(task_id)` 检查任务状态，仅当状态为 `待办` 时才调用 `start_task(task_id)`（避免重复追加开始时间戳）
6. 输出更新结果和当前进度（x/n 完成）
7. 如果所有子目标都 done，提示是否将任务整体标记为完成

#### `/progress` — 更新进展

**触发**：用户输入 `/progress`
**参数**：task_id

**流程**：
1. 调用 MCP `get_task(task_id)` 获取任务信息
2. 调用 MCP `get_subtasks(task_id)` 获取子目标
3. AI 根据子目标状态和当前对话上下文，生成进展摘要
4. 调用 MCP `append_task(task_id, progress_text)` 追加进展到任务页面

**追加格式**：
```markdown
---
### 📊 进展更新 (2026-03-21 15:30)
完成度: 1/3 (33%)
- [x] 去掉关联功能
- [~] 增加项目字段 — 正在实现 client.py 的改动
- [ ] 创建skill

今日进展: 完成了关联功能的移除，正在处理项目字段的 schema 变更。
```

#### `/note` — 汇总对话记笔记

**触发**：用户输入 `/note`

**流程**：
1. AI 回顾当前对话中最近的问答内容
2. 汇总为结构化笔记（标题 + 正文，Markdown 格式）
3. 展示汇总预览，用 AskUserQuestion 让用户选择标签（从常用标签中选或自定义）
4. 调用 MCP `create_note(title, content, note_type="速记", tags)`
5. 输出保存确认

#### `/daily` — 每日汇总

**触发**：用户输入 `/daily`

**流程**：
1. 调用 MCP `list_tasks()` 获取所有非完成任务（进行中 + 待办）
2. 调用 MCP `list_tasks(status="完成")` 获取已完成任务，通过 `last_edited_time >= 今日 00:00` 筛选今日完成的
3. 对相关任务调用 `get_subtasks` 获取子目标
4. 按项目分组，生成日报：
   - 今日完成的子目标
   - 进行中的子目标
   - 整体完成度
5. 用 AskUserQuestion 让用户选择输出方式：
   - `仅终端显示`：直接输出
   - `保存到 Notion`：调用 `create_note(title="日报 YYYY-MM-DD", content, note_type="速记", tags=["日报"])`
   - `两者都要`：终端输出 + 保存

#### `/weekly` — 每周汇总

**触发**：用户输入 `/weekly`

**流程**：与 `/daily` 类似，时间范围为本周（周一至今天），额外包含：
- 本周新增任务数
- 本周完成任务数
- 各项目进度对比
- 输出方式同 `/daily`（用户自选）

---

## 第三部分：文件变更清单

### MCP 端（`notion-workflow-mcp/`）

| 文件 | 操作 | 说明 |
|------|------|------|
| `notion/models.py` | 修改 | 新增 Subtask 模型、Task 加 project 字段、Note 删关联字段 |
| `notion/client.py` | 修改 | 新增 project 支持、新增子目标解析/更新、删除关联方法 |
| `tools/workflow.py` | 修改 | create_task/update_task/list_tasks 加 project 参数；新增 get_subtasks/update_subtasks |
| `tools/notes.py` | 修改 | create_note 移除 task_id 参数 |
| `tools/relations.py` | 删除 | 整个文件删除 |
| `tools/aggregations.py` | 修改 | generate_standup/generate_weekly_review 增加按 project 分组 |
| `server.py` | 修改 | 移除 relation 工具注册，新增 subtask 工具注册 |
| `scripts/init_databases.py` | 修改 | Schema 变更同步 |

### Skill 端（`notion-workflow-mcp/.claude/commands/`）

| 文件 | 操作 | 说明 |
|------|------|------|
| `capture.md` | 新建 | 快速创建任务 skill |
| `subtask.md` | 新建 | 添加子目标 skill |
| `task_list.md` | 新建 | 查看任务列表 skill |
| `status.md` | 新建 | 切换子目标状态 skill |
| `progress.md` | 新建 | 更新进展 skill |
| `note.md` | 新建/重写 | 汇总对话记笔记 skill |
| `daily.md` | 新建 | 每日汇总 skill |
| `weekly.md` | 新建 | 每周汇总 skill |

---

## 第四部分：用户工作流示例

```
# 1. 创建任务
/capture 重构Notion MCP -p MCP改造 -d 2026-03-28

# 2. 添加子目标
/subtask abc123 去掉关联功能 -pri 高
/subtask abc123 增加项目字段 -pri 紧急
/subtask abc123 创建skill

# 3. 查看所有待办
/task_list

# 4. 开始工作
/status abc123 doing 去掉关联功能

# 5. 工作中遇到问题，问 AI
> Go 的 context 包怎么用？
> [AI 解答...]
/note    # 汇总到笔记

# 6. 子目标完成
/status abc123 done 去掉关联功能

# 7. 更新进展
/progress abc123

# 8. 下班前
/daily   # 看今天干了啥

# 9. 周五
/weekly  # 看本周总结
```
