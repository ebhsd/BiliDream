"""app.py — Bili Recommender
──────────────────────────────────────────────────────────────
2025‑04‑24 rev‑7 (layout row)
  • 顶部一行版式： [时间范围] – [标题图] – [检索条数]  采用 `st.columns([2,1,2])`。
  • 图片宽 180 px，随行居中，无单独占行。
"""

from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
from typing import List

import streamlit as st
from search_core import batch_search, BiliVideo,search_with_keywords  # type: ignore

# ─── Persistent defaults ───────────────────────────────────────────────────
_DEFAULTS = Path(__file__).with_name("ui_defaults.json")

def _load() -> dict:
    if _DEFAULTS.exists():
        try:
            return json.loads(_DEFAULTS.read_text("utf-8"))
        except Exception:
            pass
    return {}

def _save(d: dict):
    try:
        _DEFAULTS.write_text(json.dumps(d, ensure_ascii=False, indent=2), "utf-8")
    except Exception:
        pass

ui_defaults = _load()
MIN_PLAY_DEFAULT  = ui_defaults.get("min_play",     1000)
MIN_LIKE_DEFAULT  = ui_defaults.get("min_like_pct", 4.0)
TIME_LABEL_DEFAULT = ui_defaults.get("time_label",  "3 天")
PAGE_SIZE_DEFAULT = ui_defaults.get("page_size",   20)
ROOT = Path(__file__).parent
TITLE_IMG = ROOT / "title.png"

# ─── Page & CSS ────────────────────────────────────────────────────────────
st.set_page_config("BiliDream", "🎬", layout="wide")

