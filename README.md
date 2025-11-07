# Local Chatbot (Streamlit + Ollama)

A simple, privacy‑friendly chatbot UI built with **Streamlit** and powered by **Ollama** for local LLM inference.

<img width="1635" height="920" alt="image" src="https://github.com/user-attachments/assets/1f04a5ea-8bc1-43f8-8718-b1d833c07c05" />

---

## ✨ Features

- **Multi‑chat sessions**: create, switch, rename, and delete conversations.
- **Per‑chat system prompt**: customize the assistant’s behavior for each chat.
- **Streaming responses**: see answers appear in real time.
- **Temperature & Max tokens controls**: fine‑tune generation.
- **Local storage**: chats are saved as JSON files in `./chats/`.

---

## 🧩 Requirements

- Python 3.9+
- https://ollama.ai installed and running locally
- Streamlit and Requests libraries

---

## 🚀 Quick Start

1. **Install dependencies**
   ```bash
   pip install streamlit requests
   ```

2. **Start Ollama and pull a model**
   ```bash
   ollama serve
   ollama pull llama3.2
   ```

3. **Run the app**
   ```bash
   streamlit run app.py
   ```

---

## 💾 Data Persistence

Chats are stored in `./chats/<chat_id>.json` with this structure:

```json
{
  "name": "Chat 1",
  "created_at": "2025-11-07T15:42:10",
  "model": "llama3.2",
  "system_prompt": "You are a helpful AI assistant.",
  "messages": [
    { "role": "user", "content": "Hello" },
    { "role": "assistant", "content": "Hi! How can I help?" }
  ]
}
```

---

## ⚙️ Configuration

Edit `app.py` to change:

- `OLLAMA_CHAT_API`: Ollama API endpoint (default: `http://localhost:11434/api/chat`)
- `MODEL_NAME`: default model name
- `SAVE_DIR`: folder for chat files
- Logo path and size

---

## 📚 Tech Stack

- **Frontend**: Streamlit
- **Backend**: Ollama local LLM
- **Storage**: JSON files

---

