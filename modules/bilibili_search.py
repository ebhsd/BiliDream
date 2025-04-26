import requests
import re
from modules import tool
import json

def clean_html(raw_text):
    return re.sub(r'<.*?>', '', raw_text)

class BiliVideo:
    def __init__(self, raw_data: dict):
        self.bvid = raw_data.get("bvid", "").strip()
        self.title = clean_html(raw_data.get("title", ""))
        self.author = raw_data.get("author", "")
        self.play = raw_data.get("play", "0")
        self.like = raw_data.get("like", "0")
        self.tag = raw_data.get("tag", "")
        self.favorites = raw_data.get("favorites", "0")
        self.cover= 'https:'+raw_data.get("pic", "")

    def to_dict(self):
        return {
            "bvid": self.bvid,
            "title": self.title,
            "author": self.author,
            "play": self.play,
            "like": self.like,
            "tag": self.tag,
            "favorites": self.favorites
        }

    def __repr__(self):
        return (
            f"BiliVideo(\n"
            f"  标题: {self.title}\n"
            f"  作者: {self.author}\n"
            f"  BV号: {self.bvid}\n"
            f"  播放量:{self.play}"
            f"  点赞: {self.like}"
            f"  收藏: {self.favorites}"
            f"  标签: {self.tag}"
            f"  封面: {self.cover}"
            f")"
        )

def search_bilibili_videos(
        keyword,
        page_size,
        data_mode,
        *,
        custom_start=None,              # ← 新增
        custom_end=None                 # ← 新增
):
    url = "https://api.bilibili.com/x/web-interface/search/type"

    time_range = tool.get_time_range(
        data_mode,
        custom_start=custom_start,  # ← 终于传给工具函数
        custom_end=custom_end
    )
    params = {
        "keyword": keyword,
        "search_type": "video",
        "page": 1,
        "page_size": page_size,
        "order": "totalrank",
        "duration": 0,
        "pubtime_begin_s": time_range['start_ts'],
        "pubtime_end_s": time_range['end_ts']
    }

    headers, cookies = tool.load_config_from_parent()
    resp = requests.get(url, headers=headers, cookies=cookies, params=params)

    if resp.status_code != 200:
        print("请求失败，状态码：", resp.status_code)
        return []

    try:
        data = resp.json()
        result = []
        for item in data["data"]["result"]:
            video = BiliVideo(item)
            if video.bvid:  # 确保 bvid 存在
                result.append(video)
        return result
    except Exception as e:
        print("解析失败:", e)
        return []

if __name__ == "__main__":
    videos = search_bilibili_videos("AI绘画", 5, "1d")
    for video in videos:
        print(video)
