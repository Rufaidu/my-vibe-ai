import streamlit as st
import sqlite3
import time
import re
import os
import tempfile
from google import genai
import yt_dlp
import requests

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Vibe AI", page_icon="🧠", layout="wide")

# ---------- CSS ----------
st.markdown("""
<style>
body { background-color: #0b0f19; color: white; font-family: 'Segoe UI', sans-serif; }
.user-bubble { background: linear-gradient(135deg, #2563eb, #1d4ed8); padding: 12px; border-radius: 18px; margin: 8px 0; text-align: right; max-width: 75%; margin-left: auto; word-wrap: break-word; }
.ai-bubble { background-color: #1f2937; padding: 12px; border-radius: 18px; margin: 8px 0; max-width: 75%; word-wrap: break-word; }
.chat-container { max-height: 70vh; overflow-y: auto; }
</style>
""", unsafe_allow_html=True)

# ---------- DATABASE ----------
conn = sqlite3.connect("vibe_memory.db", check_same_thread=False)
c = conn.cursor()

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
    ai_response TEXT
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

    c.execute("SELECT id, title FROM threads ORDER BY created_at DESC")
    threads = c.fetchall()
    thread_dict = {t[1]: t[0] for t in threads}

    selected = st.selectbox("Select Chat", ["New Chat"] + list(thread_dict.keys()))

    if selected == "New Chat":
        st.session_state.thread_id = None
        st.session_state.messages = []
    else:
        st.session_state.thread_id = thread_dict[selected]
        if st.session_state.thread_id is not None:
            c.execute(
                "SELECT user_input, ai_response FROM conversations WHERE thread_id=? ORDER BY id ASC",
                (st.session_state.thread_id,)
            )
            data = c.fetchall()
            st.session_state.messages = []
            for u, a in data:
                st.session_state.messages.append(("user", u))
                st.session_state.messages.append(("ai", a))

# ---------- HEADER ----------
st.markdown("<h2 style='text-align:center;'>🧠 Vibe AI</h2>", unsafe_allow_html=True)
chat_placeholder = st.empty()

def display_chat():
    with chat_placeholder.container():
        st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
        for role, msg in st.session_state.messages:
            if role == "user":
                st.markdown(f"<div class='user-bubble'>{msg}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='ai-bubble'>{msg}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

display_chat()

# ---------- URL DETECTION ----------
def contains_url(text):
    url_pattern = r"(https?://[^\s]+)"
    return re.findall(url_pattern, text)

# ---------- DOWNLOAD FUNCTION ----------
def download_media(url):
    temp_dir = tempfile.TemporaryDirectory()
    file_path = None

    if "youtube.com" in url or "youtu.be" in url or "tiktok.com" in url:
        ydl_opts = {
            "outtmpl": os.path.join(temp_dir.name, "%(title)s.%(ext)s"),
            "format": "best",
            "quiet": True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
    else:
        local_filename = os.path.join(temp_dir.name, url.split("/")[-1])
        r = requests.get(url, stream=True)
        r.raise_for_status()
        with open(local_filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        file_path = local_filename

    return file_path, temp_dir

# ---------- INPUT ----------
user_input = st.chat_input("Message Vibe AI...")

if user_input:
    st.session_state.messages.append(("user", user_input))
    display_chat()

    # ---------- ENSURE THREAD EXISTS IMMEDIATELY ----------
    if st.session_state.thread_id is None:
        title = (user_input[:30] if len(user_input) > 0 else "New Chat")
        try:
            c.execute("INSERT INTO threads (title) VALUES (?)", (title,))
            conn.commit()
            st.session_state.thread_id = c.lastrowid
        except Exception as e:
            st.error(f"Failed to create thread: {e}")
            st.stop()

    # ---------- SAVE PLACEHOLDER CONVERSATION ----------
    try:
        c.execute(
            "INSERT INTO conversations (thread_id, user_input, ai_response) VALUES (?, ?, ?)",
            (st.session_state.thread_id, user_input, "")
        )
        conn.commit()
        conversation_row_id = c.lastrowid
    except Exception as e:
        st.error(f"Failed to save conversation: {e}")
        st.stop()

    # ---------- HANDLE URL DOWNLOAD ----------
    urls = contains_url(user_input)
    if urls:
        url = urls[0]
        with st.spinner("Downloading media..."):
            try:
                file_path, temp_dir = download_media(url)
                st.success("Download ready!")

                with open(file_path, "rb") as f:
                    st.download_button(
                        label="📥 Download File",
                        data=f,
                        file_name=os.path.basename(file_path)
                    )

                ai_response = "Vibe AI detected a URL and prepared your download."

            except Exception as e:
                ai_response = f"Download failed: {e}"

    else:
        # ---------- MEMORY ----------
        c.execute(
            f"SELECT user_input, ai_response FROM conversations WHERE thread_id=? ORDER BY id DESC LIMIT {memory_limit}",
            (st.session_state.thread_id,)
        )
        past = c.fetchall()

        memory_text = ""
        for u, a in reversed(past):
            memory_text += f"User: {u}\nAI: {a}\n"

        system_instruction = (
            "You are Vibe AI, a powerful assistant. "
            "Always refer to yourself as 'Vibe AI'. "
            "Be concise and helpful."
        )

        prompt = system_instruction + "\n\n" + memory_text + f"User: {user_input}\nAI:"

        try:
            client = genai.Client(api_key=st.secrets["AI_STUDIO_API_KEY"])
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            ai_response = response.text.strip()
        except Exception as e:
            ai_response = f"AI Error: {e}"

    # ---------- TYPING ANIMATION ----------
    display_text = ""
    for char in ai_response:
        display_text += char
        temp = st.session_state.messages + [("ai", display_text)]
        chat_placeholder.empty()
        with chat_placeholder.container():
            st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
            for role, msg in temp:
                if role == "user":
                    st.markdown(f"<div class='user-bubble'>{msg}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='ai-bubble'>{msg}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        time.sleep(0.01)

    # ---------- UPDATE CONVERSATION ----------
    st.session_state.messages.append(("ai", ai_response))
    display_chat()

    try:
        c.execute(
            "UPDATE conversations SET ai_response=? WHERE id=?",
            (ai_response, conversation_row_id)
        )
        conn.commit()
    except Exception as e:
        st.error(f"Failed to update conversation: {e}")
