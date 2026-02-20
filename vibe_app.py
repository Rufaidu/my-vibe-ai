import streamlit as st
import sqlite3
import requests
import time

st.set_page_config(page_title="Vibe AI", page_icon="🧠", layout="wide")

# ---------- CSS ----------
st.markdown("""
<style>
body { background-color: #0b0f19; color: white; font-family: 'Segoe UI', sans-serif; }
.block-container { padding-top: 1rem; padding-bottom: 6rem; }
.user-bubble { background: linear-gradient(135deg, #2563eb, #1d4ed8); padding: 12px; border-radius: 18px; margin: 8px 0; text-align: right; max-width: 75%; margin-left: auto; }
.ai-bubble { background-color: #1f2937; padding: 12px; border-radius: 18px; margin: 8px 0; max-width: 75%; }
.stChatInputContainer { position: fixed; bottom: 0; left: 0; right: 0; background-color: #111827; padding: 10px; }
.sidebar .sidebar-content { background-color: #0b0f19; }
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

# ---------- DISPLAY CHAT ----------
for role, message in st.session_state.messages:
    if role == "user":
        st.markdown(f"<div class='user-bubble'>{message}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='ai-bubble'>{message}</div>", unsafe_allow_html=True)

user_input = st.chat_input("Message Vibe AI...")

if user_input:
    st.session_state.messages.append(("user", user_input))

    # build prompt with memory
    c.execute("SELECT user_input, ai_response FROM conversations ORDER BY id DESC LIMIT ?", (memory_limit,))
    past = c.fetchall()
    memory_text = ""
    for u, a in reversed(past):
        memory_text += f"User: {u}\nAI: {a}\n"
    prompt = memory_text + f"User: {user_input}\nAI:"

    # ---------- AI STUDIO API CALL ----------
    with st.spinner("Vibe AI is thinking..."):
        try:
            # Auto-select Gemini: fetch available models
            model_list_url = "https://aistudio.google.com/api-keys/models"  # Replace with your AI Studio endpoint if different
            headers = {
                "Authorization": f"Bearer {st.secrets['AI_STUDIO_API_KEY']}"
            }
            models_resp = requests.get(model_list_url, headers=headers)
            models_resp.raise_for_status()
            available_models = models_resp.json().get("models", [])
            
            if not available_models:
                st.error("No Gemini models available.")
                st.stop()
            
            # pick the first available Gemini model
            selected_model = next((m for m in available_models if "gemini" in m.lower()), available_models[0])
            
            # prediction call
            predict_url = f"https://aistudio.google.com/api/v1/models/{selected_model}/predict"
            payload = {
                "prompt": prompt,
                "max_output_tokens": 250
            }
            response = requests.post(predict_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            ai_response = data.get("prediction", "No response from AI Studio.")

        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {e}")
            st.stop()

    # Typing animation
    placeholder = st.empty()
    typed = ""
    for char in ai_response:
        typed += char
        placeholder.markdown(f"<div class='ai-bubble'>{typed}</div>", unsafe_allow_html=True)
        time.sleep(0.01)

    st.session_state.messages.append(("ai", ai_response))
    c.execute("INSERT INTO conversations (user_input, ai_response) VALUES (?, ?)", (user_input, ai_response))
    conn.commit()
