import streamlit as st
import sqlite3
import time
from google import genai  # Correct Google GenAI SDK

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
.chat-container { max-height: 70vh; overflow-y: auto; }
</style>
""", unsafe_allow_html=True)

# ---------- DATABASE ----------
conn = sqlite3.connect("vibe_memory.db", check_same_thread=False)
c = conn.cursor()

# Create tables for threads and messages
c.execute("""
CREATE TABLE IF NOT EXISTS threads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id INTEGER,
    user_input TEXT,
    ai_response TEXT,
    FOREIGN KEY(thread_id) REFERENCES threads(id)
)
""")

# ---------- SESSION ----------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

# ---------- SIDEBAR ----------
with st.sidebar:
    st.title("⚙️ Settings")
    memory_limit = st.slider("Memory Depth", 1, 15, 5)

    # List threads
    c.execute("SELECT id, title FROM threads ORDER BY created_at DESC")
    threads = c.fetchall()
    thread_options = {t[1]: t[0] for t in threads}  # title -> id
    selected_thread_title = st.selectbox("Select a Chat", ["New Chat"] + list(thread_options.keys()))

    # Load selected thread
    if selected_thread_title == "New Chat":
        st.session_state.thread_id = None
        st.session_state.messages = []
    else:
        st.session_state.thread_id = thread_options[selected_thread_title]
        c.execute("SELECT user_input, ai_response FROM conversations WHERE thread_id=? ORDER BY id ASC", (st.session_state.thread_id,))
        loaded = c.fetchall()
        st.session_state.messages = []
        for u, a in loaded:
            st.session_state.messages.append(("user", u))
            st.session_state.messages.append(("ai", a))

    if st.button("🗑 Clear Chat"):
        if st.session_state.thread_id:
            c.execute("DELETE FROM conversations WHERE thread_id=?", (st.session_state.thread_id,))
            c.execute("DELETE FROM threads WHERE id=?", (st.session_state.thread_id,))
            conn.commit()
            st.session_state.messages = []
            st.session_state.thread_id = None

# ---------- HEADER ----------
st.markdown("<h2 style='text-align:center;'>🧠 Vibe AI</h2>", unsafe_allow_html=True)

# ---------- CHAT DISPLAY ----------
chat_placeholder = st.empty()

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

    # ---------- CREATE NEW THREAD IF NEEDED ----------
    if st.session_state.thread_id is None:
        thread_title = user_input[:30]  # first 30 chars as title
        c.execute("INSERT INTO threads (title) VALUES (?)", (thread_title,))
        conn.commit()
        st.session_state.thread_id = c.lastrowid

    # ---------- BUILD PROMPT ----------
    c.execute("SELECT user_input, ai_response FROM conversations WHERE thread_id=? ORDER BY id DESC LIMIT ?", (st.session_state.thread_id, memory_limit))
    past = c.fetchall()
    memory_text = ""
    for u, a in reversed(past):
        memory_text += f"User: {u}\nAI: {a}\n"

    # System instruction
    system_instruction = (
        "You are Vibe AI, a helpful and friendly assistant. "
        "Always refer to yourself as 'Vibe AI'. "
        "Keep responses concise and engaging."
    )

    prompt = system_instruction + "\n\n" + memory_text + f"User: {user_input}\nAI:"

    # ---------- CALL GEMINI ----------
    with st.spinner("Vibe AI is thinking..."):
        try:
            client = genai.Client(api_key=st.secrets["AI_STUDIO_API_KEY"])
            response = client.models.generate_content(
                model="gemini-2.5-flash",
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

    # ---------- SAVE FINAL RESPONSE ----------
    st.session_state.messages.append(("ai", ai_response))
    display_chat()
    c.execute(
        "INSERT INTO conversations (thread_id, user_input, ai_response) VALUES (?, ?, ?)",
        (st.session_state.thread_id, user_input, ai_response)
    )
    conn.commit()
