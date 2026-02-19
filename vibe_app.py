import streamlit as st
import google.generativeai as genai
from PIL import Image
import yt_dlp
import os
import re

# --- 1. PAGE CONFIG & DARK THEME CSS ---
st.set_page_config(page_title="VibeOS", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #00f2ff; }
    /* Glowing Title */
    h1 { color: #00f2ff; text-shadow: 0 0 10px #00f2ff; text-align: center; }
    /* Chat Input Styling */
    [data-testid="stChatInput"] { border: 2px solid #00f2ff; border-radius: 20px; box-shadow: 0 0 10px #00f2ff; }
    </style>
""", unsafe_allow_html=True)

# --- 2. THE BRAIN & TOOLS ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
else:
    st.error("Missing API Key!")
    st.stop()

def download_video(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
    }
    if not os.path.exists('downloads'): os.makedirs('downloads')
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# --- 3. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 4. MAIN INTERFACE ---
st.title("🧠 VibeOS")

# Display history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# INTEGRATED CHAT & PLUS ICON
# The accept_file=True adds the plus/attachment icon automatically
prompt_data = st.chat_input("Message VibeOS, paste a URL, or attach a file...", accept_file=True)

if prompt_data:
    user_text = prompt_data.text
    attached_files = prompt_data.files # This is where the plus-icon files go

    # Handle Attached Image
    if attached_files:
        for file in attached_files:
            img = Image.open(file)
            st.image(img, caption="Attached Image", width=300)
            with st.chat_message("assistant"):
                with st.spinner("Analyzing image..."):
                    res = model.generate_content(["Describe this image for VibeOS", img])
                    st.markdown(res.text)
                    st.session_state.messages.append({"role": "assistant", "content": res.text})

    # Handle Text / URL Detection
    if user_text:
        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown(user_text)

        # Detect URL for Auto-Download
        url_match = re.search(r'(https?://\S+)', user_text)
        if url_match:
            video_url = url_match.group(1)
            with st.chat_message("assistant"):
                with st.spinner(f"Detecting video at {video_url}..."):
                    try:
                        file_path = download_video(video_url)
                        with open(file_path, "rb") as f:
                            st.download_button("💾 Download Detected Video", f, file_name=os.path.basename(file_path))
                    except:
                        st.write("I see a link, but I couldn't fetch a video from it.")

        # Regular Chat Response
        else:
            with st.chat_message("assistant"):
                history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
                response = model.generate_content(f"Context: {history}\nUser: {user_text}")
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            with st.chat_message("assistant"):
                with st.spinner("Analyzing image..."):
                    res = model.generate_content(["Describe this image for VibeOS", img])
                    st.markdown(res.text)
                    st.session_state.messages.append({"role": "assistant", "content": res.text})

    # Handle Text / URL Detection
    if user_text:
        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown(user_text)

        # Detect URL for Auto-Download
        url_match = re.search(r'(https?://\S+)', user_text)
        if url_match:
            video_url = url_match.group(1)
            with st.chat_message("assistant"):
                with st.spinner(f"Detecting video at {video_url}..."):
                    try:
                        file_path = download_video(video_url)
                        with open(file_path, "rb") as f:
                            st.download_button("💾 Download Detected Video", f, file_name=os.path.basename(file_path))
                    except:
                        st.write("I see a link, but I couldn't fetch a video from it.")

        # Regular Chat Response
        else:
            with st.chat_message("assistant"):
                history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
                response = model.generate_content(f"Context: {history}\nUser: {user_text}")
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # THIS LINE IS VITAL:
        return ydl.prepare_filename(info) 

# --- 4. SESSION MEMORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 5. SIDEBAR: THE MULTIMODAL HUB ---
with st.sidebar:
    st.title("📟 VibeOS Tools")
    
    # Video Downloader
    st.subheader("🎥 Media Fetcher")
    video_url = st.text_input("Paste Video Link", placeholder="YouTube, X, etc.")
    if st.button("Generate Download"):
        if video_url:
            try:
                with st.spinner("Fetching..."):
                    file_path = download_video(video_url)
                    with open(file_path, "rb") as f:
                        st.download_button("💾 DOWNLOAD VIDEO", f, file_name=os.path.basename(file_path))
                st.success("Media captured!")
            except Exception as e:
                st.error(f"Fetch failed: {e}")

    st.divider()

    # Image Analysis
    st.subheader("🔍 Visual Scanner")
    uploaded_file = st.file_uploader("Upload an Image", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, use_container_width=True)
        if st.button("🚀 SCAN PIXELS"):
            with st.spinner("Thinking..."):
                # Multimodal call: prompt + image
                res = model.generate_content(["Analyze this image for VibeOS and describe it.", img])
                st.info(res.text)

    if st.button("Clear Memory"):
        st.session_state.messages = []
        st.rerun()

# --- 6. MAIN CHAT SYSTEM ---
st.title("🧠 VibeOS")
st.subheader("Your Personal AI Workspace")

# Re-display memory
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Interaction Logic
if prompt := st.chat_input("Command the Brain..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Compile history for memory context
        history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
        response = model.generate_content(f"History context:\n{history}\n\nUser: {prompt}")
        st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
