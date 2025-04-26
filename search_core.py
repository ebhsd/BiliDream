from typing import List
import json
import random

from modules.bilibili_search import search_bilibili_videos, BiliVideo


def filter_videos(
    videos: List[BiliVideo],
    *,
    min_play: int = 1000,
    min_like_ratio: float = 0.04,
    banned_keywords: List[str] | None = None,
) -> List[BiliVideo]:
    """根据播放量 / 点赞比 / 屏蔽关键词筛选 B 站视频列表。

    Args:
        videos: search_bilibili_videos 返回的 BiliVideo 列表。
        min_play:   播放量阈值，低于该值的视频会被过滤掉。
        min_like_ratio: 赞 / 播放 的最小比例，低于该值的视频会被过滤掉。
        banned_keywords: 标题或标签中若出现任一关键词，则过滤掉该视频（大小写不敏感）。

    Returns:
        过滤后的 BiliVideo 列表。
    """
    if banned_keywords is None:
        banned_keywords = []

    banned_lower = [kw.lower() for kw in banned_keywords]
    filtered: List[BiliVideo] = []

    for v in videos:
        # --- 数值字段容错处理（B 站接口有时会返回带逗号的字符串） ---
        try:
            play = int(str(v.play).replace(",", ""))
            like = int(str(v.like).replace(",", ""))
        except ValueError:
            play, like = 0, 0

        like_ratio = like / play if play else 0  # 避免除零

        # --- 过滤规则 ---
        if play < min_play:
            continue
        if like_ratio < min_like_ratio:
            continue
        title_tag_combined = f"{v.title} {v.tag}".lower()
        if any(bk in title_tag_combined for bk in banned_lower):
            continue

        filtered.append(v)
        random.shuffle(filtered)

    return filtered


def batch_search(
        keywords: List[str],
        page_size: int,
        data_mode: str,
        *,
        custom_start=None,              # ← 新增
        custom_end=None,                # ← 新增
        **filter_kwargs
) -> List[BiliVideo]:
    """批量搜索多个关键词并按需过滤。

    Args:
        keywords:    关键词列表。
        page_size:   每个关键词请求的条目数。
        data_mode:   时间范围模式，传递给 search_bilibili_videos。
        **filter_kwargs: 传递给 filter_videos 的可选参数。

    Returns:
        最终满足过滤规则的 BiliVideo 列表。
    """
    all_videos: List[BiliVideo] = []
    for kw in keywords:
        vids = search_bilibili_videos(
            kw,
            page_size,
            data_mode,
            custom_start=custom_start,  # ← 继续下传
            custom_end=custom_end
        )
        all_videos.extend(vids)

    if filter_kwargs:
        all_videos = filter_videos(all_videos, **filter_kwargs)

    return all_videos


def videos_to_json(videos: List[BiliVideo], path: str | None = None):
    """将视频列表序列化为 JSON，便于 WebUI 消费。"""
    data = [v.to_dict() for v in videos]
    if path:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    return data
def search_with_keywords(
    keywords: List[str],
    page_size: int,
    data_mode: str,
    *,
    min_play: int = 0,
    min_like_ratio: float = 0,
    banned_keywords: List[str] = [],
    custom_start: str | None = None,
    custom_end: str | None = None,
    shuffle: bool = True,
) -> List[BiliVideo]:
    """多关键词搜索并统一筛选 + 日期支持 + 打乱顺序"""
    all_videos = []
    for kw in keywords:
        vids = search_bilibili_videos(
            keyword=kw,
            page_size=page_size,
            data_mode=data_mode,
            custom_start=custom_start,
            custom_end=custom_end,
        )
        filtered = filter_videos(
            vids,
            min_play=min_play,
            min_like_ratio=min_like_ratio,
            banned_keywords=banned_keywords,
        )
        all_videos.extend(filtered)

    all_videos = list({v.bvid: v for v in all_videos}.values())
    if shuffle:
        import random
        random.shuffle(all_videos)

    return all_videos


if __name__ == "__main__":
    # --- 示例配置，可由前端或 CLI 参数覆盖 -----------------------------
    KEYWORDS = [
        "mygo",
        "赛马娘",
    ]
    PAGE_SIZE = 10          # 每个关键词检索条目数
    DATA_MODE = "1d"       # 时间范围：昨天全天

    # 过滤条件（可暴露给前端表单）
    MIN_PLAY = 1000
    MIN_LIKE_RATIO = 0.04  # 4%
    BANNED_KEYWORDS = ["crychic"]

    # -----------------------------------------------------------------
    videos = batch_search(
        KEYWORDS,
        PAGE_SIZE,
        DATA_MODE,
        min_play=MIN_PLAY,
        min_like_ratio=MIN_LIKE_RATIO,
        banned_keywords=BANNED_KEYWORDS,
    )

    print(f"找到符合条件的视频：{len(videos)} 条")
    for v in videos:
        print(v)

    # 保存为 JSON，WebUI 可直接读取该文件渲染列表
    videos_to_json(videos, "videos.json")
