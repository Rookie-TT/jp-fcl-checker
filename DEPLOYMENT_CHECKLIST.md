# Vercel 部署检查清单

在部署到 Vercel 之前，请确保完成以下检查：

## ✅ 必需文件检查

- [x] `api/index.py` - Flask 应用入口
- [x] `vercel.json` - Vercel 配置文件
- [x] `requirements.txt` - Python 依赖列表
- [x] `templates/index.html` - 前端页面
- [x] `config/ports.yaml` - 港口配置
- [x] `utils/` 目录及所有工具文件

## ✅ 配置检查

### vercel.json
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
确保包含以下依赖：
- Flask==3.0.3
- Jinja2==3.1.4
- PyYAML==6.0.2
- requests==2.32.3

### api/index.py
- [x] 移除了 `mangum` 导入
- [x] Flask app 变量名为 `app`
- [x] 正确配置了 `template_folder`
- [x] 正确配置了 `config` 目录路径

## ✅ 本地测试

在部署前，请先本地测试：

```bash
# 激活虚拟环境
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 运行应用
python run.py

# 测试功能
# 1. 访问 http://localhost:5000
# 2. 输入测试地址：北海道雨竜郡北竜町
# 3. 检查返回结果
```

## ✅ 代码检查

- [x] 没有语法错误
- [x] 所有导入路径正确
- [x] 没有硬编码的本地路径
- [x] 超时设置合理（<10秒）
- [x] 错误处理完善

## ✅ Git 准备

```bash
# 初始化 Git（如果还没有）
git init

# 添加文件
git add .

# 提交
git commit -m "Prepare for Vercel deployment"

# 推送到远程仓库（可选）
git remote add origin <your-repo-url>
git push -u origin main
```

## ✅ Vercel 账号准备

1. 注册 Vercel 账号：https://vercel.com/signup
2. 连接 GitHub/GitLab/Bitbucket（推荐）
3. 或安装 Vercel CLI：`npm install -g vercel`

## 🚀 部署方式选择

### 方式 1：通过 Git 自动部署（推荐）

1. 将代码推送到 GitHub/GitLab/Bitbucket
2. 在 Vercel 导入仓库
3. 每次 push 自动部署

### 方式 2：通过 Vercel CLI

```bash
# 登录
vercel login

# 预览部署
vercel

# 生产部署
vercel --prod
```

### 方式 3：使用部署脚本

```bash
# Windows
deploy.bat

# Linux/Mac
chmod +x deploy.sh
./deploy.sh
```

## ✅ 部署后验证

部署完成后，请验证以下功能：

1. **首页访问**
   - 访问部署 URL
   - 页面正常加载
   - 日文界面显示正确

2. **地址查询**
   - 输入：`北海道雨竜郡北竜町`
   - 预期：返回可达性结果和最近港口

3. **批量查询**
   - 输入多行地址
   - 预期：返回多个结果

4. **错误处理**
   - 输入无效地址
   - 预期：返回友好错误信息

5. **API 测试**
   ```bash
   curl -X POST https://your-app.vercel.app/check \
     -H "Content-Type: application/json" \
     -d '{"addresses": ["北海道雨竜郡北竜町"]}'
   ```

## 📊 监控和日志

部署后，在 Vercel Dashboard 检查：

1. **Deployments** - 部署历史和状态
2. **Functions** - Serverless 函数日志
3. **Analytics** - 访问统计（需要升级套餐）
4. **Logs** - 实时日志查看

## ⚠️ 常见问题

### 问题 1：模块导入错误
**解决方案**：确保 `vercel.json` 中设置了 `PYTHONPATH`

### 问题 2：模板文件 404
**解决方案**：检查 `template_folder` 路径配置

### 问题 3：API 超时
**解决方案**：
- 优化地理编码超时设置
- 考虑添加缓存
- 升级 Vercel 套餐

### 问题 4：冷启动慢
**说明**：Serverless 函数首次调用会有延迟，这是正常现象

## 📝 部署记录

记录你的部署信息：

- **部署日期**：____________________
- **Vercel URL**：____________________
- **Git 仓库**：____________________
- **部署方式**：____________________
- **测试结果**：____________________

## 🎉 完成

恭喜！你的应用已成功部署到 Vercel。

下一步：
- 配置自定义域名（可选）
- 设置环境变量（如需要）
- 启用分析功能（可选）
- 配置 CI/CD 流程（可选）
