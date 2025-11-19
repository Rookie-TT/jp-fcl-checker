# utils/rules.py
# 2025 年 Vercel 终极无敌版 —— 零导入、零路径、零崩溃！

from typing import List, Dict, Tuple

def is_restricted_area(parsed: dict) -> bool:
    restricted = ["東山区","祇園","銀座","谷中","国際通り","浅草","仲見世","花見小路","先斗町","清水寺","二年坂","三年坂"]
    text = parsed.get("city","") + parsed.get("town","") + parsed.get("rest","")
    return any(kw in text for kw in restricted)

def can_access_fcl(roads: List[Dict], parsed: dict) -> Tuple[bool, str]:
    # 白名单（港口工业区）
    if any(kw in (parsed.get("town","") + parsed.get("city","")) 
           for kw in ["大黒ふ頭","鶴見区","南港","築港","港北区","本牧ふ頭","扇町","港区","臨海"]):
        return True, "港湾・工業地区、40フィートコンテナ対応可能"

    # 黑名单
    if is_restricted_area(parsed):
        return False, "歴史的地区・歩行者専用エリア、コンテナトラック進入不可"

    if not roads:
        return False, "周辺道路データ取得失敗（OSM）"

    # 过滤无效道路
    valid_roads = [r for r in roads if r.get("type") not in ["pedestrian","footway","living_street","steps","path","cycleway"]]
    if not valid_roads:
        return False, "周辺は歩行者・自転車道のみ、コンテナ車進入不可"

    # 安全取宽度（防止 None 或 str）
    widths = []
    for r in valid_roads:
        w = r.get("width")
        if isinstance(w, (int, float)):
            widths.append(w)
        elif isinstance(w, str) and "m" in w:
            try:
                widths.append(float(w.replace("m","").strip()))
            except:
                pass
    if not widths:
        return False, "道路幅データなし（手動確認推奨）"

    min_width = min(widths)
    if min_width < 3.5:
        return False, f"最寄り道路幅{min_width}m（必要3.5m以上）"

    return True, f"道路幅{min_width}m以上、40フィートコンテナ対応可能"
