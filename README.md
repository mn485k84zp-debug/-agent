# 电商客服与数据分析 Agent

一个基于 Python、LangGraph 与阿里百炼 DashScope 的企业级多 Agent 示例工程，覆盖以下关键能力：

- 企业级 RAG：语义切分、Query 改写、混合检索、Rerank、防御性 Embedding 清洗
- Text-to-SQL：表结构向量检索，避免把全部 Schema 塞进 Prompt
- 稳健 Tool Calling：Pydantic 入参、异常捕获、有限重试、自修复回传
- Tool RAG：从工具池中动态检索最相关工具，而不是把 100+ 工具全部注入 Prompt
- 分层记忆：滑动窗口 + 动态摘要，缓解长上下文爆炸
- 多 Agent：Supervisor 调度 RAG Agent 与 SQL Agent 协同完成任务

## 目录结构

```text
ecommerce_cs_agent/
├── .env.example
├── README.md
├── app.py
├── requirements.txt
├── data/
│   ├── chroma/
│   ├── docs/
│   │   ├── faq.md
│   │   └── policies.md
│   └── sqlite/
├── scripts/
│   ├── build_indexes.py
│   └── init_demo_db.py
└── src/
    ├── __init__.py
    ├── agents/
    ├── core/
    ├── graph/
    ├── llm/
    ├── rag/
    ├── sql_agent/
    └── tools/
```

## 快速启动

```bash
pip install -r requirements.txt
copy .env.example .env
python scripts/init_demo_db.py
python scripts/build_indexes.py
python app.py
```

## 关键环境变量

- `DASHSCOPE_API_KEY`：阿里百炼 API Key
- `DASHSCOPE_BASE_URL`：默认 `https://dashscope.aliyuncs.com/compatible-mode/v1`
- `LLM_MODEL`：推荐 `qwen-plus` 或 `qwen-max`
- `EMBEDDING_MODEL`：推荐 `text-embedding-v3`
- `RERANK_MODEL`：推荐 `gte-rerank-v2`

## 说明

- 聊天模型通过 DashScope OpenAI 兼容接口接入。
- Rerank 通过 DashScope SDK 调用官方重排序接口。
- SQLite 仅作为本地演示数据源，生产环境可替换为 MySQL、PostgreSQL 或数据仓库。
