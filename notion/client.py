"""
Notion API client — low-level wrapper around notion-client SDK v3.
Handles all direct communication with Notion for both data sources.

notion-client 3.0 changes:
  - databases.query()  → data_sources.query()
  - databases.retrieve() → data_sources.retrieve()
  - databases.update()   → data_sources.update()
  - search filter value  → "page" or "data_source" (not "database")
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from dotenv import load_dotenv
from notion_client import Client

from notion.models import (
    Note,
    NoteCreate,
    NoteType,
    Subtask,
    SubtaskStatus,
    Task,
    TaskCreate,
    TaskOverview,
    TaskPriority,
    TaskStatus,
    TaskUpdate,
)

load_dotenv()


class NotionClient:
    """Thin wrapper around notion-client that speaks Task/Note domain objects."""

    def __init__(self) -> None:
        token = os.getenv("NOTION_TOKEN")
        if not token:
            raise ValueError("NOTION_TOKEN is not set. Copy .env.example to .env and fill it in.")

        self.client = Client(auth=token)
        self.workflow_db_id = os.getenv("WORKFLOW_DATABASE_ID", "")
        self.notes_db_id = os.getenv("NOTES_DATABASE_ID", "")

        if not self.workflow_db_id or not self.notes_db_id:
            raise ValueError(
                "WORKFLOW_DATABASE_ID and NOTES_DATABASE_ID must be set in .env"
            )

    # Subtask Markdown format regex (class-level constants)
    _SUBTASK_RE = re.compile(
        r'^- \[( |~|x)\] (.+?)(?:\s*\((🔴 紧急|🟡 高|🟢 普通)\))?\s*$'
    )
    _SUBTASK_STATUS_MAP = {" ": SubtaskStatus.TODO, "~": SubtaskStatus.DOING, "x": SubtaskStatus.DONE}
    _SUBTASK_STATUS_CHAR = {SubtaskStatus.TODO: " ", SubtaskStatus.DOING: "~", SubtaskStatus.DONE: "x"}

    # ------------------------------------------------------------------
    # Internal helpers: Notion response → domain model
    # ------------------------------------------------------------------

    def _parse_task(self, page: dict) -> Task:
        props = page["properties"]

        def _select(key: str) -> Optional[str]:
            val = props.get(key, {}).get("select")
            return val["name"] if val else None

        def _multi_select(key: str) -> list[str]:
            items = props.get(key, {}).get("multi_select", [])
            return [i["name"] for i in items]

        def _date(key: str) -> Optional[str]:
            val = props.get(key, {}).get("date")
            return val["start"] if val else None

        def _rich_text(key: str) -> Optional[str]:
            items = props.get(key, {}).get("rich_text", [])
            return "".join(i["plain_text"] for i in items) if items else None

        def _title() -> str:
            items = props.get("名称", {}).get("title", [])
            return "".join(i["plain_text"] for i in items)

        status_raw = _select("状态")
        priority_raw = _select("优先级")

        last_edited_raw = page.get("last_edited_time")
        last_edited_time = (
            datetime.fromisoformat(last_edited_raw.replace("Z", "+00:00"))
            if last_edited_raw else None
        )

        return Task(
            id=page["id"],
            name=_title(),
            status=TaskStatus(status_raw) if status_raw else TaskStatus.TODO,
            priority=TaskPriority(priority_raw) if priority_raw else TaskPriority.NORMAL,
            project=_select("项目"),
            due_date=_date("截止日期"),
            tags=_multi_select("标签"),
            note=_rich_text("备注"),
            created_time=datetime.fromisoformat(page["created_time"].replace("Z", "+00:00")),
            last_edited_time=last_edited_time,
            url=page.get("url"),
        )

    def _parse_note(self, page: dict) -> Note:
        props = page["properties"]

        def _select(key: str) -> Optional[str]:
            val = props.get(key, {}).get("select")
            return val["name"] if val else None

        def _multi_select(key: str) -> list[str]:
            items = props.get(key, {}).get("multi_select", [])
            return [i["name"] for i in items]

        def _title() -> str:
            items = props.get("名称", {}).get("title", [])
            return "".join(i["plain_text"] for i in items)

        type_raw = _select("类型")

        return Note(
            id=page["id"],
            title=_title(),
            type=NoteType(type_raw) if type_raw else NoteType.QUICK,
            tags=_multi_select("标签"),
            created_time=datetime.fromisoformat(page["created_time"].replace("Z", "+00:00")),
            url=page.get("url"),
        )

    # ------------------------------------------------------------------
    # Internal helpers: domain model → Notion properties payload
    # ------------------------------------------------------------------

    def _task_properties(
        self,
        name: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        project: Optional[str] = None,
        due_date: Optional[str] = None,
        tags: Optional[list[str]] = None,
        note: Optional[str] = None,
    ) -> dict:
        props: dict[str, Any] = {}

        if name is not None:
            props["名称"] = {"title": [{"text": {"content": name}}]}
        if status is not None:
            props["状态"] = {"select": {"name": status.value}}
        if priority is not None:
            props["优先级"] = {"select": {"name": priority.value}}
        if project is not None:
            props["项目"] = {"select": {"name": project}}
        if due_date is not None:
            props["截止日期"] = {"date": {"start": due_date}}
        if tags is not None:
            props["标签"] = {"multi_select": [{"name": t} for t in tags]}
        if note is not None:
            props["备注"] = {"rich_text": [{"text": {"content": note}}]}

        return props

    def _note_properties(
        self,
        title: Optional[str] = None,
        note_type: Optional[NoteType] = None,
        tags: Optional[list[str]] = None,
    ) -> dict:
        props: dict[str, Any] = {}

        if title is not None:
            props["名称"] = {"title": [{"text": {"content": title}}]}
        if note_type is not None:
            props["类型"] = {"select": {"name": note_type.value}}
        if tags is not None:
            props["标签"] = {"multi_select": [{"name": t} for t in tags]}

        return props

    @staticmethod
    def _text_block(content: str) -> dict:
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": content}}]
            },
        }

    # ------------------------------------------------------------------
    # Task CRUD (uses data_sources.query — notion-client 3.0)
    # ------------------------------------------------------------------

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        tag: Optional[str] = None,
        project: Optional[str] = None,
        limit: int = 20,
    ) -> list[Task]:
        filters: list[dict] = []

        if status:
            filters.append({
                "property": "状态",
                "select": {"equals": status.value},
            })
        if priority:
            filters.append({
                "property": "优先级",
                "select": {"equals": priority.value},
            })
        if tag:
            filters.append({
                "property": "标签",
                "multi_select": {"contains": tag},
            })
        if project:
            filters.append({
                "property": "项目",
                "select": {"equals": project},
            })

        query_params: dict[str, Any] = {
            "data_source_id": self.workflow_db_id,
            "page_size": min(limit, 100),
            "sorts": [
                {"property": "状态", "direction": "ascending"},
                {"timestamp": "created_time", "direction": "descending"},
            ],
        }
        if filters:
            query_params["filter"] = (
                {"and": filters} if len(filters) > 1 else filters[0]
            )

        response = self.client.data_sources.query(**query_params)
        return [self._parse_task(p) for p in response["results"]]

    def get_task(self, task_id: str) -> Task:
        page = self.client.pages.retrieve(page_id=task_id)
        return self._parse_task(page)

    def create_task(self, data: TaskCreate) -> Task:
        props = self._task_properties(
            name=data.name,
            status=TaskStatus.TODO,
            priority=data.priority,
            project=data.project,
            due_date=data.due_date,
            tags=data.tags,
            note=data.note,
        )
        page = self.client.pages.create(
            parent={"data_source_id": self.workflow_db_id},
            properties=props,
        )
        return self._parse_task(page)

    def update_task(self, task_id: str, data: TaskUpdate) -> Task:
        props = self._task_properties(
            status=data.status,
            priority=data.priority,
            project=data.project,
            due_date=data.due_date,
            tags=data.tags,
            note=data.note,
        )
        page = self.client.pages.update(page_id=task_id, properties=props)
        return self._parse_task(page)

    def append_task_body(self, task_id: str, content: str) -> None:
        """Append a paragraph block to a task page body."""
        self.client.blocks.children.append(
            block_id=task_id,
            children=[self._text_block(content)],
        )

    def _find_subtask_section(self, blocks: list[dict]) -> tuple[int | None, int | None]:
        """Find the ## 子目标 section boundaries in a list of blocks.

        Returns:
            (start_idx, end_idx) — start is the heading_2 block index,
            end is the next heading_2 index (exclusive) or None if section
            extends to the end of blocks. Both None if section not found.
        """
        start: int | None = None
        end: int | None = None
        for i, block in enumerate(blocks):
            if block.get("type") == "heading_2":
                text = "".join(
                    t["plain_text"]
                    for t in block.get("heading_2", {}).get("rich_text", [])
                )
                if text.strip() == "子目标":
                    start = i
                elif start is not None and end is None:
                    end = i
                    break
        return start, end

    def get_subtasks(self, task_id: str) -> list[Subtask]:
        """Parse subtasks from the ## 子目标 section in a task page body."""
        blocks = self._get_all_child_blocks(task_id)
        start, end = self._find_subtask_section(blocks)
        if start is None:
            return []

        section = blocks[start + 1 : end]  # skip heading itself
        subtasks: list[Subtask] = []
        for block in section:
            if block.get("type") != "paragraph":
                continue
            rich_text = block.get("paragraph", {}).get("rich_text", [])
            text = "".join(t["plain_text"] for t in rich_text)
            m = self._SUBTASK_RE.match(text)
            if m:
                status_char, name, priority_str = m.group(1), m.group(2), m.group(3)
                status = self._SUBTASK_STATUS_MAP.get(status_char, SubtaskStatus.TODO)
                priority = TaskPriority(priority_str) if priority_str else TaskPriority.NORMAL
                subtasks.append(Subtask(name=name, status=status, priority=priority))
        return subtasks

    def update_subtasks(self, task_id: str, subtasks: list[Subtask]) -> list[Subtask]:
        """Rewrite the ## 子目标 section in the task page body."""
        blocks = self._get_all_child_blocks(task_id)
        start, end = self._find_subtask_section(blocks)

        # Delete old section blocks (heading + content within boundaries)
        if start is not None:
            section_end = end if end is not None else len(blocks)
            for block in blocks[start:section_end]:
                self.client.blocks.delete(block_id=block["id"])

        # Build new blocks: heading + subtask lines
        new_children: list[dict] = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "子目标"}}]
                },
            },
        ]
        for st in subtasks:
            status_char = self._SUBTASK_STATUS_CHAR[st.status]
            line = f"- [{status_char}] {st.name} ({st.priority.value})"
            new_children.append(self._text_block(line))

        # Insert at the old position, or append if first time
        if start is not None and start > 0:
            before_block_id = blocks[start - 1]["id"]
            self.client.blocks.children.append(
                block_id=task_id,
                children=new_children,
                after=before_block_id,
            )
        else:
            self.client.blocks.children.append(
                block_id=task_id,
                children=new_children,
            )

        return subtasks

    def _get_all_child_blocks(self, block_id: str) -> list[dict]:
        """Retrieve all child blocks of a page/block, handling pagination."""
        results: list[dict] = []
        resp = self.client.blocks.children.list(block_id=block_id, page_size=100)
        results.extend(resp["results"])
        while resp.get("has_more"):
            resp = self.client.blocks.children.list(
                block_id=block_id,
                page_size=100,
                start_cursor=resp["next_cursor"],
            )
            results.extend(resp["results"])
        return results

    def search_tasks(self, query: str) -> list[Task]:
        response = self.client.search(
            query=query,
            filter={"value": "page", "property": "object"},
            page_size=20,
        )
        tasks = []
        for page in response["results"]:
            parent = page.get("parent", {})
            parent_id = (
                parent.get("data_source_id") or parent.get("database_id", "")
            ).replace("-", "")
            if parent_id == self.workflow_db_id.replace("-", ""):
                tasks.append(self._parse_task(page))
        return tasks

    def get_today_tasks(self) -> list[Task]:
        today = datetime.now(timezone.utc).date().isoformat()
        tomorrow = (datetime.now(timezone.utc).date() + timedelta(days=1)).isoformat()

        response = self.client.data_sources.query(
            data_source_id=self.workflow_db_id,
            filter={
                "or": [
                    {
                        "property": "状态",
                        "select": {"equals": TaskStatus.IN_PROGRESS.value},
                    },
                    {
                        "and": [
                            {"property": "截止日期", "date": {"on_or_after": today}},
                            {"property": "截止日期", "date": {"before": tomorrow}},
                        ]
                    },
                ]
            },
            sorts=[{"property": "优先级", "direction": "ascending"}],
            page_size=30,
        )
        return [self._parse_task(p) for p in response["results"]]

    def get_task_overview(self) -> TaskOverview:
        counts: dict[str, int] = {}
        for status in TaskStatus:
            resp = self.client.data_sources.query(
                data_source_id=self.workflow_db_id,
                filter={"property": "状态", "select": {"equals": status.value}},
                page_size=100,
            )
            total = len(resp["results"])
            while resp.get("has_more"):
                resp = self.client.data_sources.query(
                    data_source_id=self.workflow_db_id,
                    filter={"property": "状态", "select": {"equals": status.value}},
                    start_cursor=resp["next_cursor"],
                    page_size=100,
                )
                total += len(resp["results"])
            counts[status.value] = total

        return TaskOverview(
            todo=counts.get(TaskStatus.TODO.value, 0),
            in_progress=counts.get(TaskStatus.IN_PROGRESS.value, 0),
            done=counts.get(TaskStatus.DONE.value, 0),
            on_hold=counts.get(TaskStatus.ON_HOLD.value, 0),
            total=sum(counts.values()),
        )

    # ------------------------------------------------------------------
    # Note CRUD
    # ------------------------------------------------------------------

    def list_notes(
        self,
        note_type: Optional[NoteType] = None,
        tag: Optional[str] = None,
        limit: int = 20,
    ) -> list[Note]:
        filters: list[dict] = []

        if note_type:
            filters.append({
                "property": "类型",
                "select": {"equals": note_type.value},
            })
        if tag:
            filters.append({
                "property": "标签",
                "multi_select": {"contains": tag},
            })

        query_params: dict[str, Any] = {
            "data_source_id": self.notes_db_id,
            "page_size": min(limit, 100),
            "sorts": [{"timestamp": "created_time", "direction": "descending"}],
        }
        if filters:
            query_params["filter"] = (
                {"and": filters} if len(filters) > 1 else filters[0]
            )

        response = self.client.data_sources.query(**query_params)
        return [self._parse_note(p) for p in response["results"]]

    def get_note(self, note_id: str) -> Note:
        page = self.client.pages.retrieve(page_id=note_id)
        return self._parse_note(page)

    def get_note_content(self, note_id: str) -> str:
        """Retrieve the full plain-text content of a note page body."""
        blocks = self.client.blocks.children.list(block_id=note_id)
        lines: list[str] = []
        for block in blocks["results"]:
            block_type = block["type"]
            rich_text = block.get(block_type, {}).get("rich_text", [])
            text = "".join(t["plain_text"] for t in rich_text)
            if text:
                lines.append(text)
        return "\n".join(lines)

    def create_note(self, data: NoteCreate) -> Note:
        props = self._note_properties(
            title=data.title,
            note_type=data.type,
            tags=data.tags,
        )
        children = [self._text_block(data.content)] if data.content else []
        page = self.client.pages.create(
            parent={"data_source_id": self.notes_db_id},
            properties=props,
            children=children,
        )
        return self._parse_note(page)

    def append_note_content(self, note_id: str, content: str) -> None:
        """Append a paragraph block to a note page body."""
        self.client.blocks.children.append(
            block_id=note_id,
            children=[self._text_block(content)],
        )

    def search_notes(self, query: str) -> list[Note]:
        response = self.client.search(
            query=query,
            filter={"value": "page", "property": "object"},
            page_size=20,
        )
        notes = []
        for page in response["results"]:
            parent = page.get("parent", {})
            parent_id = (
                parent.get("data_source_id") or parent.get("database_id", "")
            ).replace("-", "")
            if parent_id == self.notes_db_id.replace("-", ""):
                notes.append(self._parse_note(page))
        return notes
