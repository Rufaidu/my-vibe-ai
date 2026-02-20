import streamlit as st
import time
import uuid
import requests
import openai

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Vibe AI", page_icon="🔥", layout="wide")

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
    "https://router.huggingface.co/models/google/flan-t5-xl",
    "https://router.huggingface.co/models/google/flan-t5-large",
    "https://router.huggingface.co/models/facebook/opt-2.7b-instruct"
]

# ================= QUERY FUNCTIONS =================
def query_openai(prompt):
    if not OPENAI_KEY:
        return None
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except:
        return None

def query_gemini(prompt):
    if not GEMINI_KEY:
        return None
    # Replace this with real Gemini API call if you have access
    # Example pseudo-code:
    # response = requests.post("https://gemini.api.endpoint", headers={"Authorization": f"Bearer {GEMINI_KEY}"}, json={"prompt": prompt})
    # return response.json()["response"]
    return None  # placeholder

def query_hf(prompt, retries=3, delay=2):
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    for model_url in HF_MODELS:
        for _ in range(retries):
            try:
                resp = requests.post(model_url, json={"inputs": prompt, "options":{"use_cache": False}}, headers=headers, timeout=60)
                data = resp.json()
                if isinstance(data, dict) and "error" in data:
                    time.sleep(delay)
                    continue
                return data[0]["generated_text"]
            except:
                time.sleep(delay)
                continue
    return None

def query_multi_provider(prompt):
    # 1️⃣ OpenAI
    result = query_openai(prompt)
    if result:
        return result

    # 2️⃣ Gemini
    result = query_gemini(prompt)
    if result:
        return result

    # 3️⃣ Hugging Face
    result = query_hf(prompt)
    if result:
        return result

    return "⚠️ Sorry, all providers/models are busy. Please try again later."

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

# ================= SESSION STATE =================
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
    st.caption("Provider priority: OpenAI → Gemini → Hugging Face Falcon")
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

    # last 5 messages
    conversation = ""
    for msg in current_chat["messages"][-5:]:
        role = "User" if msg["role"] == "user" else "Assistant"
        conversation += f"{role}: {msg['content']}\n"

    with st.spinner("Vibe AI is thinking..."):
        bot_reply = query_multi_provider(conversation)

    # streaming typing animation
    full_response = ""
    placeholder = st.empty()
    for word in bot_reply.split():
        full_response += word + " "
        placeholder.markdown(f"<div class='chat-bubble-bot'>{full_response}</div>", unsafe_allow_html=True)
        time.sleep(0.02)

    current_chat["messages"].append({"role": "assistant", "content": bot_reply})
