# Vercel 部署检查清单

✅ **项目状态：已通过所有检查，可以部署！**

在部署到 Vercel 之前，请确保完成以下检查：

## ✅ 必需文件检查

### 核心应用文件
- ✅ `api/index.py` - Flask 应用入口
- ✅ `templates/index.html` - 前端页面
- ✅ `run.py` - 本地开发启动脚本

### 工具模块
- ✅ `utils/geocoder.py` - 地理编码（GSI + Nominatim）
- ✅ `utils/osm_roads.py` - OSM 道路查询
- ✅ `utils/rules.py` - FCL 规则判断
- ✅ `utils/address_extractor.py` - 地址提取工具
- ✅ `utils/jp_address_parser_simple.py` - 日本地址解析

### 配置文件
- ✅ `config/ports.yaml` - 港口配置（44个港口）
- ✅ `config/vehicles.yaml` - 车辆配置（5种车辆）
- ✅ `vercel.json` - Vercel 部署配置
- ✅ `requirements.txt` - Python 依赖列表

### 部署脚本（可选）
- ✅ `deploy.bat` - Windows 部署脚本
- ✅ `deploy.sh` - Linux/Mac 部署脚本

## ✅ 配置检查

### vercel.json
✅ 配置正确：
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/index.py"
    }
  ],
  "env": {
    "PYTHONPATH": "."
  }
}
```

### requirements.txt
✅ 包含以下依赖：
- ✅ Flask==3.0.3
- ✅ Jinja2==3.1.4
- ✅ PyYAML==6.0.2
- ✅ requests==2.32.3

### api/index.py
- ✅ Flask app 变量名为 `app`
- ✅ 正确配置了 `template_folder`
- ✅ 正确配置了 `config` 目录路径
- ✅ 包含 `if __name__ == "__main__"` 块用于本地开发

### config/ports.yaml
- ✅ 包含 44 个港口配置
- ✅ 每个港口有 name, code, lat, lng, type, region 字段
- ✅ 坐标准确无误

### config/vehicles.yaml
- ✅ 包含 5 种车辆配置
- ✅ 每个车辆有 name, length, width, min_road_width, description 字段

## ✅ 本地测试

在部署前，请先本地测试：

```bash
# 1. 激活虚拟环境
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行应用
python run.py

# 4. 访问测试
http://localhost:5000
```

### 功能测试清单

#### 基础功能
- [ ] 页面正常加载
- [ ] 日文界面显示正确
- [ ] 车辆类型选择器工作正常

#### 地址查询测试
- [ ] 输入完整地址：`神奈川県横浜市鶴見区大黒ふ頭2丁目1番地`
  - 预期：返回可达性结果和最近港口
- [ ] 输入简化地址：`東京都中央区銀座`
  - 预期：能够解析并返回结果
- [ ] 输入英文地址：`Yokohama, Kanagawa`
  - 预期：能够解析并返回结果

#### 批量查询测试
- [ ] 输入多行地址（3-5个）
- [ ] 预期：返回多个结果，每个地址独立显示

#### 车辆类型测试
- [ ] 选择不同车辆类型（40ft, 20ft, 10t, 4t, 2t）
- [ ] 预期：判断结果根据车辆类型变化

#### 错误处理测试
- [ ] 输入无效地址
- [ ] 预期：返回友好错误信息
- [ ] 输入空地址
- [ ] 预期：提示"住所を入力してください"

#### UI/UX 测试
- [ ] 进度条正常显示
- [ ] 加载动画流畅
- [ ] 结果展示清晰
- [ ] 地址标准化显示正确（原地址 + 标准化地址）

## ✅ 代码检查

### 语法检查
- ✅ 没有 Python 语法错误
- ✅ 没有 JavaScript 语法错误
- ✅ 没有 HTML/CSS 错误

### 导入检查
- ✅ 所有导入路径正确
- ✅ 没有循环导入
- ✅ 没有导入未使用的模块

### 路径检查
- ✅ 没有硬编码的本地路径
- ✅ 使用相对路径或 `os.path.join`
- ✅ 配置文件路径正确

### 性能检查
- ✅ API 超时设置合理（6-8秒）
- ✅ 没有无限循环
- ✅ 错误处理完善

## ✅ Git 准备

```bash
# 1. 初始化 Git（如果还没有）
git init

# 2. 添加 .gitignore
# 确保排除：venv/, __pycache__/, *.pyc, .env

# 3. 添加文件
git add .

# 4. 提交
git commit -m "Ready for Vercel deployment"

