from datetime import datetime, date,timedelta
from dateutil.relativedelta import relativedelta  # pip install python-dateutil
import json
import os

#时间戳
def get_time_range(mode: str = "1d", custom_start: str = None, custom_end: str = None):
    """
    获取指定时间段的起止时间戳（单位：秒）

    参数:
    - mode: 可选时间段 '1d', '3d', '7d', '1m', '1y', 'custom'
    - custom_start / custom_end: 当 mode='custom' 时使用，格式 'YYYY-MM-DD'

    返回:
    - dict: {"start_ts": int, "end_ts": int}
    """
    today = datetime.now().date()

    if mode == "custom":
        if not (custom_start and custom_end):
            raise ValueError("自定义模式必须提供 custom_start 和 custom_end")

        def _to_date(x):
            if isinstance(x, date):
                return x if not isinstance(x, datetime) else x.date()
            return datetime.strptime(x, "%Y-%m-%d").date()

        start_date = _to_date(custom_start)
        end_date = _to_date(custom_end)
    else:
        if mode == "1d":
            start_date = today - timedelta(days=1)
        elif mode == "3d":
            start_date = today - timedelta(days=3)
        elif mode == "7d":
            start_date = today - timedelta(days=7)
        elif mode == "1m":
            start_date = today - relativedelta(months=1)
        elif mode == "1y":
            start_date = today - relativedelta(years=1)
        else:
            raise ValueError("未知的模式：" + mode)
        end_date = today

    # 生成起止时间戳（从起始日 00:00 到结束日 23:59:59）
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time()).replace(microsecond=0)

    return {
        "start_ts": int(start_dt.timestamp()),
        "end_ts": int(end_dt.timestamp())
    }

#读取config.json
def load_config_from_parent(filename="config.json"):
    # 获取当前脚本文件所在路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 找到父目录
    parent_dir = os.path.dirname(current_dir)
    # 构造完整路径
    config_path = os.path.join(parent_dir, filename)

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    return config["headers"], config["cookies"]


if __name__ == '__main__':

    print(get_time_range("1d"))
    # {'start_ts': 1745337600, 'end_ts': 1745423999}  ← 昨天全天

    print(get_time_range("1m"))
    # {'start_ts': 1742745600, 'end_ts': 1745423999}  ← 1个月前到昨天

    print(get_time_range("custom", "2025-03-01", "2025-03-05"))
    # {'start_ts': 1740768000, 'end_ts': 1741209599}