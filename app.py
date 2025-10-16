import json
import streamlit as st
import requests

# -- ollama --
OLLAMA_API = "http://localhost:11434/api/generate"

st.title("Local Chatbot")
st.caption("Experiment with prompt engineering and temperature fine-tuning")

# Sidebar Controls
# temperature: min=0.0, max=1.0, default=0.7, step=0.1
temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
# max_tokens: min=10, max=500, default=200, step=10
max_tokens = st.sidebar.slider("Max tokens", 10, 500, 200, 10)
system_prompt = st.sidebar.text_area("System Prompt",
                                     "You are a helpful AI assistant.")

# Initialize session state for message history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render existing messages
for msg in st.session_state.messages:
    st.chat_message(msg['role']).markdown(msg["content"])

prompt = st.chat_input("Ask anything ..")
if prompt:
    # append user's message to history and render it
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)

    payload = {
        "model": "llama3.2"
        "",
        "prompt": f"{system_prompt}\n\nUser: {prompt}",
        # Ollama-like APIs typically expect 'temperature' and 'max_tokens' (adjust if your API differs)
        "options": {"temperature": temperature, "max_tokens": max_tokens}
    }

    with st.spinner("Generating response..."):
        try:
            response = requests.post(OLLAMA_API, json=payload, stream=True, timeout=60)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {e}")
        else:
            full_response = ""
            # Use a placeholder inside an assistant chat message to stream updates
            with st.chat_message("assistant"):
                placeholder = st.empty()
                for line in response.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    text_chunk = ""
                    # Try to parse each line as JSON first (common for streamed APIs)
                    try:
                        parsed = json.loads(line)
                        if isinstance(parsed, dict):
                            # common fields: 'response', 'text', 'token'
                            text_chunk = parsed.get("response") or parsed.get("text") or parsed.get("token") or ""
                        else:
                            text_chunk = str(parsed)
                    except Exception:
                        # Fallback: remove any leading 'data: ' and use raw text
                        raw = line
                        if raw.startswith("data: "):
                            raw = raw[len("data: "):]
                        text_chunk = raw

                    full_response += text_chunk
                    placeholder.markdown(full_response)

            # save assistant message to history
            st.session_state.messages.append({"role": "assistant", "content": full_response})