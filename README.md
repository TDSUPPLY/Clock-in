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

## ⚙️ 环境变量（`.env`）

使用 Supabase 提供的 Transaction Pooler 连接方式，避免 Render 无法访问主机。

```env
# Supabase 数据库连接字符串（建议使用 Transaction Pooler）
DATABASE_URL=postgresql://postgres.vsyfhmuobenltfjsuhag:TDSUPPLY202020@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres
