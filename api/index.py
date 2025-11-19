import os
import yaml
from flask import Flask, render_template, request, jsonify
from mangum import Mangum

# 路径
BASE_DIR = "/var/task" if os.getenv("VERCEL") else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))

# 加载港口
with open(os.path.join(BASE_DIR, "config", "ports.yaml"), encoding="utf-8") as f:
    PORTS = yaml.safe_load(f)["destination_ports"]

# 导入（必须在 __init__.py 存在后才行）
from utils.geocoder import geocode_gsi
from utils.osm_roads import query_osm_roads
from utils.rules import can_access_fcl
from utils.jp_address_parser_simple import parse

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/check", methods=["POST"])
def check():
    addrs = request.json.get("addresses", [])
    if isinstance(addrs, str):
        addrs = [addrs]
    results = []
    for addr in addrs:
        addr = addr.strip()
        if not addr:
            continue
        parsed = {"city": "", "town": "", "rest": ""}
        try:
            parsed.update(parse(addr)._asdict())
        except: pass
        
        lat, lng = geocode_gsi(addr)
        if not lat:
            results.append({"address": addr, "error": "座標取得失敗"})
            continue
        
        roads = query_osm_roads(lat, lng)
        can_access, reason = can_access_fcl(roads, parsed)
        
        distances = [(p, (lat-p["lat"])**2 + (lng-p["lng"])**2) for p in PORTS]
        port = min(distances, key=lambda x: x[1])[0]
        
        results.append({
            "address": addr,
            "can_access": can_access,
            "reason": reason,
            "nearest_port": f"{port['name']}（{port['code']}）",
            "distance": "計算略"
        })
    return jsonify({"results": results})

handler = Mangum(app)
