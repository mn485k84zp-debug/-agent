from __future__ import annotations

import traceback

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import BaseTool

from src.core.exceptions import DeterministicToolError, TransientToolError
from src.core.retry import retry_with_backoff


class SafeToolExecutor:
    """稳健的工具执行器。"""

    def execute(self, ai_message: AIMessage, tools: list[BaseTool]) -> tuple[list[ToolMessage], list[str]]:
        tool_map = {tool.name: tool for tool in tools}
        tool_messages: list[ToolMessage] = []
        traces: list[str] = []

        for call in ai_message.tool_calls:
            tool_name = call["name"]
            args = call.get("args", {})
            tool_call_id = call.get("id", tool_name)
            tool = tool_map.get(tool_name)

            if not tool:
                content = f"TOOL_ERROR: 工具 {tool_name} 未注册，请检查工具名。"
                tool_messages.append(ToolMessage(content=content, name=tool_name, tool_call_id=tool_call_id))
                traces.append(content)
                continue

            try:
                result = retry_with_backoff(lambda: self._invoke_tool(tool, args), retries=3)
                content = result if isinstance(result, str) else str(result)
            except Exception as exc:
                content = (
                    "TOOL_ERROR: 工具执行失败，请基于报错修正参数后重试。\n"
                    f"{self._format_exception(exc)}"
                )
                traces.append(content)

            tool_messages.append(ToolMessage(content=content, name=tool_name, tool_call_id=tool_call_id))

        return tool_messages, traces

    def _invoke_tool(self, tool: BaseTool, args: dict) -> str:
        try:
            result = tool.invoke(args)
            return result if isinstance(result, str) else str(result)
        except (TimeoutError, ConnectionError) as exc:
            raise TransientToolError(str(exc)) from exc
        except (DeterministicToolError, ValueError, ModuleNotFoundError) as exc:
            raise exc
        except Exception as exc:
            raise DeterministicToolError(str(exc)) from exc

    def _format_exception(self, exc: Exception) -> str:
        return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
