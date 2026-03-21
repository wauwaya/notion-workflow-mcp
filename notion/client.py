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
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from dotenv import load_dotenv
from notion_client import Client

from notion.models import (
    Note,
    NoteCreate,
    NoteType,
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

        def _relations(key: str) -> list[str]:
            return [r["id"] for r in props.get(key, {}).get("relation", [])]

        status_raw = _select("状态")
        priority_raw = _select("优先级")

        return Task(
            id=page["id"],
            name=_title(),
            status=TaskStatus(status_raw) if status_raw else TaskStatus.TODO,
            priority=TaskPriority(priority_raw) if priority_raw else TaskPriority.NORMAL,
            due_date=_date("截止日期"),
            tags=_multi_select("标签"),
            note=_rich_text("备注"),
            linked_note_ids=_relations("关联笔记"),
            created_time=datetime.fromisoformat(page["created_time"].replace("Z", "+00:00")),
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

        def _relations(key: str) -> list[str]:
            return [r["id"] for r in props.get(key, {}).get("relation", [])]

        type_raw = _select("类型")

        return Note(
            id=page["id"],
            title=_title(),
            type=NoteType(type_raw) if type_raw else NoteType.QUICK,
            tags=_multi_select("标签"),
            linked_task_ids=_relations("关联任务"),
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
        note = self._parse_note(page)

        if data.task_id:
            self.link_note_to_task(note.id, data.task_id)

        return note

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

    # ------------------------------------------------------------------
    # Relations
    # ------------------------------------------------------------------

    def link_note_to_task(self, note_id: str, task_id: str) -> None:
        """Create a bidirectional relation between a note and a task."""
        note = self.get_note(note_id)
        existing_task_ids = note.linked_task_ids
        if task_id not in existing_task_ids:
            self.client.pages.update(
                page_id=note_id,
                properties={
                    "关联任务": {
                        "relation": [{"id": t} for t in existing_task_ids + [task_id]]
                    }
                },
            )

        task = self.get_task(task_id)
        existing_note_ids = task.linked_note_ids
        if note_id not in existing_note_ids:
            self.client.pages.update(
                page_id=task_id,
                properties={
                    "关联笔记": {
                        "relation": [{"id": n} for n in existing_note_ids + [note_id]]
                    }
                },
            )

    def get_task_notes(self, task_id: str) -> list[Note]:
        """Retrieve all notes linked to a task."""
        task = self.get_task(task_id)
        notes = []
        for note_id in task.linked_note_ids:
            try:
                notes.append(self.get_note(note_id))
            except Exception:
                pass
        return notes
