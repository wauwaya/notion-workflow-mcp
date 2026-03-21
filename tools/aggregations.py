"""
Aggregation tools — high-level workflow summaries and reports.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from notion.client import NotionClient
from notion.models import StandupReport, TaskStatus, WeeklyReview

_client: Optional[NotionClient] = None


def get_client() -> NotionClient:
    global _client
    if _client is None:
        _client = NotionClient()
    return _client


def get_overview() -> dict:
    """
    获取工作流库的任务状态概览（各状态数量仪表盘）。

    Returns:
        包含 todo / in_progress / done / on_hold / total 数量的字典
    """
    return get_client().get_task_overview().model_dump()


def get_today_tasks() -> list[dict]:
    """
    获取今日相关任务：今天到期的任务 + 所有进行中的任务。

    Returns:
        任务列表，按优先级排序
    """
    tasks = get_client().get_today_tasks()
    return [t.model_dump() for t in tasks]


def generate_standup() -> dict:
    """
    自动生成每日站会内容：昨日完成 / 今日计划 / 阻塞项。

    Returns:
        StandupReport 字典，包含三个列表和生成时间
    """
    client = get_client()
    now = datetime.now(timezone.utc)
    yesterday = (now - timedelta(days=1)).date().isoformat()
    today = now.date().isoformat()
    tomorrow = (now + timedelta(days=1)).date().isoformat()

    # Yesterday's completed tasks
    done_tasks = client.list_tasks(status=TaskStatus.DONE, limit=50)
    yesterday_done = [
        t.name for t in done_tasks
        if t.created_time and t.created_time.date().isoformat() >= yesterday
    ]

    # Today's plan: in-progress + due today
    today_tasks = client.get_today_tasks()
    today_plan = [t.name for t in today_tasks]

    # Blockers: on-hold tasks
    on_hold = client.list_tasks(status=TaskStatus.ON_HOLD, limit=20)
    blockers = [t.name for t in on_hold]

    report = StandupReport(
        yesterday_done=yesterday_done,
        today_plan=today_plan,
        blockers=blockers,
    )
    return report.model_dump()


def generate_weekly_review(week_offset: int = 0) -> dict:
    """
    生成工作周报/复盘，默认为本周，week_offset=-1 为上周。

    Args:
        week_offset: 0 = 本周，-1 = 上周，以此类推

    Returns:
        WeeklyReview 字典，包含完成任务、进行中任务、创建笔记数和总结
    """
    client = get_client()
    now = datetime.now(timezone.utc)

    # Calculate week boundaries (Monday to Sunday)
    monday = now - timedelta(days=now.weekday()) + timedelta(weeks=week_offset)
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    sunday = monday + timedelta(days=6, hours=23, minutes=59, seconds=59)

    year, week_num, _ = monday.isocalendar()
    week_label = f"{year}-W{week_num:02d}"

    # Completed tasks this week
    done_tasks = client.list_tasks(status=TaskStatus.DONE, limit=100)
    weekly_done = [
        t for t in done_tasks
        if t.created_time and monday <= t.created_time <= sunday
    ]

    # In-progress tasks
    in_progress = client.list_tasks(status=TaskStatus.IN_PROGRESS, limit=50)

    # Notes created this week
    notes = client.list_notes(limit=100)
    weekly_notes_count = sum(
        1 for n in notes
        if n.created_time and monday <= n.created_time <= sunday
    )

    summary_lines = [
        f"📅 {week_label} 工作复盘",
        f"✅ 完成任务：{len(weekly_done)} 项",
        f"🔄 进行中：{len(in_progress)} 项",
        f"📝 新增笔记：{weekly_notes_count} 篇",
    ]
    if weekly_done:
        summary_lines.append("\n完成项目：")
        summary_lines.extend(f"  • {t.name}" for t in weekly_done)

    review = WeeklyReview(
        week_label=week_label,
        completed_tasks=weekly_done,
        in_progress_tasks=in_progress,
        notes_created=weekly_notes_count,
        summary="\n".join(summary_lines),
    )
    return review.model_dump()
