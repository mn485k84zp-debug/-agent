from __future__ import annotations

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage

from src.core.types import ConversationTurn


def estimate_tokens(text: str) -> int:
    """使用轻量级近似估算 token 数。

    对于中英文混合电商场景，这个近似值足以用来触发摘要阈值，
    真正生产中可替换成模型对应 tokenizer。
    """

    return max(1, len(text) // 4)


def render_message(message: BaseMessage) -> str:
    if isinstance(message, ToolMessage):
        return f"[tool:{message.name}] {message.content}"
    if isinstance(message, HumanMessage):
        return f"[user] {message.content}"
    if isinstance(message, AIMessage):
        return f"[assistant] {message.content}"
    if isinstance(message, SystemMessage):
        return f"[system] {message.content}"
    return str(message.content)


def group_messages_into_turns(messages: list[BaseMessage]) -> list[ConversationTurn]:
    """按“用户消息开始，直到下一条用户消息前结束”的方式切成轮次。"""

    turns: list[ConversationTurn] = []
    buffer: list[BaseMessage] = []

    for message in messages:
        if isinstance(message, HumanMessage) and buffer:
            turns.append(
                ConversationTurn(
                    messages=buffer,
                    approx_tokens=sum(estimate_tokens(render_message(item)) for item in buffer),
                )
            )
            buffer = [message]
        else:
            buffer.append(message)

    if buffer:
        turns.append(
            ConversationTurn(
                messages=buffer,
                approx_tokens=sum(estimate_tokens(render_message(item)) for item in buffer),
            )
        )

    return turns


def flatten_turns(turns: list[ConversationTurn]) -> list[BaseMessage]:
    messages: list[BaseMessage] = []
    for turn in turns:
        messages.extend(turn.messages)
    return messages
