from openai import OpenAI
from app.config import settings
from app.services.customer_service import get_customer, calculate_metrics
from app.services.chat_db import get_memory, append_memory
import json
import logging

logger = logging.getLogger(__name__)

tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "get_customer_profile",
            "description": "Fetch the complete profile, detailed expense breakdowns, bills, and portfolio holdings of the customer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"}
                },
                "required": ["customer_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_derived_financial_metrics",
            "description": "Fetch computed metrics like savings rate, asset allocation, and goal progress.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"}
                },
                "required": ["customer_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "project_goal_feasibility",
            "description": "Calculate if a customer can reach their financial goal given current savings and time horizon.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "goal_name": {"type": "string"}
                },
                "required": ["customer_id", "goal_name"]
            }
        }
    }
]

def project_goal_feasibility(customer_id: str, goal_name: str) -> str:
    customer = get_customer(customer_id)
    if not customer: return "Customer not found."
    
    goal = next((g for g in customer.get("goals", []) if g["goal_name"].lower() == goal_name.lower()), None)
    if not goal: return f"Goal '{goal_name}' not found."
    
    target = goal["target_amount"]
    current = goal["current_amount"]
    years_left = goal["target_year"] - 2026
    if years_left <= 0: return "Target year is already reached or passed."
    
    future_val = current * ((1 + 0.12) ** years_left)
    shortfall = target - future_val
    
    if shortfall <= 0:
        return f"On track! Current savings of ₹{current} growing at ~12% will exceed the target of ₹{target}."
    
    r = 0.12 / 12
    n = years_left * 12
    sip_required = (shortfall * r) / (((1 + r) ** n) - 1)
    
    return f"Not on track. Shortfall of ₹{int(shortfall)}. Required additional monthly SIP: ₹{int(sip_required)}."

def fallback_response(customer_id: str, message: str) -> dict:
    customer = get_customer(customer_id)
    if not customer:
        return {"response": "I cannot find your profile details.", "tool_trace": [], "degraded": True}
    
    metrics = calculate_metrics(customer)
    
    return {
        "response": f"Hi {customer['name']}, I'm operating in offline mode. Your portfolio is worth ₹{customer['portfolio_value']:,} with a {metrics['weighted_return']}% overall return. You are saving {metrics['savings_rate']}% of your income. Let me know if you need specific details about your holdings.",
        "tool_trace": [],
        "degraded": True
    }

def summarize_and_store_memory(customer_id: str, history: list):
    if not history or not settings.openrouter_api_key or settings.openrouter_api_key == "your-key-here":
        return
        
    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
        )
        
        chat_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
        
        prompt = (
            "You are a helpful assistant. Please read the following chat history between a wealth advisor and a client, "
            "and extract a very concise, bulleted list of the client's key financial preferences, concerns, or unrecorded goals. "
            "Ignore general greetings. Output only the bullet points.\n\n"
            f"Chat History:\n{chat_text}"
        )
        
        response = client.chat.completions.create(
            model=settings.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        
        summary = response.choices[0].message.content.strip()
        if summary:
            append_memory(customer_id, summary)
            
    except Exception as e:
        logger.error(f"Memory Summarization Error: {str(e)}")

def chat_with_advisor(customer_id: str, message: str, history: list) -> dict:
    if not settings.openrouter_api_key or settings.openrouter_api_key == "your-key-here":
        logger.warning("OpenRouter API key missing, using fallback.")
        return fallback_response(customer_id, message)
    
    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
        )
        
        customer = get_customer(customer_id)
        goals_list = [g["goal_name"] for g in customer.get("goals", [])] if customer else []
        goals_str = ", ".join(goals_list) if goals_list else "None"
        
        memory = get_memory(customer_id)
        memory_str = f" Here are important facts and preferences you learned about this user in past conversations: {memory}" if memory else ""
        
        system_prompt = (
            "CRITICAL INSTRUCTION: You are 'IDBI WealthAI', an exclusive, sophisticated AI Financial Coach and Wealth Advisor created exclusively by IDBI Bank. "
            "You MUST NEVER identify yourself as a generic large language model, AI assistant, or mention any training by Google, OpenAI, Anthropic, etc. "
            "If a user asks who you are, you are exclusively IDBI WealthAI. If a user asks about programming, LLMs, or non-financial topics, politely decline and pivot the conversation back to their wealth and IDBI Bank services. "
            "You provide personalized, accurate financial advice to customers based ONLY on their real data. "
            f"The current user's customer_id is '{customer_id}' and their listed financial goals are: {goals_str}.{memory_str} "
            "Always use this ID when calling tools. You have full access to their detailed expense tracking, bills, and portfolios via tools. "
            "Use the provided tools to fetch data before answering. Never hallucinate financial numbers. "
            "Actively identify money leaks and unnecessary subscriptions from their detailed bills when asked about expenses. "
            "Keep answers concise, professional, and conversational. "
            "IMPORTANT: Do NOT use any Markdown formatting (like asterisks for bold or bullet points). Output plain text only."
        )
        
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        messages.append({"role": "user", "content": message})
        
        response = client.chat.completions.create(
            model=settings.model_name,
            messages=messages,
            tools=tools_definition,
            tool_choice="auto",
            max_tokens=4000,
        )
        
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        
        tool_trace = []
        
        if tool_calls:
            messages.append(response_message)
            
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                tool_trace.append({"name": function_name, "input": function_args})
                
                result_str = ""
                if function_name == "get_customer_profile":
                    cust = get_customer(function_args.get("customer_id"))
                    result_str = json.dumps(cust) if cust else "Not found"
                elif function_name == "get_derived_financial_metrics":
                    cust = get_customer(function_args.get("customer_id"))
                    result_str = json.dumps(calculate_metrics(cust)) if cust else "Not found"
                elif function_name == "project_goal_feasibility":
                    result_str = project_goal_feasibility(function_args.get("customer_id"), function_args.get("goal_name"))
                
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": result_str,
                })
                
            second_response = client.chat.completions.create(
                model=settings.model_name,
                messages=messages,
                max_tokens=4000,
            )
            final_text = second_response.choices[0].message.content
        else:
            final_text = response_message.content
            
        return {
            "response": final_text,
            "tool_trace": tool_trace,
            "degraded": False
        }
        
    except Exception as e:
        logger.error(f"LLM Error: {str(e)}")
        return fallback_response(customer_id, message)