st.markdown(
    """
    <style>
    .block-container{padding-top:2.8rem;}
    .video-card{position:relative;width:100%;aspect-ratio:16/9;overflow:hidden;border-radius:12px;box-shadow:0 2px 6px rgba(0,0,0,.12);margin-bottom:.3rem;}
    .video-card img{width:100%;height:100%;object-fit:cover;transition:transform .25s ease;display:block;}
    .video-card:hover img{transform:scale(1.05);} 
    .video-info{padding:.6rem .38rem 1rem;font-size:.94rem;}
    .video-title{font-weight:600;font-size:1.08rem;line-height:1.35;height:2.8em;overflow:hidden;margin:0;}
    .video-title a{color:#000;text-decoration:none;}
    .stats{color:#000;font-size:.87rem;line-height:1.45;margin-top:.14rem;}
    .stats b{font-weight:600;margin-right:.55rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── Cached backend ────────────────────────────────────────────────────────
@st.cache_data(show_spinner="📡 正在抓取视频…")
def fetch_videos(
        keywords: List[str],
        page_size: int,
        data_mode: str,
        min_play: int,
        min_like: float,
        banned: List[str],
        *,
        custom_start=None,
        custom_end=None
) -> List[BiliVideo]:
    return search_with_keywords(
        keywords,
        page_size,
        data_mode,
        min_play=min_play,
        min_like_ratio=min_like,
        banned_keywords=banned,
        custom_start=custom_start,
        custom_end=custom_end,
    )
# ─── Session init ──────────────────────────────────────────────────────────
if "keywords" not in st.session_state:
    st.session_state["keywords"]=", ".join(ui_defaults.get("keywords",[]))
if "banned" not in st.session_state:
    st.session_state["banned"]=", ".join(ui_defaults.get("banned",[]))
VIDEOS_KEY="videos"

# ─── Top Row: time · title · size ──────────────────────────────────────────
preset=["1 天","3 天","7 天","1 月","1 年","自定义"]
code_map={"1 天":"1d","3 天":"3d","7 天":"7d","1 月":"1m","1 年":"1y","自定义":"custom"}

c_time,c_logo,c_size=st.columns([4,3,3])
with c_time:
    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
    sel_label=st.radio("时间范围",preset,horizontal=True,key="sel_label",index=preset.index(TIME_LABEL_DEFAULT) if TIME_LABEL_DEFAULT in preset else 0,label_visibility="visible")
time_mode=code_map[sel_label]
with c_logo:
    if TITLE_IMG.exists():
        st.image(TITLE_IMG.as_posix(),width=220)
with c_size:
    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
    page_size=st.slider("检索条数",5,50,PAGE_SIZE_DEFAULT,5,key="page_size")

# Custom dates if needed
if time_mode=="custom":
    d1,d2=st.columns(2)
    custom_start=d1.date_input("开始日期",value=datetime.now().date(),key="start_date")
    custom_end=d2.date_input("结束日期",value=datetime.now().date(),key="end_date")
    if custom_start>custom_end:
        st.error("开始日期不能晚于结束日期")
else:
    custom_start=custom_end=None
# ─── Session 初始化 ─────────────────────────────────────
if "initialized" not in st.session_state:
    ui_defaults = _load()  # 只在第一次执行

    # 将 JSON 中的默认值写入 session_state
    st.session_state["keywords_input"] = ", ".join(ui_defaults.get("keywords", []))
    st.session_state["banned_input"]   = ", ".join(ui_defaults.get("banned", []))
    st.session_state["min_play"]       = ui_defaults.get("min_play", 1000)
    st.session_state["min_like_pct"]   = ui_defaults.get("min_like_pct", 4.0)

    st.session_state["initialized"] = True  # 标记已经初始化
# ─── Filter form ───────────────────────────────────────────────────────────
with st.form("filters"):
    c1, c2 = st.columns(2)

    min_play = c1.number_input(
        "最低播放量",
        min_value=0,
        step=100,
        key="min_play"
    )
    min_like_pct = c2.number_input(
        "最低点赞率 (%)",
        min_value=0.0,
        max_value=100.0,
        step=0.5,
        key="min_like_pct"
    )

    keywords_text = st.text_input("关键词 (逗号分隔)", key="keywords_input")
    banned_text = st.text_input("屏蔽关键词 (逗号分隔)", key="banned_input")

    submitted = st.form_submit_button("🚀 开始检索")

# ─── Fetch ────────────────────────────────────────────────────────────────



if submitted:
    kw_raw     = st.session_state["keywords_input"]
    banned_raw = st.session_state["banned_input"]

    kw     = [k.strip() for k in kw_raw.split(",")     if k.strip()]
    banned = [b.strip() for b in banned_raw.split(",") if b.strip()]
    with st.spinner("正在检索并筛选…"):
        vids = fetch_videos(
            kw or [""],
            page_size,
            time_mode,
            min_play,
            min_like_pct / 100,
            banned,
            custom_start=custom_start,
            custom_end=custom_end
        )
    st.session_state[VIDEOS_KEY]=vids
    st.session_state["keywords"]=keywords_text
    st.session_state["banned"]=banned_text
    _save({
        "keywords": kw,
        "banned": banned,
        "min_play": min_play,
        "min_like_pct": min_like_pct,
        "time_label": sel_label,
        "time_mode": time_mode,
        "page_size": page_size,
        "custom_start": custom_start.isoformat() if custom_start else None,
        "custom_end": custom_end.isoformat() if custom_end else None
    })
    st.success(f"找到 {len(vids)} 条符合条件的视频")

# ─── Grid ─────────────────────────────────────────────────────────────────

def render(vs:List[BiliVideo]):
    cols=4
    for i in range(0,len(vs),cols):
        row=st.columns(cols)
        for j,col in enumerate(row):
            idx=i+j
            if idx>=len(vs): break
            v=vs[idx]
            cover=v.cover.replace("http://","https://") if v.cover else ""
            if cover.startswith("//"):cover="https:"+cover
            cover="https://images.weserv.nl/?url="+cover.lstrip("https://")
            link=f"https://www.bilibili.com/video/{v.bvid}"
            col.markdown(
                f"<div class='video-card'><a href='{link}' target='_blank' referrerpolicy='no-referrer'>"
                f"<img src='{cover}'/></a></div>"
                f"<div class='video-info'><div class='video-title'><a href='{link}' target='_blank' referrerpolicy='no-referrer'>{v.title}</a></div>"
                f"<div class='stats'>▶️{v.play} 👍{v.like} 💾{v.favorites}<br><b>UP:</b> {v.author}</div></div>",
                unsafe_allow_html=True)

if VIDEOS_KEY in st.session_state and st.session_state[VIDEOS_KEY]:
    render(st.session_state[VIDEOS_KEY])
