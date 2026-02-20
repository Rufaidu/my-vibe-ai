import streamlit as st
import uuid
import requests
import openai
import json

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Vibe AI", page_icon="🧠", layout="wide")

# ================= LOAD API KEYS =================
try:
    HF_API_KEY = st.secrets["HF_API_KEY"]
except Exception:
    st.error("Add your HF_API_KEY to Streamlit Secrets before running.")
    st.stop()

GEMINI_KEY = st.secrets.get("GEMINI_KEY", None)
OPENAI_KEY = st.secrets.get("OPENAI_KEY", None)

if OPENAI_KEY:
    openai.api_key = OPENAI_KEY

# ================= HUGGING FACE MODELS =================
HF_MODELS = [
    "https://router.huggingface.co/models/tiiuae/falcon-h1-1.5b-instruct",
    "https://router.huggingface.co/models/tiiuae/falcon3-1b-instruct",
    "https://router.huggingface.co/models/google/flan-t5-large"
]

# ================= SESSION STATE =================
if "chats" not in st.session_state:
    st.session_state.chats = {}

if "current_chat" not in st.session_state:
    new_id = str(uuid.uuid4())
    st.session_state.chats[new_id] = {"title": "New Chat", "messages": []}
    st.session_state.current_chat = new_id

if "is_generating" not in st.session_state:
    st.session_state.is_generating = False

current_chat = st.session_state.chats[st.session_state.current_chat]

# ================= QUERY FUNCTIONS =================

def query_openai(prompt):
    if not OPENAI_KEY:
        return None
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            request_timeout=10
        )
        return response.choices[0].message.content
    except:
        return None


def query_gemini(prompt):
    if not GEMINI_KEY:
        return None
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=15)
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return None


def query_hf(prompt):
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    for model_url in HF_MODELS:
        try:
            resp = requests.post(
                model_url,
                json={"inputs": prompt},
                headers=headers,
                timeout=15
            )
            data = resp.json()
            if isinstance(data, dict) and "error" in data:
                continue
            return data[0]["generated_text"]
        except:
            continue
    return None


def query_multi_provider(prompt):
    providers = [
        query_openai,
        query_gemini,
        query_hf
    ]

    for provider in providers:
        try:
            result = provider(prompt)
            if result:
                return result
        except:
            continue

    return "⚠️ All providers are currently busy. Please try again later."


# ================= CUSTOM UI =================
st.markdown("""
<style>
.stApp { background-color: #0f172a; color: white; }
[data-testid="stSidebar"] { background-color: #111827; }

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

# ================= SIDEBAR =================
with st.sidebar:
    st.title("🧠 Vibe AI")

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
    st.caption("Provider order: OpenAI → Gemini → HuggingFace")

# ================= LANDING =================
if not current_chat["messages"]:
    st.markdown("<div class='center-title'>🧠 Vibe AI</div>", unsafe_allow_html=True)
    st.markdown("<center>Your intelligent AI companion</center>", unsafe_allow_html=True)

# ================= DISPLAY CHAT =================
for msg in current_chat["messages"]:
    if msg["role"] == "user":
        st.markdown(f"<div class='chat-bubble-user'>{msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='chat-bubble-bot'>{msg['content']}</div>", unsafe_allow_html=True)

# ================= CHAT INPUT =================
prompt = st.chat_input(
    "Message Vibe AI...",
    disabled=st.session_state.is_generating
)

if prompt and not st.session_state.is_generating:

    st.session_state.is_generating = True

    current_chat["messages"].append({
        "role": "user",
        "content": prompt
    })

    if current_chat["title"] == "New Chat":
        current_chat["title"] = prompt[:30]

    conversation = ""
    for msg in current_chat["messages"][-5:]:
        role = "User" if msg["role"] == "user" else "Assistant"
        conversation += f"{role}: {msg['content']}\n"

    placeholder = st.empty()
    placeholder.markdown(
        "<div class='chat-bubble-bot'><em>🧠 Vibe AI is thinking...</em></div>",
        unsafe_allow_html=True
    )

    with st.spinner("🧠 Generating response..."):
        bot_reply = query_multi_provider(conversation)

    placeholder.markdown(
        f"<div class='chat-bubble-bot'>{bot_reply}</div>",
        unsafe_allow_html=True
    )

    current_chat["messages"].append({
        "role": "assistant",
        "content": bot_reply
    })

    st.session_state.is_generating = False

    # Auto scroll
    st.markdown(
        """
        <script>
        window.scrollTo(0, document.body.scrollHeight);
        </script>
        """,
        unsafe_allow_html=True
    )

    st.rerun()
