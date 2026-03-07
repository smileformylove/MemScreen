"""Chat HTTP routes."""

import asyncio
import json
import queue
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .. import deps

router = APIRouter(prefix="/chat", tags=["chat"])
_executor = ThreadPoolExecutor(max_workers=2)


class ChatMessageBody(BaseModel):
    message: str
    thread_id: Optional[str] = None


class ChatReplyResponse(BaseModel):
    reply: Optional[str] = None
    error: Optional[str] = None


class SetModelBody(BaseModel):
    model: str


class ChatThreadCreateBody(BaseModel):
    title: str = ""


class ChatThreadSwitchBody(BaseModel):
    thread_id: str


@router.post("", response_model=ChatReplyResponse)
async def chat_post(body: ChatMessageBody):
    """Non-streaming chat: send message, get full reply."""
    presenter = deps.get_chat_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Chat not available")
    if body.thread_id and not presenter.switch_chat_thread(body.thread_id):
        raise HTTPException(status_code=404, detail=f"Chat thread not found: {body.thread_id}")

    loop = asyncio.get_event_loop()
    result = [None, None]
    done = threading.Event()

    def on_done(ai_text: str, error_text: Optional[str]):
        result[0], result[1] = ai_text, error_text
        done.set()

    presenter.send_message_sync(body.message, on_done=on_done)
    await loop.run_in_executor(_executor, lambda: done.wait(180))
    ai_text, error_text = result[0], result[1]
    if ai_text is None and error_text is None:
        return ChatReplyResponse(reply=None, error="Chat request timed out")
    if error_text:
        return ChatReplyResponse(reply=None, error=error_text)
    return ChatReplyResponse(reply=ai_text, error=None)


@router.post("/stream")
async def chat_stream(body: ChatMessageBody):
    """Stream chat response via SSE."""
    presenter = deps.get_chat_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Chat not available")
    if body.thread_id and not presenter.switch_chat_thread(body.thread_id):
        raise HTTPException(status_code=404, detail=f"Chat thread not found: {body.thread_id}")

    chunk_queue: queue.Queue = queue.Queue()
    full_response = [None]
    sentinel = object()

    class StreamView:
        def on_message_added(self, role: str, content: str):
            pass

        def on_response_started(self):
            pass

        def on_response_chunk(self, chunk: str):
            chunk_queue.put(chunk)

        def on_response_completed(self, full: str):
            full_response[0] = full
            chunk_queue.put(sentinel)

    presenter.set_view(StreamView())

    def run_stream():
        def on_done(ai_text: str, error_text: Optional[str]):
            if error_text:
                chunk_queue.put({"error": error_text})
            else:
                full_response[0] = ai_text
                chunk_queue.put(ai_text)
            chunk_queue.put(sentinel)

        presenter.send_message_sync(body.message, on_done=on_done)

    loop = asyncio.get_event_loop()
    loop.run_in_executor(_executor, run_stream)

    async def event_stream():
        while True:
            try:
                item = chunk_queue.get_nowait()
            except queue.Empty:
                if full_response[0] is not None:
                    break
                await asyncio.sleep(0.05)
                continue
            if item is sentinel:
                break
            if isinstance(item, dict) and "error" in item:
                yield f"data: {json.dumps({'error': item['error']})}\n\n"
                break
            yield f"data: {json.dumps({'chunk': item})}\n\n"
        if full_response[0] is not None:
            yield f"data: {json.dumps({'done': True, 'full': full_response[0]})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/models")
async def chat_get_models():
    """List available models."""
    presenter = deps.get_chat_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Chat not available")
    return {"models": presenter.get_available_models()}


@router.get("/model")
async def chat_get_model():
    """Get current model."""
    presenter = deps.get_chat_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Chat not available")
    return {"model": presenter.get_current_model()}


@router.put("/model")
async def chat_set_model(body: SetModelBody):
    """Set current model."""
    presenter = deps.get_chat_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Chat not available")
    ok = presenter.set_model(body.model)
    if not ok:
        raise HTTPException(status_code=400, detail=f"Model not available: {body.model}")
    return {"model": presenter.get_current_model()}


@router.get("/threads")
async def chat_get_threads():
    """List chat threads and active selection."""
    presenter = deps.get_chat_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Chat not available")
    return {
        "threads": presenter.list_chat_threads(),
        "active_thread_id": presenter.get_active_thread_id(),
    }


@router.post("/threads")
async def chat_create_thread(body: ChatThreadCreateBody):
    """Create and switch to a new chat thread."""
    presenter = deps.get_chat_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Chat not available")
    thread = presenter.create_chat_thread(body.title)
    return {
        "thread": thread,
        "active_thread_id": presenter.get_active_thread_id(),
    }


@router.put("/threads/active")
async def chat_set_active_thread(body: ChatThreadSwitchBody):
    """Switch the active chat thread."""
    presenter = deps.get_chat_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Chat not available")
    if not presenter.switch_chat_thread(body.thread_id):
        raise HTTPException(status_code=404, detail=f"Chat thread not found: {body.thread_id}")
    return {"active_thread_id": presenter.get_active_thread_id()}


@router.get("/history")
async def chat_get_history(thread_id: Optional[str] = Query(None)):
    """Get conversation history for the active or selected thread."""
    presenter = deps.get_chat_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Chat not available")
    selected_thread_id = str(thread_id or "").strip()
    if selected_thread_id:
        known_ids = {str(item.get("id", "")) for item in presenter.list_chat_threads()}
        if selected_thread_id not in known_ids:
            raise HTTPException(status_code=404, detail=f"Chat thread not found: {selected_thread_id}")
    history = presenter.get_thread_history(selected_thread_id or None)
    return {
        "thread_id": selected_thread_id or presenter.get_active_thread_id(),
        "messages": [
            {"role": message.role, "content": message.content, "timestamp": message.timestamp}
            for message in history
        ],
    }
