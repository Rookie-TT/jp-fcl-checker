# 日本住所 FCL 到達性チェックツール

基于 Flask 的 Web 应用，用于检查日本地址是否可以进行集装箱（FCL）配送。支持多种车辆类型，自动计算最近港口和预估运输时间。

## ✨ 主要功能

### 🚚 车辆类型支持
- **40ft 拖车** - 最小道路宽度 3.5m
- **20ft 拖车** - 最小道路宽度 3.5m  
- **10t 飞翼车** - 最小道路宽度 3.2m
- **4t 飞翼车** - 最小道路宽度 3.0m
- **2t 箱型卡车** - 最小道路宽度 2.5m

### 📍 地址处理
- **智能地理编码** - GSI（日本国土地理院）+ Nominatim 双重保障
- **地址标准化** - 自动转换格式（如：4-6-16 → 4丁目6-16）
- **地址降级** - 详细地址找不到时自动尝试简化版本
- **批量处理** - 支持多行地址同时查询

### 🗺️ 道路分析
- **OSM 道路数据** - 查询周边道路宽度和类型
- **智能估算** - 根据道路类型估算宽度
- **规则判断** - 基于车辆类型和道路条件判断可达性

### 🚢 港口匹配
- **44个港口** - 覆盖日本全国（7个主要港口 + 37个地方港口）
- **自动计算** - 最近港口、距离和预估牵引时间
- **地区分类** - 北海道、東北、関東、中部、関西、中国地方、四国、九州、沖縄

### 🎨 用户界面
- **进度显示** - 实时进度条和加载动画
- **结果展示** - 清晰的可达性判断和理由说明
- **地址对比** - 显示原始地址和标准化后的地址
- **响应式设计** - 适配各种屏幕尺寸

## 🚀 快速开始

### 本地运行

```bash
# 1. 克隆项目
git clone <repository-url>
cd jp-fcl-checker-master

# 2. 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行应用
python run.py

# 5. 访问
http://localhost:5000
```

### Vercel 部署

#### 方式 1：通过 Vercel 网站（推荐）