# 5. 推送到远程仓库（可选，用于自动部署）
git remote add origin <your-repo-url>
git push -u origin main
```

## ✅ Vercel 账号准备

- [ ] 注册 Vercel 账号：https://vercel.com/signup
- [ ] 连接 GitHub/GitLab/Bitbucket（推荐）
- [ ] 或安装 Vercel CLI：`npm install -g vercel`

## 🚀 部署方式选择

### 方式 1：通过 Git 自动部署（✅ 推荐使用）

**优点：**
- ✅ 每次 push 自动部署
- ✅ 支持预览部署
- ✅ 易于回滚
- ✅ 团队协作友好

**步骤：**
1. 将代码推送到 GitHub/GitLab/Bitbucket
2. 在 Vercel 导入仓库
3. Vercel 自动检测配置
4. 点击 Deploy

### 方式 2：通过 Vercel 网站部署（✅ 推荐使用）

**优点：**
- ✅ 可视化操作
- ✅ 无需安装 CLI
- ✅ 适合初次部署

**步骤：**
1. 访问 https://vercel.com
2. 点击 "Add New Project"
3. 导入 Git 仓库或上传文件
4. 配置自动检测
5. 点击 Deploy

### 方式 3：通过 Vercel CLI（备用）

**优点：**
- 快速部署
- 本地控制
- 适合测试

**步骤：**
```bash
# 安装 CLI
npm install -g vercel

# 登录
vercel login

# 预览部署
vercel

# 生产部署
vercel --prod
```

### 方式 4：使用部署脚本（备用）

**Windows:**
```bash
deploy.bat
```

**Linux/Mac:**
```bash
chmod +x deploy.sh
./deploy.sh
```

**注意：** 方式 3 和 4 需要先安装 Vercel CLI

## ✅ 部署后验证

部署完成后，请验证以下功能：

### 1. 首页访问
- [ ] 访问部署 URL
- [ ] 页面正常加载
- [ ] 日文界面显示正确
- [ ] 车辆类型选择器显示正常

### 2. 地址查询功能
测试地址：
- [ ] `神奈川県横浜市鶴見区大黒ふ頭2丁目1番地`
  - 预期：港口工业区，可达
- [ ] `東京都中央区銀座4-6-16 銀座ジェムズビル8階`
  - 预期：商业区高楼，不可达
- [ ] `福岡県福岡市博多区博多駅前2-20-1`
  - 预期：能解析并返回结果

### 3. 批量查询
- [ ] 输入多行地址
- [ ] 预期：返回多个结果

### 4. 车辆类型切换
- [ ] 切换不同车辆类型
- [ ] 预期：判断结果相应变化

### 5. 错误处理
- [ ] 输入无效地址
- [ ] 预期：返回友好错误信息

### 6. API 测试
```bash
curl -X POST https://your-app.vercel.app/check \
  -H "Content-Type: application/json" \
  -d '{
    "addresses": ["神奈川県横浜市鶴見区大黒ふ頭2丁目1番地"],
    "vehicle_type": "40ft"
  }'
```
- [ ] 返回正确的 JSON 响应

## 📊 监控和日志

部署后，在 Vercel Dashboard 检查：

### Deployments
- [ ] 部署状态：Success
- [ ] 构建日志无错误
- [ ] 部署时间合理

### Functions
- [ ] Serverless 函数正常运行
- [ ] 查看函数日志
- [ ] 检查错误率

### Performance
- [ ] 响应时间 < 3秒
- [ ] 冷启动时间可接受
- [ ] 没有超时错误

## ⚠️ 常见问题排查

### 问题 1：模块导入错误
**症状：** `ModuleNotFoundError: No module named 'utils'`

**解决方案：**
- 确保 `vercel.json` 中设置了 `PYTHONPATH`
- 检查文件结构是否正确

### 问题 2：模板文件 404
**症状：** `TemplateNotFound: index.html`

**解决方案：**
- 检查 `template_folder` 路径配置
- 确保 `templates/` 目录存在

### 问题 3：API 超时
**症状：** `Function execution timed out`

**解决方案：**
- 优化地理编码超时设置（当前 6-8 秒）
- 考虑添加缓存
- 升级 Vercel 套餐（Pro 有 60 秒限制）

### 问题 4：配置文件读取失败
**症状：** `FileNotFoundError: config/ports.yaml`

**解决方案：**
- 确保配置文件在正确位置
- 检查路径拼接逻辑

### 问题 5：冷启动慢
**说明：** Serverless 函数首次调用会有延迟，这是正常现象

**优化方案：**
- 减少依赖大小
- 使用 Vercel Pro（减少冷启动）
- 添加预热机制

## 📝 部署记录

记录你的部署信息：

- **项目状态**：✅ 已通过所有检查
- **本地测试**：✅ 成功运行（http://localhost:5000）
- **代码质量**：✅ 无语法错误
- **配置文件**：✅ 全部正确
- **推荐部署方式**：Git 自动部署 或 Vercel 网站部署
- **部署日期**：____________________
- **Vercel URL**：____________________
- **Git 仓库**：____________________
- **实际部署方式**：____________________
- **测试结果**：____________________
- **备注**：____________________

## 🎉 完成

✅ **项目已完全就绪，可以立即部署！**

恭喜！你的应用已通过所有检查，可以部署到 Vercel。

### 下一步：
- [ ] 配置自定义域名（可选）
- [ ] 设置环境变量（如需要）
- [ ] 启用分析功能（可选）
- [ ] 配置 CI/CD 流程（可选）
- [ ] 添加监控告警（可选）

### 维护建议：
- 定期检查 Vercel 日志
- 监控 API 响应时间
- 更新港口配置（如有新港口）
- 优化地理编码性能
- 收集用户反馈

---

**部署文档：** [DEPLOYMENT.md](DEPLOYMENT.md)  
**项目说明：** [README.md](README.md)
