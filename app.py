import os
import json
import uuid
from datetime import datetime
import requests
import streamlit as st

# ====== Config ======
OLLAMA_CHAT_API = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.2"
SAVE_DIR = "chats"  # folder to store JSON chat files
os.makedirs(SAVE_DIR, exist_ok=True)

# ====== Helpers for saving/loading ======
def save_chat(chat_id):
    """Save one chat to disk as JSON."""
    data = st.session_state.chats[chat_id]
    path = os.path.join(SAVE_DIR, f"{chat_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_all_chats():
    """Load all chats from disk into session state."""
    chats = {}
    for fn in os.listdir(SAVE_DIR):
        if fn.endswith(".json"):
            chat_id = fn[:-5]
            try:
                with open(os.path.join(SAVE_DIR, fn), "r", encoding="utf-8") as f:
                    chats[chat_id] = json.load(f)
            except Exception:
                # If a file is corrupted, skip it
                pass
    return chats

# ====== Session init ======
if "chats" not in st.session_state:
    st.session_state.chats = load_all_chats()
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = "You are a helpful AI assistant."

def new_chat():
    """Create a brand new empty chat (a new 'box')."""
    chat_id = str(uuid.uuid4())[:8]
    next_number = len(st.session_state.chats) + 1
    st.session_state.chats[chat_id] = {
        "name": f"Chat {next_number}",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "model": MODEL_NAME,
        "system_prompt": st.session_state.system_prompt,
        "messages": []  # list of {"role": "user"/"assistant"/"system", "content": "..."}
    }
    st.session_state.current_chat_id = chat_id
    save_chat(chat_id)

# Create first chat if none exist
if not st.session_state.chats:
    new_chat()
elif st.session_state.current_chat_id is None:
    # pick any existing chat as current
    st.session_state.current_chat_id = next(iter(st.session_state.chats.keys()))


#=====delete_chat function=====

def delete_chat(chat_id):
    # Remove from disk
    path = os.path.join(SAVE_DIR, f"{chat_id}.json")
    try:
        os.remove(path)   # <- physically delete the JSON file
    except FileNotFoundError:
        pass
    except PermissionError:
        # OneDrive or AV can lock files for a moment; mark as deleted in memory
        # and we'll also ignore missing files on next load.
        pass

    # Remove from session
    st.session_state.chats.pop(chat_id, None)

    # Pick a new current chat, or create a fresh one if none left
    if st.session_state.current_chat_id == chat_id:
        next_id = next(iter(st.session_state.chats), None)
        if next_id is None:
            new_chat()  # your existing function that creates an empty chat and saves it
        else:
            st.session_state.current_chat_id = next_id

    # Refresh UI
    st.rerun()

# ====== UI: Title & Sidebar ======

col1, col2 = st.columns([1, 5])
with col1:
    st.image("logo.png", width=200)
with col2:
    st.markdown("<h1 style=' color: #ff6c6c;'>Local Chatbot</h1>", unsafe_allow_html=True)


st.caption("Experiment with prompt engineering and temperature fine-tuning")

with st.sidebar:
    st.markdown("<h1 style=' color: #ff6c6c;'>Local Chatbot</h1>", unsafe_allow_html=True)
    
    st.subheader("Conversations")

    # New chat button
    if st.button("➕ New chat", use_container_width=True):
        new_chat()
        st.rerun()  # optional: force immediate refresh

    # List chats by name
    id_to_name = {cid: st.session_state.chats[cid]["name"] for cid in st.session_state.chats}
    name_to_id = {v: k for k, v in id_to_name.items()}
    names = list(name_to_id.keys())

    current_id = st.session_state.current_chat_id
    current_name = st.session_state.chats[current_id]["name"]

    selected_name = st.selectbox(
        "Pick a conversation",
        options=names,
        index=names.index(current_name) if current_name in names else 0
    )
    st.session_state.current_chat_id = name_to_id[selected_name]

    # Rename chat
    new_name = st.text_input("Rename this chat", value=current_name)
    if new_name and new_name != current_name:
        st.session_state.chats[current_id]["name"] = new_name
        save_chat(current_id)

    # System prompt (per chat)
    sp = st.text_area("System Prompt", value=st.session_state.chats[current_id].get("system_prompt", st.session_state.system_prompt))
    if sp != st.session_state.chats[current_id].get("system_prompt", ""):
        st.session_state.chats[current_id]["system_prompt"] = sp
        save_chat(current_id)

    # Temperature & max tokens
    temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
    max_tokens = st.slider("Max tokens", 10, 500, 200, 10)

    # Delete current chat
    if st.button("🗑️ Delete this chat", type="secondary"):
        delete_chat(st.session_state.current_chat_id)

# ====== Show messages for the current chat ======
cid = st.session_state.current_chat_id
chat = st.session_state.chats[cid]
messages = chat["messages"]

# Render message history (cards inside the chosen box)
for msg in messages:
    st.chat_message(msg["role"]).markdown(msg["content"])

# ====== Chat input & streaming to Ollama ======
prompt = st.chat_input("Type your message...")
if prompt:
    # 1) Store user's turn
    messages.append({"role": "user", "content": prompt})
    save_chat(cid)  # autosave after user message
    st.chat_message("user").markdown(prompt)

    # 2) Build payload with full history (+ system prompt at the top)
    chat_messages = []
    sys = chat.get("system_prompt", "").strip()
    if sys:
        chat_messages.append({"role": "system", "content": sys})
    # append the stored conversation
    chat_messages.extend(messages)

    payload = {
        "model": chat.get("model", MODEL_NAME),
        "messages": chat_messages,
        "options": {"temperature": temperature, "max_tokens": max_tokens},
        "stream": True
    }

    # 3) Stream the assistant's answer
    full_response = ""
    with st.spinner("Thinking..."):
        try:
            resp = requests.post(OLLAMA_CHAT_API, json=payload, stream=True, timeout=120)
            resp.raise_for_status()
            with st.chat_message("assistant"):
                placeholder = st.empty()
                for raw in resp.iter_lines():
                    if not raw:
                        continue
                    # 1) Normalize to str
                    line = raw.decode("utf-8", errors="ignore") if isinstance(raw, (bytes, bytearray)) else raw
                    
                    # 2) (Optional) strip SSE prefix if some proxy added it
                    if line.startswith("data: "):
                        line = line[6:]
                    # 3) Parse JSON chunk from Ollama stream
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    
                    # 4) Read the text field depending on endpoint
                    # For /api/chat:
                    text_chunk = (chunk.get("message") or {}).get("content", "")
                    # For /api/generate, use:
                    # text_chunk = chunk.get("response", "")

                    if text_chunk:
                        full_response += text_chunk
                        placeholder.markdown(full_response)

                    if chunk.get("done"):
                        break

        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {e}")

    # 4) Save assistant turn and persist
    messages.append({"role": "assistant", "content": full_response})

