import streamlit as st
import re
import time
import os
import tempfile
import requests
from google import genai
import yt_dlp
import sqlite3
from datetime import datetime, timedelta

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

# Create table with timestamp
c.execute("""
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_input TEXT,
    ai_response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# ---------- SESSION ----------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "memory_limit" not in st.session_state:
    st.session_state.memory_limit = 5

# ---------- LOAD PAST 7 DAYS ----------
seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
c.execute("SELECT user_input, ai_response FROM conversations WHERE created_at >= ? ORDER BY id ASC",
          (seven_days_ago,))
messages = c.fetchall()
st.session_state.messages = []
for u, a in messages:
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

    # ---------- SAVE USER INPUT ----------
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        c.execute("INSERT INTO conversations (user_input, ai_response, created_at) VALUES (?, ?, ?)", (user_input, "", now_str))
        conn.commit()
        conversation_row_id = c.lastrowid
    except Exception as e:
        st.error(f"Failed to save user input: {e}")
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
        memory_text = ""
        past = st.session_state.messages[-st.session_state.memory_limit*2:]  # last n user+AI pairs
        for role, msg in past:
            if role == "user":
                memory_text += f"User: {msg}\n"
            else:
                memory_text += f"AI: {msg}\n"

        system_instruction = (
            "You are Vibe AI, a helpful assistant. "
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

    # ---------- UPDATE AI RESPONSE ----------
    st.session_state.messages.append(("ai", ai_response))
    display_chat()

    try:
        c.execute(
            "UPDATE conversations SET ai_response=? WHERE id=?",
            (ai_response, conversation_row_id)
        )
        conn.commit()
    except Exception as e:
        st.error(f"Failed to save AI response: {e}")
