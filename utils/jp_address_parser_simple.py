# utils/jp_address_parser_simple.py
import re
from collections import namedtuple

# 定义一个兼容旧接口的 NamedTuple
ParsedAddress = namedtuple('ParsedAddress', ['prefecture', 'city', 'town', 'rest', 'full'])

PREFECTURES = (
    "北海道|東京都|大阪府|神奈川県|愛知県|埼玉県|千葉県|兵庫県|広島県|福岡県|静岡県|茨城県|"
    "栃木県|群馬県|新潟県|長野県|岐阜県|三重県|京都府|奈良県|沖縄県|"
    "青森県|岩手県|宮城県|秋田県|山形県|福島県|富山県|石川県|福井県|山梨県|"
    "滋賀県|和歌山県|鳥取県|島根県|岡山県|山口県|徳島県|香川県|愛媛県|高知県|"
    "佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県"
).split("|")

def parse(address: str):
    addr = address.strip()
    prefecture = city = town = ""
    rest = addr

    # 提取都道府县
    for pref in PREFECTURES:
        if addr.startswith(pref):
            prefecture = pref
            addr = addr[len(pref):]
            break

    # 提取市/区/町/村
    m = re.match(r"(.+?[市区町村])", addr)
    if m:
        city = m.group(1)
        addr = addr[m.end():]

    # 提取町名（到数字或丁目前）
    m = re.search(r"(.+?)(?:[0-9一二三四五六七八九十丁目番地])", addr)
    if m:
        town = m.group(1)
        rest = addr[m.end():]
    else:
        town = addr

    # 返回 NamedTuple（完美兼容你原来的 .prefecture / ._asdict()）
    return ParsedAddress(prefecture, city, town, rest, address.strip())
