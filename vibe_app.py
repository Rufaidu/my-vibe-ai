import streamlit as st
import sqlite3
import requests
import time

st.set_page_config(page_title="Vibe AI", page_icon="🔥", layout="wide")

# ------------------ MOBILE APP CSS ------------------
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: 'Segoe UI', sans-serif;
}

body {
    background-color: #0b0f19;
    color: white;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 6rem;
}

.user-bubble {
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    padding: 12px;
    border-radius: 18px;
    margin: 8px 0;
    text-align: right;
    max-width: 75%;
    margin-left: auto;
}

.ai-bubble {
    background-color: #1f2937;
    padding: 12px;
    border-radius: 18px;
    margin: 8px 0;
    max-width: 75%;
}

.stChatInputContainer {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background-color: #111827;
    padding: 10px;
}
</style>
""", unsafe_allow_html=True)

# ------------------ DATABASE ------------------
conn = sqlite3.connect("vibe_memory.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_input TEXT,
    ai_response TEXT
)
""")

# ------------------ HEADER ------------------
st.markdown("<h2 style='text-align:center;'>🔥 Vibe AI</h2>", unsafe_allow_html=True)
st.caption("Powered by Grok")

# ------------------ SESSION ------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ------------------ DISPLAY CHAT ------------------
for role, message in st.session_state.messages:
    if role == "user":
        st.markdown(f"<div class='user-bubble'>{message}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='ai-bubble'>{message}</div>", unsafe_allow_html=True)

# ------------------ CHAT INPUT ------------------
user_input = st.chat_input("Message Vibe AI...")

if user_input:
    st.session_state.messages.append(("user", user_input))

    # Retrieve memory
    c.execute("SELECT user_input, ai_response FROM conversations ORDER BY id DESC LIMIT 5")
    past = c.fetchall()

    memory_text = ""
    for u, a in reversed(past):
        memory_text += f"User: {u}\nAI: {a}\n"

    prompt = memory_text + f"User: {user_input}\nAI:"

    # ------------------ GROK API CALL ------------------
    with st.spinner("Vibe AI is thinking..."):
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {st.secrets['GROK_API_KEY']}",
                "Content-Type": "application/json"
            },
            json={
                "model": "grok-1",
                "messages": [
                    {"role": "system", "content": "You are Vibe AI, a smart and modern assistant."},
                    {"role": "user", "content": prompt}
                ]
            }
        )

        ai_response = response.json()["choices"][0]["message"]["content"]

    # Typing animation
    placeholder = st.empty()
    typed = ""
    for char in ai_response:
        typed += char
        placeholder.markdown(f"<div class='ai-bubble'>{typed}</div>", unsafe_allow_html=True)
        time.sleep(0.01)

    st.session_state.messages.append(("ai", ai_response))

    # Save to DB
    c.execute("INSERT INTO conversations (user_input, ai_response) VALUES (?, ?)", (user_input, ai_response))
    conn.commit()
