快速创建一篇笔记到笔记库。

## 用法

```
/note <笔记内容>
/note <标题> --type <类型> --task <task_id>
```

## 示例

```
/note 今天发现登录接口有并发问题，需要加锁
/note 架构评审结论 --type 会议记录 --task abc123
/note 参考文章：https://example.com/redis-lock --type 参考
```

## 行为

1. 解析内容、类型（默认"速记"）、关联任务（可选）
2. 调用 `create_note` 创建笔记
3. 如果有 `--task`，自动建立双向关联
4. 输出确认信息：

```
📝 笔记已创建：今天发现登录接口有并发问题
  类型：速记
  🔗 https://notion.so/...
```

## 类型关键词识别

- 会议 / meeting → 会议记录
- 想法 / idea → 想法
- 参考 / ref / reference → 参考
- 其他（默认）→ 速记
