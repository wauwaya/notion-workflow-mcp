"""
init_databases.py — 检查并初始化 Notion 数据库字段。

notion-client 3.0: databases.* → data_sources.*

用法：
    python scripts/init_databases.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
from notion_client import Client

load_dotenv()

# ---------------------------------------------------------------------------
# Expected schema definitions
# ---------------------------------------------------------------------------

WORKFLOW_SCHEMA: dict[str, dict] = {
    "状态": {
        "select": {
            "options": [
                {"name": "待办",   "color": "gray"},
                {"name": "进行中", "color": "blue"},
                {"name": "完成",   "color": "green"},
                {"name": "搁置",   "color": "yellow"},
            ]
        }
    },
    "优先级": {
        "select": {
            "options": [
                {"name": "🔴 紧急", "color": "red"},
                {"name": "🟡 高",   "color": "yellow"},
                {"name": "🟢 普通", "color": "green"},
            ]
        }
    },
    "截止日期": {"date": {}},
    "标签": {"multi_select": {"options": []}},
    "备注": {"rich_text": {}},
    "项目": {
        "select": {
            "options": []
        }
    },
}

NOTES_SCHEMA: dict[str, dict] = {
    "类型": {
        "select": {
            "options": [
                {"name": "会议记录", "color": "blue"},
                {"name": "想法",     "color": "purple"},
                {"name": "参考",     "color": "orange"},
                {"name": "速记",     "color": "gray"},
            ]
        }
    },
    "标签": {"multi_select": {"options": []}},
}


def get_existing_properties(client: Client, ds_id: str) -> set[str]:
    ds = client.data_sources.retrieve(data_source_id=ds_id)
    return set(ds.get("properties", {}).keys())


def add_property(client: Client, ds_id: str, name: str, prop_config: dict) -> None:
    client.data_sources.update(
        data_source_id=ds_id,
        properties={name: prop_config},
    )
    print(f"  ✅ 添加字段：{name}")


def init_database(client: Client, ds_id: str, schema: dict, db_label: str) -> None:
    print(f"\n🗄  检查 {db_label} (ID: {ds_id[:8]}...)")
    existing = get_existing_properties(client, ds_id)
    print(f"  已有字段：{sorted(existing)}")

    for prop_name, prop_config in schema.items():
        if prop_name in existing:
            print(f"  ⏭  已存在：{prop_name}")
            continue
        try:
            add_property(client, ds_id, prop_name, prop_config)
        except Exception as e:
            print(f"  ❌ 添加失败 {prop_name}：{e}")


def main() -> None:
    token = os.getenv("NOTION_TOKEN")
    workflow_db_id = os.getenv("WORKFLOW_DATABASE_ID")
    notes_db_id = os.getenv("NOTES_DATABASE_ID")

    if not all([token, workflow_db_id, notes_db_id]):
        print("❌ 请先复制 .env.example 为 .env，并填写所有变量")
        sys.exit(1)

    client = Client(auth=token)

    print("=" * 50)
    print("  Notion Workflow MCP — 数据库初始化")
    print("=" * 50)

    init_database(client, workflow_db_id, WORKFLOW_SCHEMA, "工作流库")
    init_database(client, notes_db_id, NOTES_SCHEMA, "笔记库")

    print("\n✨ 初始化完成！")
    print("\n📌 下一步：重启 Claude CLI，MCP Server 即可使用")


if __name__ == "__main__":
    main()
