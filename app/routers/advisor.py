from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.services.llm_gateway import chat_with_advisor, summarize_and_store_memory
from app.services.chat_db import get_history, add_message, clear_history

router = APIRouter(prefix="/api/advisor", tags=["advisor"])

class Message(BaseModel):
    role: str
    content: Optional[str] = None
    tool_trace: Optional[list] = None
    degraded: Optional[bool] = False

class ChatRequest(BaseModel):
    customer_id: str
    message: str

@router.get("/chat/{customer_id}")
def get_chat_history(customer_id: str):
    return get_history(customer_id)

@router.delete("/chat/{customer_id}")
def delete_chat_history(customer_id: str, background_tasks: BackgroundTasks):
    history = get_history(customer_id)
    if history:
        background_tasks.add_task(summarize_and_store_memory, customer_id, history)
    clear_history(customer_id)
    return {"status": "success"}

@router.post("/chat")
def chat(request: ChatRequest):
    # Fetch existing history from DB
    history = get_history(request.customer_id)
    history_dict = [{"role": msg["role"], "content": msg["content"] or ""} for msg in history]
    
    # Save the user's new message to DB
    add_message(request.customer_id, "user", request.message)
    
    # Process through LLM
    result = chat_with_advisor(
        customer_id=request.customer_id,
        message=request.message,
        history=history_dict
    )
    
    # Save assistant's response to DB
    add_message(
        request.customer_id, 
        "assistant", 
        result.get("response") or "", 
        tool_trace=result.get("tool_trace"), 
        degraded=result.get("degraded", False)
    )
    
    return result
