import streamlit as st
import google.generativeai as genai
import time
import uuid

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Vibe AI",
    page_icon="🔥",
    layout="wide"
)

# ================= LOAD API KEY =================
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("Add GEMINI_API_KEY to Streamlit Secrets.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

MODEL_OPTIONS = {
    "Gemini 1.5 Flash": "gemini-1.5-flash",
    "Gemini 1.5 Pro": "gemini-1.5-pro"
}

# ================= CUSTOM UI =================
st.markdown("""
<style>
.stApp {
    background-color: #0f172a;
    color: white;
}

[data-testid="stSidebar"] {
    background-color: #111827;
}

.chat-bubble-user {
    background: #1e293b;
    padding: 14px;
    border-radius: 14px;
    margin-bottom: 10px;
    text-align: right;
}

.chat-bubble-bot {
    background: #111827;
    padding: 14px;
    border-radius: 14px;
    margin-bottom: 10px;
    text-align: left;
}

.title-center {
    text-align: center;
    margin-top: 20vh;
    font-size: 38px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ================= SESSION STRUCTURE =================
if "chats" not in st.session_state:
    st.session_state.chats = {}

if "current_chat" not in st.session_state:
    new_id = str(uuid.uuid4())
    st.session_state.chats[new_id] = {
        "title": "New Chat",
        "messages": []
    }
    st.session_state.current_chat = new_id

current_chat_data = st.session_state.chats[st.session_state.current_chat]

# ================= SIDEBAR =================
with st.sidebar:
    st.title("🔥 Vibe AI")

    if st.button("➕ New Chat"):
        new_id = str(uuid.uuid4())
        st.session_state.chats[new_id] = {
            "title": "New Chat",
            "messages": []
        }
        st.session_state.current_chat = new_id
        st.rerun()

    st.markdown("### Chats")

    for chat_id, chat_data in st.session_state.chats.items():
        if st.button(chat_data["title"], key=chat_id):
            st.session_state.current_chat = chat_id
            st.rerun()

    st.markdown("---")

    selected_model_name = st.selectbox(
        "Model",
        list(MODEL_OPTIONS.keys())
    )

    if st.button("🗑 Delete Chat"):
        del st.session_state.chats[st.session_state.current_chat]
        if not st.session_state.chats:
            st.session_state.chats = {}
        st.rerun()

# ================= LANDING SCREEN =================
if not current_chat_data["messages"]:
    st.markdown("<div class='title-center'>🔥 Vibe AI</div>", unsafe_allow_html=True)
    st.markdown("<center>Your intelligent AI companion.</center>", unsafe_allow_html=True)

# ================= DISPLAY CHAT =================
for msg in current_chat_data["messages"]:
    if msg["role"] == "user":
        st.markdown(
            f"<div class='chat-bubble-user'>{msg['content']}</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<div class='chat-bubble-bot'>{msg['content']}</div>",
            unsafe_allow_html=True
        )

# ================= FILE UPLOAD =================
uploaded_file = st.file_uploader("Upload file (optional)", type=["pdf", "png", "jpg", "jpeg"])

# ================= CHAT INPUT =================
prompt = st.chat_input("Message Vibe AI...")

if prompt:
    current_chat_data["messages"].append({"role": "user", "content": prompt})

    if current_chat_data["title"] == "New Chat":
        current_chat_data["title"] = prompt[:30]

    # Build conversation history
    conversation = ""
    for msg in current_chat_data["messages"]:
        role = "User" if msg["role"] == "user" else "Assistant"
        conversation += f"{role}: {msg['content']}\n"

    model = genai.GenerativeModel(
        MODEL_OPTIONS[selected_model_name]
    )

    with st.spinner("Vibe AI is thinking..."):
        response = model.generate_content(conversation)
        bot_reply = response.text

    # Streaming animation
    full_response = ""
    placeholder = st.empty()

    for word in bot_reply.split():
        full_response += word + " "
        placeholder.markdown(
            f"<div class='chat-bubble-bot'>{full_response}</div>",
            unsafe_allow_html=True
        )
        time.sleep(0.02)

    current_chat_data["messages"].append(
        {"role": "assistant", "content": bot_reply}
    )
