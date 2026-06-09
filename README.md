# ✍️ AI 小说创作助手

一个基于 AI 的中文小说创作工具，帮助你从灵感到成书全流程创作。

## ✨ 功能特性

| 功能 | 说明 |
|------|------|
| 📋 大纲生成 | 输入题材和设定，AI 自动生成完整小说大纲 |
| 👥 角色管理 | 自动生成主要角色设定和人物关系 |
| 📝 章节写作 | 基于大纲自动生成章节正文，保持情节连贯 |
| ✨ 文本润色 | 多种润色模式，提升文笔和质量 |
| ➡️ 智能续写 | 基于已有内容自动续写，突破写作瓶颈 |
| 💾 导出成书 | 一键导出为 TXT 文件，方便后续编辑 |

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

支持 OpenAI、DeepSeek 等兼容 API，在应用侧边栏填入：

- **API Key**：你的 API Key
- **API Base URL**：DeepSeek 填 `https://api.deepseek.com/v1`
- **模型名称**：DeepSeek 填 `deepseek-chat`

### 3. 启动应用

```bash
streamlit run app.py
```

浏览器访问 `http://localhost:8501` 即可使用！

## 📖 使用流程

```
输入设定 → 生成大纲 → 逐章生成 → 编辑润色 → 导出成书
```

1. **新建小说**：选择题材，描述你的故事设定
2. **大纲管理**：查看 AI 生成的标题、简介、角色、章节大纲
3. **章节写作**：逐章生成正文，支持续写和手动编辑
4. **文本润色**：粘贴文本，选择润色模式，一键优化
5. **导出小说**：汇总所有章节，下载为 TXT 文件

## 🛠️ 技术栈

- **Python 3.10+**
- **Streamlit** — Web UI
- **OpenAI SDK** — 兼容多种 AI 模型

## 📁 项目结构

```
ai-novel-writer/
├── app.py              # Streamlit Web 主界面
├── novel_generator.py   # 核心生成逻辑
├── requirements.txt     # 依赖列表
└── README.md           # 项目说明
```

## 🔮 后续迭代计划

- [ ] 角色关系图谱可视化
- [ ] 多 Agent 协作（策划 Agent + 写作 Agent）
- [ ] 支持本地模型（Ollama）
- [ ] 导出 EPUB / PDF 格式
- [ ] 章节版本管理
- [ ] 世界观设定管理

## 📝 License

MIT License — 自由使用和修改！

---

⭐ 如果这个项目对你有帮助，欢迎 Star！
