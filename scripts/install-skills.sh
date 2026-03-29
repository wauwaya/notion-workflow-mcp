#!/usr/bin/env bash
# 将仓库中的 skills 安装到 Claude Code 全局目录
# 用法: bash scripts/install-skills.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
SKILLS_SRC="$REPO_DIR/.claude/skills"
SKILLS_DST="$HOME/.claude-internal/skills"

if [ ! -d "$SKILLS_SRC" ]; then
    echo "❌ 未找到 $SKILLS_SRC"
    exit 1
fi

mkdir -p "$SKILLS_DST"

installed=0
for skill_dir in "$SKILLS_SRC"/*/; do
    [ -f "$skill_dir/SKILL.md" ] || continue
    skill_name="$(basename "$skill_dir")"
    dst="$SKILLS_DST/$skill_name"
    mkdir -p "$dst"
    cp "$skill_dir/SKILL.md" "$dst/SKILL.md"
    installed=$((installed + 1))
done

echo "✅ 已安装 $installed 个 skills 到 $SKILLS_DST"
echo "   重启 Claude Code 会话即可生效"