1. 访问 [Vercel](https://vercel.com)
2. 点击 "Add New Project"
3. 导入你的 Git 仓库
4. Vercel 自动检测配置并部署
5. 获取部署 URL

#### 方式 2：通过 Vercel CLI

```bash
# 安装 CLI
npm install -g vercel

# 登录
vercel login

# 部署
vercel --prod
```

#### 方式 3：使用部署脚本

```bash
# Windows
deploy.bat

# Linux/Mac
chmod +x deploy.sh
./deploy.sh
```

详细部署说明请查看 [DEPLOYMENT.md](DEPLOYMENT.md)

## 📁 项目结构

```
jp-fcl-checker-master/
├── api/
│   └── index.py              # Flask 应用入口
├── config/
│   ├── ports.yaml            # 港口配置（44个港口）
│   └── vehicles.yaml         # 车辆配置（5种车辆）
├── templates/
│   └── index.html            # 前端页面（原生 HTML/CSS/JS）
├── utils/
│   ├── geocoder.py           # 地理编码（GSI + Nominatim）
│   ├── osm_roads.py          # OSM 道路查询
│   ├── rules.py              # FCL 可达性规则判断
│   ├── address_extractor.py  # 地址提取工具
│   └── jp_address_parser_simple.py  # 日本地址解析
├── vercel.json               # Vercel 配置
├── requirements.txt          # Python 依赖
├── run.py                    # 本地开发启动脚本
├── .gitignore                # Git 忽略配置
├── .vercelignore             # Vercel 忽略配置
├── deploy.bat / deploy.sh    # 部署脚本
├── DEPLOYMENT.md             # 详细部署文档
├── DEPLOYMENT_CHECKLIST.md   # 部署检查清单
└── README.md                 # 项目说明
```

## 🔧 技术栈

### 后端
- **Flask 3.0.3** - Web 框架
- **PyYAML 6.0.2** - 配置文件解析
- **Requests 2.32.3** - HTTP 请求

### 前端
- **原生 HTML5** - 页面结构
- **原生 CSS3** - 样式设计
- **原生 JavaScript** - 交互逻辑
- **Fetch API** - AJAX 请求

### 地理服务
- **GSI API** - 日本国土地理院地理编码
- **Nominatim API** - OpenStreetMap 地理编码
- **Overpass API** - OpenStreetMap 道路数据查询

### 部署
- **Vercel** - Serverless 部署平台

## 📖 使用说明

### 地址输入格式

系统支持多种日本地址格式：

✅ **推荐格式**
```
神奈川県横浜市鶴見区大黒ふ頭2丁目1番地
東京都中央区銀座4-6-16
福岡県福岡市博多区博多駅前2-20-1
```

✅ **简化格式**
```
横浜市鶴見区大黒ふ頭
東京都中央区銀座
福岡市博多区
```

✅ **英文格式**
```
Yokohama, Kanagawa
Tokyo, Chuo-ku
Fukuoka, Hakata
```

⚠️ **避免使用**
- 只有建筑物名称（如：○○ビル）
- 只有公司名称（如：株式会社○○）
- 过于模糊的描述（如：○○駅近く）

### 批量查询

在输入框中每行输入一个地址：

```
神奈川県横浜市鶴見区大黒ふ頭2丁目1番地
東京都中央区銀座4-6-16
京都府京都市東山区祇園町南側593-1
大阪府大阪市北区梅田1-13-1
```

点击"チェック実行"即可批量处理。

### 车辆类型选择

根据实际运输需求选择合适的车辆类型：

- **集装箱运输** → 选择 40ft 或 20ft 拖车
- **大型货物** → 选择 10t 飞翼车
- **中型货物** → 选择 4t 飞翼车  
- **小型货物** → 选择 2t 箱型卡车

## 🎯 判断规则

### 白名单（自动可达）
- 港口工业区（ふ頭、埠頭、港）
- 物流中心（物流センター、倉庫）
- 工业团地（工業団地）

### 黑名单（自动不可达）
- 高层建筑（タワー、ビル、階、F）
- 商业区（銀座、祇園、表参道、原宿）
- 观光地（博物館、動物園、公園）
- 古街区（町家、花见小路）

### 道路宽度判断
根据选择的车辆类型，系统会检查道路宽度是否满足要求：

| 车辆类型 | 车宽 | 最小道路宽度 |
|---------|------|-------------|
| 40ft拖车 | 2.5m | 3.5m |
| 20ft拖车 | 2.5m | 3.5m |
| 10t飞翼车 | 2.5m | 3.2m |
| 4t飞翼车 | 2.35m | 3.0m |
| 2t箱型卡车 | 2.1m | 2.5m |

## 🚢 港口列表

### 主要港口（7个）
- 東京港（Tokyo）
- 横浜港（Yokohama）
- 名古屋港（Nagoya）
- 大阪港（Osaka）
- 神戸港（Kobe）
- 博多港（Hakata）
- 門司港（Moji）

### 地方港口（37个）
覆盖北海道、東北、関東、中部、関西、中国地方、四国、九州、沖縄等地区。

完整列表请查看 [config/ports.yaml](config/ports.yaml)

## 🔌 API 接口

### POST /check

检查地址的 FCL 可达性

**请求体：**
```json
{
  "addresses": [
    "神奈川県横浜市鶴見区大黒ふ頭2丁目1番地",
    "東京都中央区銀座4-6-16"
  ],
  "vehicle_type": "40ft"
}
```

**响应：**
```json
{
  "results": [
    {
      "address": "神奈川県横浜市鶴見区大黒ふ頭2丁目1番地",
      "used_address": "神奈川県横浜市鶴見区大黒ふ頭2丁目",
      "can_access": true,
      "reason": "港湾・工業地区に位置、道路幅12m以上、40HQ対応可能",
      "nearest_port": "横浜港（JPYOK）",
      "distance": "約2.5km",
      "estimated_time": "予想牽引時間：5分"
    }
  ]
}
```

## ⚙️ 配置说明

### 添加新港口

编辑 `config/ports.yaml`：

```yaml
- name: "新港口名"
  code: "JPXXX"
  lat: 纬度
  lng: 经度
  type: "main"  # 或 "local"
  region: "地区名"
```

### 修改车辆配置

编辑 `config/vehicles.yaml`：

```yaml
vehicle_type:
  name: "车辆名称"
  length: 长度（米）
  width: 宽度（米）
  min_road_width: 最小道路宽度（米）
  description: "描述"
```

## 🐛 常见问题

### Q: 为什么某些地址返回"座標解析不可"？

**A:** 可能原因：
- 地址过于模糊（如只有建筑物名称）
- 地理编码 API 数据库中没有该地址
- 网络连接问题或 API 超时

**解决方案**：使用完整的街道地址或城市名。

### Q: 如何添加新的港口？

**A:** 编辑 `config/ports.yaml`，添加港口信息后重启应用即可。

### Q: 部署到 Vercel 后超时？

**A:** Vercel 免费版有 10 秒执行时间限制。如果地理编码 API 响应慢，考虑：
- 优化超时设置
- 使用缓存
- 升级 Vercel 套餐

### Q: 如何修改道路宽度判断规则？

**A:** 编辑 `utils/rules.py` 中的 `can_access_fcl` 函数，或修改 `config/vehicles.yaml` 中的 `min_road_width` 值。

## 📝 开发说明

### 本地开发

```bash
# 激活虚拟环境
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 运行开发服务器
python run.py

# 访问
http://localhost:5000
```

### 代码结构

- `api/index.py` - Flask 路由和业务逻辑
- `utils/geocoder.py` - 地理编码核心逻辑
- `utils/osm_roads.py` - OSM 道路查询
- `utils/rules.py` - 可达性判断规则
- `templates/index.html` - 前端页面

### 添加新功能

1. 后端逻辑 → 修改 `api/index.py` 或 `utils/` 模块
2. 前端界面 → 修改 `templates/index.html`
3. 配置数据 → 修改 `config/` 下的 YAML 文件

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题，请提交 GitHub Issue。

---

**Made with ❤️ for logistics professionals**
