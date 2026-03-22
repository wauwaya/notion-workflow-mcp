生成指定时间范围的工作复盘报告，按项目分组输出。

## 用法

```
/review                              # 默认本周
/review today                        # 今日
/review yesterday                    # 昨日
/review this week                    # 本周
/review last week                    # 上周
/review 2026-03-15 2026-03-22        # 指定日期范围（最长31天）
```

## 行为

1. 解析参数，计算 `start_date` 和 `end_date`（YYYY-MM-DD 格式）：
   - 无参数 / `this week` → 本周一 ~ 今天
   - `today` → 今天 ~ 今天
   - `yesterday` → 昨天 ~ 昨天
   - `last week` → 上周一 ~ 上周日
   - `YYYY-MM-DD YYYY-MM-DD` → 直接使用，校验范围 ≤ 31 天
   - 超过 31 天 → 报错：`❌ 日期范围不能超过 31 天`
2. 调用 MCP `generate_review(start_date, end_date)` 获取数据
3. 按项目分组输出复盘报告：

```
📅 {start_date} ~ {end_date} 工作复盘

📊 数据概览
  ✅ 完成任务：{n} 项
  🔄 进行中：{n} 项
  📝 新增笔记：{n} 篇

✅ 完成详情（按项目分组）
  [{项目名}]
    • 任务1
    • 任务2
  [{另一项目}]
    • ...

🔄 当前仍在进行
  • 任务A
  • 任务B

💡 重点建议
  （Claude 根据进行中任务和完成情况自动建议下一步行动）
```
