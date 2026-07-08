import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'chat_history.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.execute('PRAGMA journal_mode=WAL;')
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            tool_trace TEXT,
            degraded BOOLEAN,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customer_memory (
            customer_id TEXT PRIMARY KEY,
            memory_context TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def get_history(customer_id: str):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM chat_messages WHERE customer_id = ? ORDER BY id ASC', (customer_id,))
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        msg = {
            "role": row["role"],
            "content": row["content"]
        }
        if row["role"] == "assistant":
            msg["tool_trace"] = json.loads(row["tool_trace"]) if row["tool_trace"] else []
            msg["degraded"] = bool(row["degraded"])
        history.append(msg)
    return history

def add_message(customer_id: str, role: str, content: str, tool_trace: list = None, degraded: bool = False):
    conn = get_connection()
    cursor = conn.cursor()
    trace_str = json.dumps(tool_trace) if tool_trace is not None else None
    
    cursor.execute('''
        INSERT INTO chat_messages (customer_id, role, content, tool_trace, degraded)
        VALUES (?, ?, ?, ?, ?)
    ''', (customer_id, role, content, trace_str, degraded))
    conn.commit()
    conn.close()

def clear_history(customer_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM chat_messages WHERE customer_id = ?', (customer_id,))
    conn.commit()
    conn.close()

def get_memory(customer_id: str) -> str:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT memory_context FROM customer_memory WHERE customer_id = ?', (customer_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else ""

def append_memory(customer_id: str, new_memory: str):
    if not new_memory or not new_memory.strip():
        return
        
    current_memory = get_memory(customer_id)
    combined = current_memory + "\n- " + new_memory if current_memory else "- " + new_memory
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO customer_memory (customer_id, memory_context)
        VALUES (?, ?)
        ON CONFLICT(customer_id) DO UPDATE SET memory_context=excluded.memory_context
    ''', (customer_id, combined))
    conn.commit()
    conn.close()

# Initialize on load
init_db()
