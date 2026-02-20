import streamlit as st
import sqlite3
import time
from google import genai  # Correct GenAI SDK

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Vibe AI", page_icon="🧠", layout="wide")

# ---------- CSS ----------
st.markdown("""
<style>
body { background-color: #0b0f19; color: white; font-family: 'Segoe UI', sans-serif; }
.block-container { padding-top: 1rem; padding-bottom: 6rem; }
.user-bubble { background: linear-gradient(135deg, #2563eb, #1d4ed8); padding: 12px; border-radius: 18px; margin: 8px 0; text-align: right; max-width: 75%; margin-left: auto; word-wrap: break-word; }
.ai-bubble { background-color: #1f2937; padding: 12px; border-radius: 18px; margin: 8px 0; max-width: 75%; word-wrap: break-word; }
.stChatInputContainer { position: fixed; bottom: 0; left: 0; right: 0; background-color: #111827; padding: 10px; z-index: 100; }
.sidebar .sidebar-content { background-color: #0b0f19; }
.chat-container { max-height: 80vh; overflow-y: auto; }
</style>
""", unsafe_allow_html=True)

# ---------- DATABASE ----------
conn = sqlite3.connect("vibe_memory.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_input TEXT,
    ai_response TEXT
)
""")

# ---------- HEADER ----------
st.markdown("<h2 style='text-align:center;'>🧠 Vibe AI</h2>", unsafe_allow_html=True)

# ---------- SIDEBAR ----------
with st.sidebar:
    st.title("⚙️ Settings")
    memory_limit = st.slider("Memory Depth", 1, 15, 5)
    if st.button("🗑 Clear Chat"):
        c.execute("DELETE FROM conversations")
        conn.commit()
        st.session_state.messages = []
    st.divider()
    st.subheader("📜 Chat History")
    c.execute("SELECT user_input FROM conversations ORDER BY id DESC LIMIT 10")
    history = c.fetchall()
    for item in history:
        st.caption("• " + item[0][:40])

# ---------- SESSION ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

chat_placeholder = st.empty()

# ---------- CHAT DISPLAY ----------
def display_chat():
    with chat_placeholder.container():
        st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
        for role, message in st.session_state.messages:
            if role == "user":
                st.markdown(f"<div class='user-bubble'>{message}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='ai-bubble'>{message}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

display_chat()

# ---------- INPUT ----------
user_input = st.chat_input("Message Vibe AI...")

if user_input:
    st.session_state.messages.append(("user", user_input))
    display_chat()

    # Build prompt with memory
    c.execute("SELECT user_input, ai_response FROM conversations ORDER BY id DESC LIMIT ?", (memory_limit,))
    past = c.fetchall()
    memory_text = ""
    for u, a in reversed(past):
        memory_text += f"User: {u}\nAI: {a}\n"
    prompt = memory_text + f"User: {user_input}\nAI:"

    # ---------- CALL GEMINI ----------
    with st.spinner("Vibe AI is thinking..."):
        try:
            client = genai.Client(api_key=st.secrets["AI_STUDIO_API_KEY"])
            response = client.models.generate_content(
                model="gemini-2.5-flash",  # Free-tier compatible model
                contents=prompt
            )
            ai_response = response.text.strip()

        except Exception as e:
            st.error(f"AI Error: {e}")
            st.stop()

    # ---------- TYPING ANIMATION ----------
    display_text = ""
    for char in ai_response:
        display_text += char
        # temporarily display typing
        temp_messages = st.session_state.messages + [("ai", display_text)]
        chat_placeholder.empty()
        with chat_placeholder.container():
            st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
            for role, message in temp_messages:
                if role == "user":
                    st.markdown(f"<div class='user-bubble'>{message}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='ai-bubble'>{message}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        time.sleep(0.01)

    # Save final AI response
    st.session_state.messages.append(("ai", ai_response))
    display_chat()
    c.execute("INSERT INTO conversations (user_input, ai_response) VALUES (?, ?)", (user_input, ai_response))
    conn.commit()
