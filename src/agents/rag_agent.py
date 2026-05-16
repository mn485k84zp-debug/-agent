from __future__ import annotations

from langchain_core.documents import Document
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from src.core.config import Settings
from src.rag.retriever import HybridRetriever
from src.tools.executor import SafeToolExecutor
from src.tools.registry import ToolRegistry


class EcommerceRAGAgent:
    """负责客服知识问答与工具协同。"""

    def __init__(self, llm, settings: Settings, tool_registry: ToolRegistry) -> None:
        self.llm = llm
        self.settings = settings
        self.retriever = HybridRetriever(settings, llm)
        self.tool_registry = tool_registry
        self.tool_executor = SafeToolExecutor()

    def run(
        self,
        query: str,
        shared_context_messages: list[BaseMessage],
        session_messages: list[BaseMessage],
    ) -> tuple[str, list[Document], list[str], list[BaseMessage]]:
        docs = self.retriever.retrieve(query)
        selected_tools = self.tool_registry.retrieve(query)

        knowledge_context = "\n\n".join(
            f"[文档{i + 1}] 来源={doc.metadata.get('source')} | 标题路径={doc.metadata.get('heading_path')}\n{doc.page_content}"
            for i, doc in enumerate(docs)
        ) or "未检索到知识文档。"

        system_prompt = f"""
你是企业级电商客服 Agent。

你的工作方式：
1. 先基于知识库回答
2. 当用户问题涉及订单、库存、售后登记等实时信息时，优先调用工具
3. 如果工具返回 TOOL_ERROR，请阅读报错并修正参数后重试
4. 回答必须清晰、专业、可执行，不要编造事实

本轮可用知识上下文：
{knowledge_context}
"""

        conversation = [
            SystemMessage(content=system_prompt),
            *shared_context_messages,
            *session_messages,
            HumanMessage(content=query),
        ]
        working_session: list[BaseMessage] = [HumanMessage(content=query)]
        llm_with_tools = self.llm.bind_tools(selected_tools)

        traces: list[str] = []
        for _ in range(self.settings.tool_max_self_heal_rounds):
            ai_message = llm_with_tools.invoke(conversation)
            conversation.append(ai_message)
            working_session.append(ai_message)

            if not getattr(ai_message, "tool_calls", None):
                content = ai_message.content if isinstance(ai_message.content, str) else str(ai_message.content)
                new_session = session_messages + working_session
                return content, docs, traces, new_session

            tool_messages, new_traces = self.tool_executor.execute(ai_message, selected_tools)
            traces.extend(new_traces)
            conversation.extend(tool_messages)
            working_session.extend(tool_messages)

        fallback_prompt = (
            "工具调用已经达到最大自修复次数。请基于已有知识和错误信息，"
            "给出保守、透明的答复，并明确告诉用户哪些信息无法继续自动完成。"
        )
        final_message = self.llm.invoke(conversation + [HumanMessage(content=fallback_prompt)])
        final_text = final_message.content if isinstance(final_message.content, str) else str(final_message.content)
        working_session.append(AIMessage(content=final_text))
        new_session = session_messages + working_session
        return final_text, docs, traces, new_session
