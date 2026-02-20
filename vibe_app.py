import streamlit as st
import sqlite3
import time
from google import genai  # correct GenAI SDK

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

    # Build prompt with memory
    c.execute("SELECT user_input, ai_response FROM conversations ORDER BY id DESC LIMIT ?", (memory_limit,))
    past = c.fetchall()
    memory_text = ""
    for u, a in reversed(past):
        memory_text += f"User: {u}\nAI: {a}\n"
    prompt = memory_text + f"User: {user_input}\nAI:"

    # ---------- CALL GEMINI VIA google-genai SDK ----------
    with st.spinner("Vibe AI is thinking..."):
        try:
            # Create the client with your API key from secrets
            client = genai.Client(api_key=st.secrets["AI_STUDIO_API_KEY"])

            # Generate text using the Gemini 1.5 model
            response = client.models.generate_content(
                model="gemini-1.5-flash",  # free tier model name
                contents=prompt
            )

            ai_response = response.text

        except Exception as e:
            st.error(f"AI Error: {e}")
            st.stop()

    # Typing animation + auto-scroll
    final_text = ""
    for char in ai_response:
        final_text += char
        st.session_state.messages.append(("ai", final_text))
        display_chat()
        time.sleep(0.01)

    # Save final response
    st.session_state.messages[-1] = ("ai", ai_response)
    display_chat()
    c.execute("INSERT INTO conversations (user_input, ai_response) VALUES (?, ?)", (user_input, ai_response))
    conn.commit()
