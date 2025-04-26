import json
import random
from pathlib import Path
from urllib.parse import quote_plus

import requests
from search_core import search_with_keywords    # ← 你的搜索核心

# ── 配置区域 ─────────────────────────────────────────────
PUSHPLUS_TOKEN   = "Your_PushPlus_Token"

KEYWORDS         = ["mygo", "赛马娘", "ave mujica", "孤独摇滚",
                    "bangdream", "娱乐", "知识"]
BANNED_KEYWORDS  = ["曼波"]
MIN_PLAY         = 3_000
MIN_LIKE_RATIO   = 0.06          # 6 %
PAGE_SIZE        = 40            # 每关键词抓 40
DATA_MODE        = "3d"          # 最近 3 天
MAX_PUSH         = 10            # 每日最多推 10 条
LIMIT_CHARS      = 20_000        # PushPlus 最大字符

HISTORY_FILE     = Path("sent_history.json")    # 已推送记录

# ── PushPlus 发送 ─────────────────────────────────────
def push_markdown(title: str, md: str) -> bool:
    r = requests.post(
        "http://www.pushplus.plus/send",
        json={
            "token": PUSHPLUS_TOKEN,
            "title": title,
            "content": md,
            "template": "markdown",
        },
        timeout=10,
    )
    print("PushPlus:", r.status_code, r.text[:120])
    return r.status_code == 200

# ── 历史记录 ───────────────────────────────────────────
def load_history() -> set[str]:
    try:
        return set(json.loads(HISTORY_FILE.read_text("utf-8")))
    except Exception:
        return set()

def save_history(bvids: set[str]):
    HISTORY_FILE.write_text(json.dumps(sorted(bvids), indent=2), "utf-8")

# ── 抓取 + 本次去重 ─────────────────────────────────────
def fetch_new_videos():
    # 1. 抓取多关键词
    videos = search_with_keywords(
        KEYWORDS,
        page_size=PAGE_SIZE,
        data_mode=DATA_MODE,
        min_play=MIN_PLAY,
        min_like_ratio=MIN_LIKE_RATIO,
        banned_keywords=BANNED_KEYWORDS,
    )
    # 2. 全局去重（同一视频命中多个关键词时）
    unique = {}
    for v in videos:
        unique.setdefault(v.bvid, v)
    videos = list(unique.values())

    # 3. 去掉历史已推送
    sent = load_history()
    fresh = [v for v in videos if v.bvid not in sent]

    # 4. 随机顺序 + 截至 MAX_PUSH
    random.shuffle(fresh)
    return fresh[:MAX_PUSH]

# ── Markdown 构造（保证 ≤ 20 000 字） ──────────────────
def build_markdown(videos):
    lines = ["## 🎬 最近 3 天精选视频\n"]
    total_len = len(lines[0]) + 2

    for idx, v in enumerate(videos, 1):
        cover = v.cover
        if cover.startswith("//"):
            cover = "https:" + cover
        cover = cover.replace("http://", "https://")
        proxy = "https://images.weserv.nl/?url=" + quote_plus(cover[8:], safe=":/")
        link  = f"https://www.bilibili.com/video/{v.bvid}"

        block = [
            f"### {idx}. [{v.title}]({link})",
            f"![封面图]({proxy})",
            f"- ▶️ {v.play}　👍 {v.like}　💾 {v.favorites}",
            f"- UP：{v.author}",
            "---",
        ]
        block_text = "\n".join(block) + "\n\n"

        if total_len + len(block_text) > LIMIT_CHARS:
            break        # 超限则停止追加
        lines.append(block_text)
        total_len += len(block_text)

    return "".join(lines)

# ── 主流程 ─────────────────────────────────────────────
def main():
    new_videos = fetch_new_videos()
    if not new_videos:
        print("无新视频可推送")
        return

    md = build_markdown(new_videos)
    if push_markdown("B 站视频推送", md):
        hist = load_history()
        hist.update(v.bvid for v in new_videos)
        save_history(hist)
        print(f"已推送 {len(new_videos)} 条，历史库大小：{len(hist)}")
    else:
        print("推送失败")

if __name__ == "__main__":
    main()
