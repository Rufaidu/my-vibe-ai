import streamlit as st
import time
import uuid
import requests

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Vibe AI",
    page_icon="🔥",
    layout="wide"
)

# ================= LOAD HUGGING FACE API KEY =================
try:
    HF_API_KEY = st.secrets["HF_API_KEY"]
except Exception:
    st.error("Add HF_API_KEY inside Streamlit Secrets.")
    st.stop()

HF_MODEL_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct"

# ================= FUNCTION TO QUERY HF MODEL =================
def query_hf(prompt):
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {
        "inputs": prompt,
        "options": {"use_cache": False}
    }
    try:
        response = requests.post(HF_MODEL_URL, json=payload, headers=headers, timeout=60)
        data = response.json()
        if "error" in data:
            return "⚠️ Model error: " + data["error"]
        return data[0]["generated_text"]
    except Exception as e:
        return f"⚠️ Request failed: {str(e)}"

# ================= CUSTOM DARK UI =================
st.markdown("""
<style>
.stApp { background-color: #0f172a; color: white; }
[data-testid="stSidebar"] { background-color: #111827; }
.chat-bubble-user { background: #1e293b; padding: 14px; border-radius: 14px; margin-bottom: 10px; text-align: right; }
.chat-bubble-bot { background: #111827; padding: 14px; border-radius: 14px; margin-bottom: 10px; text-align: left; }
.center-title { text-align: center; margin-top: 20vh; font-size: 42px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ================= SESSION STRUCTURE =================
if "chats" not in st.session_state:
    st.session_state.chats = {}

if "current_chat" not in st.session_state:
    new_id = str(uuid.uuid4())
    st.session_state.chats[new_id] = {"title": "New Chat", "messages": []}
    st.session_state.current_chat = new_id

current_chat = st.session_state.chats[st.session_state.current_chat]

# ================= SIDEBAR =================
with st.sidebar:
    st.title("🔥 Vibe AI")

    if st.button("➕ New Chat"):
        new_id = str(uuid.uuid4())
        st.session_state.chats[new_id] = {"title": "New Chat", "messages": []}
        st.session_state.current_chat = new_id
        st.rerun()

    st.markdown("### Chats")
    for chat_id, chat_data in st.session_state.chats.items():
        if st.button(chat_data["title"], key=chat_id):
            st.session_state.current_chat = chat_id
            st.rerun()

    st.markdown("---")
    st.caption(f"Using Hugging Face Model: Mistral-7B-Instruct")

    if st.button("🗑 Delete Current Chat"):
        del st.session_state.chats[st.session_state.current_chat]
        if not st.session_state.chats:
            new_id = str(uuid.uuid4())
            st.session_state.chats[new_id] = {"title": "New Chat", "messages": []}
            st.session_state.current_chat = new_id
        else:
            st.session_state.current_chat = list(st.session_state.chats.keys())[0]
        st.rerun()

# ================= LANDING SCREEN =================
if not current_chat["messages"]:
    st.markdown("<div class='center-title'>🔥 Vibe AI</div>", unsafe_allow_html=True)
    st.markdown("<center>Your intelligent AI companion</center>", unsafe_allow_html=True)

# ================= DISPLAY CHAT =================
for msg in current_chat["messages"]:
    if msg["role"] == "user":
        st.markdown(f"<div class='chat-bubble-user'>{msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='chat-bubble-bot'>{msg['content']}</div>", unsafe_allow_html=True)

# ================= FILE UPLOAD =================
uploaded_file = st.file_uploader("Upload file (optional)", type=["pdf", "png", "jpg", "jpeg"])

# ================= CHAT INPUT =================
prompt = st.chat_input("Message Vibe AI...")

if prompt:
    current_chat["messages"].append({"role": "user", "content": prompt})

    if current_chat["title"] == "New Chat":
        current_chat["title"] = prompt[:30]

    # Only use last 5 messages to save tokens/quota
    conversation = ""
    for msg in current_chat["messages"][-5:]:
        role = "User" if msg["role"] == "user" else "Assistant"
        conversation += f"{role}: {msg['content']}\n"

    # Query Hugging Face Model
    with st.spinner("Vibe AI is thinking..."):
        bot_reply = query_hf(conversation)

    # Streaming animation
    full_response = ""
    placeholder = st.empty()
    for word in bot_reply.split():
        full_response += word + " "
        placeholder.markdown(f"<div class='chat-bubble-bot'>{full_response}</div>", unsafe_allow_html=True)
        time.sleep(0.02)

    current_chat["messages"].append({"role": "assistant", "content": bot_reply})
