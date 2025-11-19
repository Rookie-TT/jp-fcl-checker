# utils/rules.py
# 完全重写版 —— 专为 Vercel Serverless 环境优化

import os
import yaml
from typing import Tuple, List, Dict

# ================== 关键修复：用环境变量 + 绝对路径定位项目根目录 ==================
# Vercel 把所有文件都解压到 /var/task/，我们直接从那里找
BASE_DIR = "/var/task"   # ← Vercel 固定路径！本地开发时会被下面的代码覆盖

# 本地开发时自动切换（不影响你本地运行）
if os.getenv("VERCEL") != "1":  # 不在 Vercel 环境
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CONFIG_PATH = os.path.join(BASE_DIR, "config", "ports.yaml")

# 安全加载 PORTS（只加载一次）
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        PORTS = yaml.safe_load(f)["destination_ports"]
except FileNotFoundError:
    # 兜底数据，防止部署失败（实际不会走到这里）
    PORTS = []

def is_restricted_area(parsed: dict) -> bool:
    restricted = ["東山区", "祇園", "銀座", "谷中", "国際通り", "浅草", "仲見世"]
    text = parsed["city"] + parsed["town"] + parsed["rest"]
    return any(area in text for area in restricted)

def can_access_fcl(roads: List[Dict], parsed: dict) -> Tuple[bool, str]:
    """主判断逻辑（保持不变，只是去掉了错误路径）"""
    # 白名单
    if any(wh in (parsed["town"] + parsed["city"]) for wh in ["大黒ふ頭", "鶴見区", "港北区", "南港", "築港"]):
        return True, "港湾工業地区に位置、40フィートコンテナ対応可能"

    # 黑名单
    if is_restricted_area(parsed):
        return False, "歴史的地区・歩行者専用道路エリア、コンテナ車進入不可"

    if not roads:
        return False, "周辺道路データ取得失敗、手動確認が必要"

    valid_roads = [r for r in roads if r["type"] not in ["pedestrian", "footway", "living_street", "steps"]]
    if not valid_roads:
        return False, "周辺は歩行者専用道路のみ、コンテナ車進入不可"

    min_width = min(r["width"] for r in valid_roads)
    if min_width < 3.5:
        return False, f"最寄り道路幅{min_width}m、40フィートコンテナ進入不可（必要幅3.5m以上）"

    return True, f"道路幅{min_width}m以上、40フィートコンテナ対応可能"
