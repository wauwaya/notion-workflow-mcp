"""
Workflow tools — CRUD and lifecycle operations for 工作流库.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from notion.client import NotionClient
from notion.models import Task, TaskCreate, TaskPriority, TaskStatus, TaskUpdate

_client: Optional[NotionClient] = None


def get_client() -> NotionClient:
    global _client
    if _client is None:
        _client = NotionClient()
    return _client


# ---------------------------------------------------------------------------
# list_tasks
# ---------------------------------------------------------------------------

def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    """
    列出工作流库中的任务。

    Args:
        status:   按状态过滤，可选值：待办 | 进行中 | 完成 | 搁置
        priority: 按优先级过滤，可选值：🔴 紧急 | 🟡 高 | 🟢 普通
        tag:      按标签过滤，精确匹配单个标签名称
        limit:    返回条数，默认 20，最大 100

    Returns:
        任务列表（字典格式）
    """
    client = get_client()
    tasks = client.list_tasks(
        status=TaskStatus(status) if status else None,
        priority=TaskPriority(priority) if priority else None,
        tag=tag,
        limit=limit,
    )
    return [t.model_dump() for t in tasks]


# ---------------------------------------------------------------------------
# get_task
# ---------------------------------------------------------------------------

def get_task(task_id: str) -> dict:
    """
    获取单个任务的完整详情。

    Args:
        task_id: Notion 页面 ID（可从 list_tasks 结果中获取）

    Returns:
        任务详情（字典格式）
    """
    return get_client().get_task(task_id).model_dump()


# ---------------------------------------------------------------------------
# create_task
# ---------------------------------------------------------------------------

def create_task(
    name: str,
    priority: str = "🟢 普通",
    due_date: Optional[str] = None,
    tags: Optional[list[str]] = None,
    note: Optional[str] = None,
) -> dict:
    """
    在工作流库中创建一个新任务（状态默认为"待办"）。

    Args:
        name:     任务名称（必填）
        priority: 优先级，可选：🔴 紧急 | 🟡 高 | 🟢 普通，默认 🟢 普通
        due_date: 截止日期，格式 YYYY-MM-DD，可选
        tags:     标签列表，如 ["开发", "前端"]，可选
        note:     备注说明，可选

    Returns:
        创建成功的任务详情
    """
    data = TaskCreate(
        name=name,
        priority=TaskPriority(priority),
        due_date=due_date,
        tags=tags or [],
        note=note,
    )
    return get_client().create_task(data).model_dump()


# ---------------------------------------------------------------------------
# update_task
# ---------------------------------------------------------------------------

def update_task(
    task_id: str,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    due_date: Optional[str] = None,
    tags: Optional[list[str]] = None,
    note: Optional[str] = None,
) -> dict:
    """
    更新一个已有任务的属性（只传需要修改的字段）。

    Args:
        task_id:  Notion 页面 ID（必填）
        status:   新状态，可选：待办 | 进行中 | 完成 | 搁置
        priority: 新优先级，可选：🔴 紧急 | 🟡 高 | 🟢 普通
        due_date: 新截止日期，格式 YYYY-MM-DD
        tags:     新标签列表（会完整替换原有标签）
        note:     新备注（会替换原有备注）

    Returns:
        更新后的任务详情
    """
    data = TaskUpdate(
        status=TaskStatus(status) if status else None,
        priority=TaskPriority(priority) if priority else None,
        due_date=due_date,
        tags=tags,
        note=note,
    )
    return get_client().update_task(task_id, data).model_dump()


# ---------------------------------------------------------------------------
# start_task
# ---------------------------------------------------------------------------

def start_task(task_id: str) -> dict:
    """
    将任务从"待办"推进到"进行中"，并在页面 body 中记录开始时间。

    Args:
        task_id: 要开始的任务 ID

    Returns:
        更新后的任务详情
    """
    client = get_client()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Update status
    updated = client.update_task(
        task_id,
        TaskUpdate(status=TaskStatus.IN_PROGRESS),
    )

    # Append timestamp to page body
    client.append_task_body(task_id, f"▶ 开始时间：{now}")

    return updated.model_dump()


# ---------------------------------------------------------------------------
# complete_task
# ---------------------------------------------------------------------------

def complete_task(task_id: str, summary: Optional[str] = None) -> dict:
    """
    将任务标记为"完成"，并在页面 body 中记录完成时间和可选总结。

    Args:
        task_id: 要完成的任务 ID
        summary: 可选的完成总结/备注，会追加到页面 body

    Returns:
        更新后的任务详情
    """
    client = get_client()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    updated = client.update_task(task_id, TaskUpdate(status=TaskStatus.DONE))

    log = f"✅ 完成时间：{now}"
    if summary:
        log += f"\n总结：{summary}"
    client.append_task_body(task_id, log)

    return updated.model_dump()


# ---------------------------------------------------------------------------
# search_tasks
# ---------------------------------------------------------------------------

def search_tasks(query: str) -> list[dict]:
    """
    在工作流库中全文搜索任务。

    Args:
        query: 搜索关键词

    Returns:
        匹配的任务列表
    """
    return [t.model_dump() for t in get_client().search_tasks(query)]
