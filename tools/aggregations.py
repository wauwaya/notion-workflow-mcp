"""
Aggregation tools — high-level workflow summaries and reports.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from notion.client import NotionClient
from notion.models import ReviewReport, StandupReport, TaskStatus

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
    yesterday = (now - timedelta(days=1)).date()

    # Yesterday's completed tasks (use last_edited_time as approximate completion time)
    done_tasks = client.list_tasks(status=TaskStatus.DONE, limit=50)
    yesterday_done = [
        f"[{t.project or '无项目'}] {t.name}" for t in done_tasks
        if t.last_edited_time and t.last_edited_time.date() == yesterday
    ]

    # Today's plan: in-progress + due today
    today_tasks = client.get_today_tasks()
    today_plan = [f"[{t.project or '无项目'}] {t.name}" for t in today_tasks]

    # Blockers: on-hold tasks
    on_hold = client.list_tasks(status=TaskStatus.ON_HOLD, limit=20)
    blockers = [f"[{t.project or '无项目'}] {t.name}" for t in on_hold]

    report = StandupReport(
        yesterday_done=yesterday_done,
        today_plan=today_plan,
        blockers=blockers,
    )
    return report.model_dump()


def generate_review(start_date: str, end_date: str) -> dict:
    """
    生成指定日期范围的工作复盘报告。

    Args:
        start_date: 开始日期，格式 YYYY-MM-DD
        end_date: 结束日期，格式 YYYY-MM-DD（包含当天）

    Returns:
        ReviewReport 字典，包含完成任务、进行中任务、笔记数和总结
    """
    start_d = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_d = datetime.strptime(end_date, "%Y-%m-%d").date()

    if end_d < start_d:
        raise ValueError("结束日期不能早于开始日期")
    if (end_d - start_d).days > 30:
        raise ValueError("日期范围不能超过 31 天")

    start = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end = datetime.strptime(end_date, "%Y-%m-%d").replace(
        hour=23, minute=59, second=59, tzinfo=timezone.utc
    )

    client = get_client()

    done_tasks = client.list_tasks(status=TaskStatus.DONE, limit=100)
    range_done = [
        t for t in done_tasks
        if t.last_edited_time and start <= t.last_edited_time <= end
    ]

    in_progress = client.list_tasks(status=TaskStatus.IN_PROGRESS, limit=50)

    notes = client.list_notes(limit=100)
    range_notes_count = sum(
        1 for n in notes
        if n.created_time and start <= n.created_time <= end
    )

    summary_lines = [
        f"📅 {start_date} ~ {end_date} 工作复盘",
        f"✅ 完成任务：{len(range_done)} 项",
        f"🔄 进行中：{len(in_progress)} 项",
        f"📝 新增笔记：{range_notes_count} 篇",
    ]
    if range_done:
        projects: dict[str, list[str]] = {}
        for t in range_done:
            proj = t.project or "无项目"
            projects.setdefault(proj, []).append(t.name)
        summary_lines.append("\n完成详情（按项目分组）：")
        for proj, names in projects.items():
            summary_lines.append(f"  [{proj}]")
            summary_lines.extend(f"    • {n}" for n in names)

    report = ReviewReport(
        start_date=start_date,
        end_date=end_date,
        completed_tasks=range_done,
        in_progress_tasks=in_progress,
        notes_created=range_notes_count,
        summary="\n".join(summary_lines),
    )
    return report.model_dump()
