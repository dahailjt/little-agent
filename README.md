# Little Agent 🤖

一个基于 DeepSeek 的多工具 AI Agent，使用 OpenAI 兼容接口实现 5 个工具的自动调度。

## 功能

| 工具 | 功能 | 数据来源 |
|---|---|---|
| 🌤️ `get_weather` | 查询城市实时天气 | wttr.in |
| 🧮 `calculate` | 数学表达式计算 | Python `eval` |
| 💡 `get_quote` | 随机名言/鸡汤 | hitokoto.cn |
| 🎓 `search_student_score` | 学生成绩语义搜索 | 本地 ChromaDB + Sentence-Transformers |
| 🌐 `translate` | 英语单词翻译 | MyMemory API |

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/<your-username>/little-agent.git
cd little-agent
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API Key

在项目根目录创建 `.env` 文件：

```
DEEPSEEK_API_KEY=sk-your-deepseek-api-key
```

> 💡 在 [DeepSeek 开放平台](https://platform.deepseek.com/) 注册并生成 API Key。

### 4. 准备学生数据（可选）

`students.txt` 里是学生成绩数据，每行一条。首次运行会自动初始化向量数据库。

### 5. 运行

```bash
python agent_rag.py
```

输入问题即可，例如：

- "广州今天天气怎么样？"
- "1+2*3 等于多少？"
- "谁数学成绩最好？"
- "翻译 apple"

输入 `quit` 或 `exit` 退出。

## 技术栈

- **LLM**：DeepSeek（OpenAI 兼容接口）
- **向量数据库**：ChromaDB（持久化本地）
- **Embedding**：Sentence-Transformers (`all-MiniLM-L6-v2`)
- **Tool Calling**：OpenAI Function Calling 协议

## 项目结构

```
little-agent/
├── agent_rag.py      # 主程序
├── students.txt      # 学生成绩数据
├── requirements.txt
├── .env.example      # 环境变量示例（真实 key 写在 .gitignore 的 .env）
├── .gitignore
└── README.md
```

## ⚠️ 注意事项

- **不要把 `.env` 提交到 Git** —— 它已被 `.gitignore` 排除
- **不要硬编码 API Key 到代码里** —— 用环境变量
- chroma_db/ 是自动生成的本地数据库，已被 `.gitignore` 排除

## License

MIT