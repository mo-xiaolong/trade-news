# 全球赢必看的新闻资讯

外贸 / 跨境 / 国际 / 国内 四大板块资讯看板，由 GitHub Actions 每小时自动更新。

## 部署步骤

### 1. 创建 GitHub 仓库
- 登录 GitHub，点击 New Repository
- 仓库名填 `trade-news`（或任意名字）
- 选择 Public
- 不要勾选 "Add a README file"
- 点击 Create Repository

### 2. 推送代码
```bash
cd trade-news-cloud
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/你的用户名/trade-news.git
git branch -M main
git push -u origin main
```

### 3. 添加微信推送密钥
- 进入仓库 Settings → Secrets and variables → Actions
- 点击 New repository secret
- Name 填 `SCT_KEY`
- Value 填你的 Server酱 SendKey
- 点击 Add secret

### 4. 启用 GitHub Pages
- 进入仓库 Settings → Pages
- Source 选择 "Deploy from a branch"
- Branch 选择 `main` / `root`
- 点击 Save
- 等待几分钟后访问 `https://你的用户名.github.io/trade-news/`

### 5. 验证
- 进入仓库 Actions 页面，可以看到定时任务
- 点击 "Trade News Update" workflow，可以手动触发测试
- 检查微信是否收到推送

## 自动运行计划
- **每整点**：抓取 RSS → 更新网站 → 自动提交
- **每天北京时间 8:00**：更新网站 + 推送资讯摘要到微信

## 数据来源
- 人民日报·财经 RSS（外贸/跨境板块）
- 人民日报·国际 RSS（国际板块）
- 人民日报·时政 RSS（国内板块）
