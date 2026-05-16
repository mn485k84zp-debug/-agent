from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from src.web.knowledge_base import KnowledgeBaseManager
from src.web.service import AgentRuntimeService


runtime = AgentRuntimeService()
knowledge_manager = KnowledgeBaseManager()


@asynccontextmanager
async def lifespan(_: FastAPI):
    runtime.bootstrap()
    yield


app = FastAPI(
    title="电商客服与数据分析 Agent API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    session_id: str | None = Field(default=None, description="会话 ID，首次对话可为空")
    message: str = Field(..., description="用户输入")


class DataQueryRequest(BaseModel):
    question: str = Field(..., description="自然语言数据分析问题")
    session_id: str | None = Field(default=None, description="可选会话 ID")


def sse_event(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@app.exception_handler(Exception)
async def global_exception_handler(_, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": f"服务异常：{str(exc)}"},
    )


@app.get("/health")
async def health():
    return {"success": True, "message": "ok"}


@app.get("/sessions")
async def list_sessions():
    return {"success": True, "data": runtime.list_sessions()}


@app.post("/sessions")
async def create_session():
    return {"success": True, "data": runtime.create_session()}


@app.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    return {"success": True, "data": runtime.get_session_detail(session_id)}


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    runtime.delete_session(session_id)
    return {"success": True, "message": "会话已删除"}


@app.post("/chat")
async def chat(request: ChatRequest):
    session = runtime.ensure_session(request.session_id)

    async def event_generator():
        yield sse_event(
            {
                "type": "session",
                "session_id": session["session_id"],
                "title": session["title"],
            }
        )
        yield sse_event({"type": "status", "stage": "thinking", "message": "正在思考用户意图"})
        await asyncio.sleep(0.05)
        yield sse_event({"type": "status", "stage": "retrieving", "message": "正在检索知识库"})
        await asyncio.sleep(0.05)
        if runtime.should_hint_sql(request.message):
            yield sse_event({"type": "status", "stage": "analyzing", "message": "正在查询结构化数据"})
            await asyncio.sleep(0.05)

        try:
            result = await asyncio.to_thread(runtime.chat, session["session_id"], request.message)
            final_text = result["answer"]
            for char in final_text:
                yield sse_event({"type": "delta", "content": char})
                await asyncio.sleep(0.003)

            yield sse_event(
                {
                    "type": "done",
                    "data": {
                        "route": result["route"],
                        "route_reason": result["route_reason"],
                        "tool_traces": result["tool_traces"],
                        "session": runtime.get_session_detail(session["session_id"]),
                    },
                }
            )
        except Exception as exc:
            yield sse_event({"type": "error", "message": f"对话失败：{str(exc)}"})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/documents")
async def list_documents():
    return {"success": True, "data": knowledge_manager.list_documents()}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    data = await file.read()
    result = knowledge_manager.save_and_rebuild(file.filename, data)
    return {"success": True, "message": "文档已成功加入知识库", "data": result}


@app.delete("/documents/{file_name}")
async def delete_document(file_name: str):
    result = knowledge_manager.delete_document(file_name)
    return {"success": True, "message": "文档已删除", "data": result}


@app.post("/query_data")
async def query_data(request: DataQueryRequest):
    try:
        result = runtime.query_data(request.question, request.session_id)
        return {"success": True, "data": result}
    except Exception as exc:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": f"数据分析失败：{str(exc)}"},
        )


@app.get("/status")
async def status(session_id: str | None = None):
    return {"success": True, "data": runtime.get_status(session_id)}


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run("api:app", host=host, port=port, reload=True)
