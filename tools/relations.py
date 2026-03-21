"""
Relations tools — bidirectional linking between 工作流库 and 笔记库.
"""

from __future__ import annotations

from typing import Optional

from notion.client import NotionClient

_client: Optional[NotionClient] = None


def get_client() -> NotionClient:
    global _client
    if _client is None:
        _client = NotionClient()
    return _client


def link_note_to_task(note_id: str, task_id: str) -> dict:
    """
    在笔记和任务之间建立双向关联。

    Args:
        note_id: 笔记的 Notion 页面 ID
        task_id: 任务的 Notion 页面 ID

    Returns:
        操作结果，包含 note_id 和 task_id
    """
    get_client().link_note_to_task(note_id, task_id)
    return {"success": True, "note_id": note_id, "task_id": task_id}


def get_task_notes(task_id: str) -> list[dict]:
    """
    获取一个任务下所有关联的笔记列表。

    Args:
        task_id: 任务的 Notion 页面 ID

    Returns:
        关联笔记列表（字典格式，不含 body 内容）
    """
    notes = get_client().get_task_notes(task_id)
    return [n.model_dump() for n in notes]
