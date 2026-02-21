import streamlit as st
import re
import time
import os
import tempfile
import requests
from google import genai
import yt_dlp
import mimetypes

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

# ---------- SESSION ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------- HEADER ----------
st.markdown("<h2 style='text-align:center;'>🧠 Vibe AI</h2>", unsafe_allow_html=True)

# ---------- FORMAT SELECTOR ----------
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
    url_pattern = r"(https?://[^\s]+)"
    return re.findall(url_pattern, text)

# ---------- MEDIA TYPE DETECTION ----------
def detect_media_type(url):
    try:
        ydl_opts = {"quiet": True, "skip_download": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
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
    except Exception:
        return "unknown", None

# ---------- SMART DOWNLOAD ----------
def download_media(url, mode):
    temp_dir = tempfile.TemporaryDirectory()
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        ydl_opts = {
            "outtmpl": os.path.join(temp_dir.name, "%(title)s.%(ext)s"),
            "quiet": True,
            "noplaylist": True,
            "retries": 10,
            "http_headers": headers,
        }

        # Force MP3
        if mode == "MP3 (Audio Only)":
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        # Force MP4
        elif mode == "MP4 (Video)":
            ydl_opts["format"] = "bestvideo+bestaudio/best"
            ydl_opts["merge_output_format"] = "mp4"
        # Auto detect: best available
        else:
            ydl_opts["format"] = "best"

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

            if mode == "MP3 (Audio Only)":
                file_path = os.path.splitext(file_path)[0] + ".mp3"
            elif mode == "MP4 (Video)":
                file_path = os.path.splitext(file_path)[0] + ".mp4"

        return file_path, temp_dir

    except Exception:
        # fallback for direct files (images, PDFs)
        local_filename = os.path.join(temp_dir.name, url.split("/")[-1])
        r = requests.get(url, stream=True, headers=headers)
        r.raise_for_status()
        with open(local_filename, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        return local_filename, temp_dir

# ---------- INPUT ----------
user_input = st.chat_input("Message Vibe AI...")

if user_input:
    st.session_state.messages.append(("user", user_input))
    display_chat()

    urls = contains_url(user_input)

    if urls:
        url = urls[0]

        # Detect type first
        media_type, ext = detect_media_type(url)
        st.info(f"Detected: {media_type.upper()} | Original Format: .{ext}")

        # Smart auto-switch
        if media_type == "video":
            selected_mode = "MP4 (Video)"
        elif media_type == "audio":
            selected_mode = "MP3 (Audio Only)"
        else:
            selected_mode = "Auto Detect"

        # Respect user selection
        if download_mode != "Auto Detect":
            selected_mode = download_mode

        # Download
        with st.spinner("Processing download..."):
            try:
                file_path, temp_dir = download_media(url, selected_mode)

                file_name = os.path.basename(file_path)
                mime_type, _ = mimetypes.guess_type(file_name)
                if mime_type is None:
                    if media_type == "video":
                        mime_type = "video/mp4"
                    elif media_type == "audio":
                        mime_type = "audio/mpeg"
                    else:
                        mime_type = "application/octet-stream"

                with open(file_path, "rb") as f:
                    st.download_button(
                        "📥 Download File",
                        data=f,
                        file_name=file_name,
                        mime=mime_type
                    )

                ai_response = f"Vibe AI prepared your {media_type} download successfully."

            except Exception as e:
                ai_response = f"Download failed: {e}"

    else:
        # ---------- AI RESPONSE ----------
        memory_text = ""
        past = st.session_state.messages[-10:]
        for role, msg in past:
            if role == "user":
                memory_text += f"User: {msg}\n"
            else:
                memory_text += f"AI: {msg}\n"

        prompt = (
            "You are Vibe AI. Be helpful and concise.\n\n"
            + memory_text
            + f"User: {user_input}\nAI:"
        )

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
