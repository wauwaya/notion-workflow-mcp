"""
Pydantic data models for Notion Workflow MCP.
Mirrors the Notion database schemas for 工作流库 and 笔记库.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TaskStatus(str, Enum):
    TODO = "待办"
    IN_PROGRESS = "进行中"
    DONE = "完成"
    ON_HOLD = "搁置"


class TaskPriority(str, Enum):
    URGENT = "🔴 紧急"
    HIGH = "🟡 高"
    NORMAL = "🟢 普通"


class NoteType(str, Enum):
    MEETING = "会议记录"
    IDEA = "想法"
    REFERENCE = "参考"
    QUICK = "速记"


class SubtaskStatus(str, Enum):
    TODO = "todo"
    DOING = "doing"
    DONE = "done"


SUBTASK_STATUS_DISPLAY = {
    SubtaskStatus.TODO: "⬜ 待办",
    SubtaskStatus.DOING: "🔄 进行中",
    SubtaskStatus.DONE: "✅ 完成",
}
SUBTASK_DISPLAY_TO_STATUS = {v: k for k, v in SUBTASK_STATUS_DISPLAY.items()}


class Subtask(BaseModel):
    """A subtask embedded in a task page body as table + detail sections."""
    name: str = Field(description="子目标名称")
    status: SubtaskStatus = Field(default=SubtaskStatus.TODO, description="状态")
    priority: TaskPriority = Field(default=TaskPriority.NORMAL, description="优先级")
    detail: str = Field(default="", description="子目标详情")


# ---------------------------------------------------------------------------
# Task (工作流库)
# ---------------------------------------------------------------------------

class Task(BaseModel):
    """Represents a row in the 工作流库 database."""

    id: str = Field(description="Notion page ID")
    name: str = Field(description="任务名称")
    status: TaskStatus = Field(default=TaskStatus.TODO, description="任务状态")
    priority: Optional[TaskPriority] = Field(default=TaskPriority.NORMAL, description="优先级")
    project: Optional[str] = Field(default=None, description="所属项目")
    due_date: Optional[str] = Field(default=None, description="截止日期 (ISO 8601 date string)")
    tags: list[str] = Field(default_factory=list, description="标签列表")
    note: Optional[str] = Field(default=None, description="备注")
    created_time: Optional[datetime] = Field(default=None, description="创建时间")
    last_edited_time: Optional[datetime] = Field(default=None, description="最后编辑时间")
    url: Optional[str] = Field(default=None, description="Notion 页面 URL")


class TaskCreate(BaseModel):
    """Input model for creating a new task."""

    name: str = Field(description="任务名称")
    project: Optional[str] = Field(default=None, description="所属项目")
    priority: TaskPriority = Field(default=TaskPriority.NORMAL)
    due_date: Optional[str] = Field(default=None, description="截止日期，格式：YYYY-MM-DD")
    tags: list[str] = Field(default_factory=list)
    note: Optional[str] = Field(default=None, description="备注")


class TaskUpdate(BaseModel):
    """Input model for updating an existing task."""

    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    project: Optional[str] = None
    due_date: Optional[str] = None
    tags: Optional[list[str]] = None
    note: Optional[str] = None


# ---------------------------------------------------------------------------
# Note (笔记库)
# ---------------------------------------------------------------------------

class Note(BaseModel):
    """Represents a row in the 笔记库 database."""

    id: str = Field(description="Notion page ID")
    title: str = Field(description="笔记标题")
    type: Optional[NoteType] = Field(default=NoteType.QUICK, description="笔记类型")
    tags: list[str] = Field(default_factory=list, description="标签列表")
    created_time: Optional[datetime] = Field(default=None, description="创建时间")
    url: Optional[str] = Field(default=None, description="Notion 页面 URL")


class NoteCreate(BaseModel):
    """Input model for creating a new note."""

    title: str = Field(description="笔记标题")
    content: str = Field(description="笔记正文内容（Markdown）")
    type: NoteType = Field(default=NoteType.QUICK)
    tags: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Overview / Summary models
# ---------------------------------------------------------------------------

class TaskOverview(BaseModel):
    """Summary of task counts by status."""

    todo: int = 0
    in_progress: int = 0
    done: int = 0
    on_hold: int = 0
    total: int = 0


class StandupReport(BaseModel):
    """Daily standup report."""

    yesterday_done: list[str] = Field(default_factory=list, description="昨日完成")
    today_plan: list[str] = Field(default_factory=list, description="今日计划")
    blockers: list[str] = Field(default_factory=list, description="阻塞项")
    generated_at: datetime = Field(default_factory=datetime.now)


class WeeklyReview(BaseModel):
    """Weekly review report."""

    week_label: str = Field(description="e.g. '2026-W12'")
    completed_tasks: list[Task] = Field(default_factory=list)
    in_progress_tasks: list[Task] = Field(default_factory=list)
    notes_created: int = 0
    summary: str = ""
