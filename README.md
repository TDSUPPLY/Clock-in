# 🕒 Clock-in 系统

一个基于 Flask + Supabase 的员工打卡系统。

## 🚀 功能
- 登录/注册（本地 session）
- 上下班、午餐、加班打卡
- 自动计算迟到早退、午餐超时
- 月度导出统计报表（CSV）
- 支持 Render 部署

## 🛠️ 使用技术
- Flask + Jinja2
- PostgreSQL（Supabase 托管）
- SQLAlchemy + python-dotenv
- GitHub + Render 自动部署

## ⚙️ 环境变量（.env）
```env
DATABASE_URL=postgresql://...
