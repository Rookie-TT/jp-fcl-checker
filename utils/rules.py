# utils/rules.py
from typing import List, Dict, Tuple

# 直接引用 index.py 已经加载好的 PORTS，彻底杜绝路径问题
try:
    from api.index import PORTS
except ImportError:
    PORTS = []  # 兜底

def is_restricted_area(parsed: dict) -> bool:
    restricted = ["東山区","祇園","銀座","谷中","国際通り","浅草","仲見世","花見小路","先斗町"]
    text = parsed.get("city","") + parsed.get("town","") + parsed.get("rest","")
    return any(kw in text for kw in restricted)

def can_access_fcl(roads: List[Dict], parsed: dict) -> Tuple[bool, str]:
    # 白名单
    whitelist = ["大黒ふ頭","鶴見区","南港","築港","港北区","本牧ふ頭","扇町"]
    if any(kw in (parsed.get("town","") + parsed.get("city","")) for kw in whitelist):
        return True, "港湾・工業地区、40フィートコンテナ対応可能"

    # 黑名单
    if is_restricted_area(parsed):
        return False, "歴史的地区・歩行者天国エリア、コンテナトラック進入禁止"

    if not roads:
        return False, "周辺道路データ取得失敗"

    valid_roads = [r for r in roads if r.get("type") not in ["pedestrian","footway","living_street","steps","path"]]
    if not valid_roads:
        return False, "周辺は歩行者専用道路のみ"

    min_width = min(r["width"] for r in valid_roads if isinstance(r.get("width"), (int,float)))
    if min_width < 3.5:
        return False, f"最寄り道路幅{min_width}m（必要3.5m以上）"

    return True, f"道路幅{min_width}m以上、40フィートコンテナ対応可能"
