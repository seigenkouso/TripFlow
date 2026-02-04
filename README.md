# ✈️ TripFlow | AI 智能行程规划助手

> 基于腾讯云混元大模型 (Hunyuan-Pro) 的全栈旅行规划应用。输入目的地与偏好，一键生成 "小红书风格" 的详细行程单。

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.3%2B-green)
![Tencent Cloud](https://img.shields.io/badge/AI-Hunyuan--Pro-violet)
![License](https://img.shields.io/badge/License-MIT-orange)

## 📖 项目简介

**[TripFlow](http://124.223.17.89/)** 是一个现代化的 Web 旅行助手，旨在解决“做攻略难”的痛点。
它利用大语言模型（LLM）的推理能力，根据用户的目的地、天数和个性化标签（如：购物血拼、人文历史、自然风光），自动生成包含景点、时间安排、推荐理由的结构化行程。

项目采用前后端分离的设计思想（逻辑分离，物理部署在 Flask 模板中），并集成了完整的用户认证与数据持久化系统。

## ✨ 核心功能

* **🤖 AI 智能规划**：接入腾讯云 Hunyuan-Pro 模型，秒级生成详细行程。
* **🔐 安全认证体系**：支持邮箱验证码注册/登录（SMTP 服务），保障账户安全。
* **💾 数据持久化**：
    * **历史记录**：自动保存每一次生成的行程，随时回溯。
    * **我的收藏**：支持对心仪行程进行收藏管理。
* **🎨 沉浸式 UI**：采用磨砂玻璃 (Glassmorphism) 拟态设计，响应式布局适配移动端与 PC 端。
* **🛡️ 企业级配置**：使用 `python-dotenv` 管理敏感密钥，确保生产环境安全。

## 🛠️ 技术栈

| 模块 | 技术选型 | 说明 |
| :--- | :--- | :--- |
| **后端** | Python, Flask | 轻量级 Web 框架，处理 API 与路由 |
| **数据库** | SQLite, SQLAlchemy | ORM 映射，无需配置繁重数据库 |
| **前端** | HTML5, CSS3, JS | 原生开发，Fetch API 异步交互 |
| **AI 模型** | Tencent Cloud SDK | 调用混元大模型 API |
| **部署** | Ubuntu, Gunicorn/Nginx | 生产环境支持 |

## 📂 目录结构
```Plaintext
TripFlow/
├── app.py              # Flask 后端核心入口
├── travel.db           # 数据库文件
├── .env                # 环境变量配置
├── requirements.txt    # 项目依赖列表
├── static/             # 静态资源
│   ├── style.css       # 全局样式 (Glassmorphism)
│   └── script.js       # 前端逻辑 (Fetch, DOM操作)
└── templates/          # HTML 模板
    └── index.html      # 单页应用主视图
```

## 📜 许可证
本项目采用 MIT License 开源。

---
