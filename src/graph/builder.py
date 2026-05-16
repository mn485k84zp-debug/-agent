from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, StateGraph

from src.agents.rag_agent import EcommerceRAGAgent
from src.agents.sql_agent import AnalyticsSQLAgent
from src.agents.supervisor import SupervisorAgent
from src.core.config import get_settings
from src.core.logging_config import setup_logging
from src.core.memory import MemoryManager
from src.core.types import AgentState
from src.llm.factory import build_chat_model
from src.tools.registry import ToolRegistry


class EcommerceAgentApplication:
    """对外暴露的应用入口，内部维护跨轮对话状态。"""

    def __init__(self, graph) -> None:
        self.graph = graph
        self.state: AgentState = {
            "main_messages": [],
            "summary": "",
            "agent_sessions": {"rag": [], "sql": []},
            "tool_traces": [],
        }

    def invoke(self, payload: dict) -> AgentState:
        merged = {**self.state, **payload}
        self.state = self.graph.invoke(merged)
        return self.state


def build_application() -> EcommerceAgentApplication:
    setup_logging()
    settings = get_settings()
    llm = build_chat_model(settings)
    memory_manager = MemoryManager(
        llm=llm,
        max_recent_turns=settings.memory_max_recent_turns,
        token_threshold=settings.memory_token_threshold,
    )
    tool_registry = ToolRegistry(settings)
    supervisor = SupervisorAgent(llm)
    rag_agent = EcommerceRAGAgent(llm, settings, tool_registry)
    sql_agent = AnalyticsSQLAgent(llm, settings)

    def prepare_memory(state: AgentState) -> AgentState:
        main_messages = list(state.get("main_messages", []))
        main_messages.append(HumanMessage(content=state["user_input"]))
        summary, recent_messages = memory_manager.update(
            summary=state.get("summary", ""),
            messages=main_messages,
        )
        return {"main_messages": recent_messages, "summary": summary}

    def supervisor_node(state: AgentState) -> AgentState:
        shared_context = memory_manager.build_context_messages(
            summary=state.get("summary", ""),
            recent_messages=state.get("main_messages", [])[:-1],
        )
        decision = supervisor.decide(state["user_input"], shared_context)
        return {
            "route": decision.route,
            "route_reason": decision.reason,
            "rag_subtask": decision.rag_subtask or state["user_input"],
            "sql_subtask": decision.sql_subtask or state["user_input"],
        }

    def rag_node(state: AgentState) -> AgentState:
        sessions = dict(state.get("agent_sessions", {}))
        shared_context = memory_manager.build_context_messages(
            summary=state.get("summary", ""),
            recent_messages=state.get("main_messages", [])[:-1],
        )
        answer, docs, traces, new_session = rag_agent.run(
            query=state.get("rag_subtask", state["user_input"]),
            shared_context_messages=shared_context,
            session_messages=sessions.get("rag", []),
        )
        sessions["rag"] = new_session
        return {
            "rag_answer": answer,
            "rag_documents": docs,
            "tool_traces": traces,
            "agent_sessions": sessions,
        }

    def sql_node(state: AgentState) -> AgentState:
        sessions = dict(state.get("agent_sessions", {}))
        shared_context = memory_manager.build_context_messages(
            summary=state.get("summary", ""),
            recent_messages=state.get("main_messages", [])[:-1],
        )
        answer, new_session = sql_agent.run(
            query=state.get("sql_subtask", state["user_input"]),
            shared_context_messages=shared_context,
            session_messages=sessions.get("sql", []),
        )
        sessions["sql"] = new_session
        return {"sql_answer": answer, "agent_sessions": sessions}

    def synthesize_node(state: AgentState) -> AgentState:
        prompt = f"""
你是最终汇总 Agent，请基于各个子代理的结果生成对用户的最终答复。

用户问题：
{state["user_input"]}

Supervisor 路由原因：
{state.get("route_reason", "")}

RAG Agent 输出：
{state.get("rag_answer", "（无）")}

SQL Agent 输出：
{state.get("sql_answer", "（无）")}

工具错误轨迹：
{chr(10).join(state.get("tool_traces", [])) or "（无）"}
"""
        final = llm.invoke([HumanMessage(content=prompt)])
        final_answer = final.content if isinstance(final.content, str) else str(final.content)

        main_messages = list(state.get("main_messages", []))
        main_messages.append(AIMessage(content=final_answer))
        summary, recent_messages = memory_manager.update(
            summary=state.get("summary", ""),
            messages=main_messages,
        )
        return {
            "final_answer": final_answer,
            "main_messages": recent_messages,
            "summary": summary,
        }

    def route_from_supervisor(state: AgentState) -> str:
        return "sql" if state.get("route") == "sql" else "rag"

    def route_after_rag(state: AgentState) -> str:
        return "sql" if state.get("route") == "both" else "synthesize"

    workflow = StateGraph(AgentState)
    workflow.add_node("prepare_memory", prepare_memory)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("rag_agent", rag_node)
    workflow.add_node("sql_agent", sql_node)
    workflow.add_node("synthesize", synthesize_node)

    workflow.add_edge(START, "prepare_memory")
    workflow.add_edge("prepare_memory", "supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {"rag": "rag_agent", "sql": "sql_agent"},
    )
    workflow.add_conditional_edges(
        "rag_agent",
        route_after_rag,
        {"sql": "sql_agent", "synthesize": "synthesize"},
    )
    workflow.add_edge("sql_agent", "synthesize")
    workflow.add_edge("synthesize", END)

    graph = workflow.compile()
    return EcommerceAgentApplication(graph)
