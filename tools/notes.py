"""
Notes tools — CRUD operations for 笔记库.
"""

from __future__ import annotations

from typing import Optional

from notion.client import NotionClient
from notion.models import NoteCreate, NoteType

_client: Optional[NotionClient] = None


def get_client() -> NotionClient:
    global _client
    if _client is None:
        _client = NotionClient()
    return _client


# ---------------------------------------------------------------------------
# list_notes
# ---------------------------------------------------------------------------

def list_notes(
    note_type: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    """
    列出笔记库中的笔记。

    Args:
        note_type: 按类型过滤，可选：会议记录 | 想法 | 参考 | 速记
        tag:       按标签过滤，精确匹配单个标签名称
        limit:     返回条数，默认 20，最大 100

    Returns:
        笔记列表（字典格式，不含 body 内容）
    """
    client = get_client()
    notes = client.list_notes(
        note_type=NoteType(note_type) if note_type else None,
        tag=tag,
        limit=limit,
    )
    return [n.model_dump() for n in notes]


# ---------------------------------------------------------------------------
# get_note
# ---------------------------------------------------------------------------

def get_note(note_id: str, include_content: bool = True) -> dict:
    """
    获取单篇笔记的完整详情（含 body 内容）。

    Args:
        note_id:         Notion 页面 ID
        include_content: 是否返回页面 body 内容，默认 True

    Returns:
        笔记详情，如果 include_content=True 则包含 content 字段
    """
    client = get_client()
    note = client.get_note(note_id)
    result = note.model_dump()
    if include_content:
        result["content"] = client.get_note_content(note_id)
    return result


# ---------------------------------------------------------------------------
# create_note
# ---------------------------------------------------------------------------

def create_note(
    title: str,
    content: str,
    note_type: str = "速记",
    tags: Optional[list[str]] = None,
) -> dict:
    """
    在笔记库中创建一篇新笔记。

    Args:
        title:     笔记标题（必填）
        content:   笔记正文（必填，支持纯文本/Markdown）
        note_type: 笔记类型，可选：会议记录 | 想法 | 参考 | 速记，默认速记
        tags:      标签列表，如 ["前端", "架构"]，可选

    Returns:
        创建成功的笔记详情
    """
    data = NoteCreate(
        title=title,
        content=content,
        type=NoteType(note_type),
        tags=tags or [],
    )
    return get_client().create_note(data).model_dump()


# ---------------------------------------------------------------------------
# append_note
# ---------------------------------------------------------------------------

def append_note(note_id: str, content: str) -> dict:
    """
    向已有笔记追加内容（追加到页面 body 末尾）。

    Args:
        note_id: 笔记 ID
        content: 要追加的文本内容

    Returns:
        更新后的笔记元信息（不含完整 body）
    """
    client = get_client()
    client.append_note_content(note_id, content)
    return client.get_note(note_id).model_dump()


# ---------------------------------------------------------------------------
# search_notes
# ---------------------------------------------------------------------------

def search_notes(query: str) -> list[dict]:
    """
    在笔记库中全文搜索笔记。

    Args:
        query: 搜索关键词

    Returns:
        匹配的笔记列表
    """
    return [n.model_dump() for n in get_client().search_notes(query)]
