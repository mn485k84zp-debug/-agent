from __future__ import annotations

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from src.core.message_utils import estimate_tokens, flatten_turns, group_messages_into_turns, render_message


class MemoryManager:
    """分层记忆管理器。

    目标是把“最近上下文可回看”与“历史结论可压缩保存”两件事拆开处理。
    """

    def __init__(self, llm, max_recent_turns: int = 5, token_threshold: int = 8000) -> None:
        self.llm = llm
        self.max_recent_turns = max_recent_turns
        self.token_threshold = token_threshold

    def update(self, summary: str, messages: list[BaseMessage]) -> tuple[str, list[BaseMessage]]:
        """更新记忆，必要时触发历史摘要压缩。"""
        turns = group_messages_into_turns(messages)
        total_tokens = estimate_tokens(summary) + sum(turn.approx_tokens for turn in turns)

        if total_tokens <= self.token_threshold or len(turns) <= self.max_recent_turns:
            return summary, flatten_turns(turns[-self.max_recent_turns :])

        old_turns = turns[:-self.max_recent_turns]
        recent_turns = turns[-self.max_recent_turns :]
        merged_summary = self._summarize(summary, old_turns)
        return merged_summary, flatten_turns(recent_turns)

    def _summarize(self, existing_summary: str, old_turns) -> str:
        history_text = "\n".join(
            "\n".join(render_message(message) for message in turn.messages)
            for turn in old_turns
        )
        prompt = f"""
你是企业级 Agent 的记忆压缩器。请将历史对话压缩为稳定摘要，保留：
1. 用户身份、偏好、约束和重要上下文
2. 已确认的业务结论、承诺、澄清
3. 关键工具调用及结果
4. 未解决事项与下一步

已有摘要：
{existing_summary or "（空）"}

待压缩历史：
{history_text}
"""
        result = self.llm.invoke([HumanMessage(content=prompt)])
        return result.content if isinstance(result.content, str) else str(result.content)

    def build_context_messages(self, summary: str, recent_messages: list[BaseMessage]) -> list[BaseMessage]:
        """拼接摘要与最近窗口，作为本轮推理的上下文。"""
        messages: list[BaseMessage] = []
        if summary.strip():
            messages.append(
                SystemMessage(
                    content=(
                        "以下是系统维护的长期摘要，请把它视为高优先级历史记忆。\n"
                        f"{summary}"
                    )
                )
            )
        messages.extend(recent_messages)
        return messages
