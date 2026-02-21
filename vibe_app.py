import streamlit as st
import re
import time
import os
import tempfile
import requests
import yt_dlp
import mimetypes
from google import genai

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Vibe AI", page_icon="🧠", layout="wide")

# ---------- STYLING ----------
st.markdown("""
<style>
body { background-color: #0b0f19; color: white; font-family: 'Segoe UI', sans-serif; }
.user-bubble { background: linear-gradient(135deg, #2563eb, #1d4ed8); padding: 12px; border-radius: 18px; margin: 8px 0; text-align: right; max-width: 75%; margin-left: auto; }
.ai-bubble { background-color: #1f2937; padding: 12px; border-radius: 18px; margin: 8px 0; max-width: 75%; }
.chat-container { max-height: 70vh; overflow-y: auto; }
</style>
""", unsafe_allow_html=True)

# ---------- SESSION ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------- HEADER ----------
st.markdown("<h2 style='text-align:center;'>🧠 Vibe AI</h2>", unsafe_allow_html=True)

# ---------- SIDEBAR ----------
download_mode = st.sidebar.selectbox(
    "Download Format",
    ["Auto Detect", "MP4 (Video)", "MP3 (Audio Only)"]
)

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
    return re.findall(r"(https?://[^\s]+)", text)

# ---------- MEDIA DETECTION ----------
def detect_media_type(url):
    try:
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(url, download=False)

        ext = info.get("ext", "")
        vcodec = info.get("vcodec")
        acodec = info.get("acodec")

        if vcodec and vcodec != "none":
            return "video", ext
        elif acodec and acodec != "none":
            return "audio", ext
        else:
            return "photo", ext
    except:
        return "unknown", None

# ---------- ROBUST DOWNLOAD ----------
def download_media(url, mode):
    temp_dir = tempfile.TemporaryDirectory()

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/116.0.5845.97 Safari/537.36"
        )
    }

    ydl_opts = {
        "outtmpl": os.path.join(temp_dir.name, "%(title)s.%(ext)s"),
        "quiet": True,
        "noplaylist": True,
        "retries": 10,
        "http_headers": headers,
        "merge_output_format": "mp4",
    }

    # Mode logic
    if mode == "MP3 (Audio Only)":
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    elif mode == "MP4 (Video)":
        ydl_opts["format"] = "bestvideo+bestaudio/best"
    else:
        ydl_opts["format"] = "bestvideo+bestaudio/best"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)

        if mode == "MP3 (Audio Only)":
            file_path = os.path.splitext(file_path)[0] + ".mp3"
        else:
            file_path = os.path.splitext(file_path)[0] + ".mp4"

    # Validate file
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        raise Exception("Download failed or empty file.")

    return file_path, temp_dir

# ---------- INPUT ----------
user_input = st.chat_input("Message Vibe AI...")

if user_input:
    st.session_state.messages.append(("user", user_input))
    display_chat()

    urls = contains_url(user_input)

    if urls:
        url = urls[0]

        media_type, ext = detect_media_type(url)
        st.info(f"Detected: {media_type.upper()} | Original: .{ext}")

        # Smart auto-switch
        if media_type == "video":
            selected_mode = "MP4 (Video)"
        elif media_type == "audio":
            selected_mode = "MP3 (Audio Only)"
        else:
            selected_mode = "Auto Detect"

        if download_mode != "Auto Detect":
            selected_mode = download_mode

        with st.spinner("Downloading..."):
            try:
                file_path, temp_dir = download_media(url, selected_mode)

                file_name = os.path.basename(file_path)
                mime_type, _ = mimetypes.guess_type(file_name)
                if mime_type is None:
                    mime_type = "application/octet-stream"

                with open(file_path, "rb") as f:
                    st.download_button(
                        "📥 Download File",
                        data=f,
                        file_name=file_name,
                        mime=mime_type
                    )

                ai_response = "Download completed successfully."

            except Exception as e:
                ai_response = f"Download failed: {e}"

    else:
        # ---------- AI RESPONSE ----------
        memory_text = ""
        for role, msg in st.session_state.messages[-10:]:
            memory_text += f"{role}: {msg}\n"

        prompt = f"You are Vibe AI.\n{memory_text}\nUser: {user_input}\nAI:"

        try:
            client = genai.Client(api_key=st.secrets["AI_STUDIO_API_KEY"])
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            ai_response = response.text.strip()
        except Exception as e:
            ai_response = f"AI Error: {e}"

    # ---------- TYPING EFFECT ----------
    display_text = ""
    for char in ai_response:
        display_text += char
        temp = st.session_state.messages + [("ai", display_text)]
        chat_placeholder.empty()
        with chat_placeholder.container():
            for role, msg in temp:
                if role == "user":
                    st.markdown(f"<div class='user-bubble'>{msg}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='ai-bubble'>{msg}</div>", unsafe_allow_html=True)
        time.sleep(0.01)

    st.session_state.messages.append(("ai", ai_response))
    display_chat()
