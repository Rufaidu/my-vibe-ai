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
    st.error("Add GEMINI_API_KEY inside Streamlit Secrets.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

# ================= AUTO MODEL DETECTION =================
def get_available_models():
    try:
        models = genai.list_models()
        available = [
            m.name for m in models
            if "generateContent" in m.supported_generation_methods
        ]
        return available
    except Exception as e:
        st.error(f"Error fetching models: {e}")
        return []

def pick_best_model(models):
    # Prefer flash models first
    for m in models:
        if "flash" in m.lower():
            return m
    # Otherwise return first available
    if models:
        return models[0]
    return None

AVAILABLE_MODELS = get_available_models()
MODEL_NAME = pick_best_model(AVAILABLE_MODELS)

if not MODEL_NAME:
    st.error("No Gemini model available. Check API setup.")
    st.stop()

model = genai.GenerativeModel(MODEL_NAME)

# ================= CUSTOM DARK UI =================
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

.center-title {
    text-align: center;
    margin-top: 20vh;
    font-size: 42px;
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

current_chat = st.session_state.chats[st.session_state.current_chat]

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
    st.caption(f"Active Model: {MODEL_NAME}")

    if st.button("🗑 Delete Current Chat"):
        del st.session_state.chats[st.session_state.current_chat]
        if not st.session_state.chats:
            new_id = str(uuid.uuid4())
            st.session_state.chats[new_id] = {
                "title": "New Chat",
                "messages": []
            }
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
    current_chat["messages"].append({"role": "user", "content": prompt})

    if current_chat["title"] == "New Chat":
        current_chat["title"] = prompt[:30]

    conversation = ""
    for msg in current_chat["messages"]:
        role = "User" if msg["role"] == "user" else "Assistant"
        conversation += f"{role}: {msg['content']}\n"

    with st.spinner("Vibe AI is thinking..."):
        try:
            response = model.generate_content(conversation)
            bot_reply = response.text
        except Exception as e:
            bot_reply = "⚠️ Error generating response. Trying fallback..."
            st.warning(str(e))

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

    current_chat["messages"].append(
        {"role": "assistant", "content": bot_reply}
    )
