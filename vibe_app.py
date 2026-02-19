import streamlit as st
import google.generativeai as genai
from PIL import Image
import yt_dlp
import os
import re

# --- 1. PAGE CONFIG & DESIGN ---
st.set_page_config(page_title="VibeOS", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #00f2ff; }
    h1 { color: #00f2ff; text-shadow: 0 0 10px #00f2ff; text-align: center; }
    /* Style the chat input to look like a high-tech console */
    [data-testid="stChatInput"] { border: 2px solid #00f2ff; border-radius: 20px; box-shadow: 0 0 10px #00f2ff; }
    </style>
""", unsafe_allow_html=True)

# --- 2. THE TOOLS (FUNCTIONS) ---
def download_video(url):
    """Downloads video and returns the file path."""
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# --- 3. SET UP THE BRAIN ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Use 'flash-latest' to resolve the NotFound error
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
else:
    st.error("Missing API Key in Secrets!")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 4. MAIN INTERFACE ---
st.title("🧠 VibeOS")

# Show history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# INTEGRATED CHAT: This line adds the plus icon and accepts files
prompt_data = st.chat_input("Ask VibeOS, paste a link, or tap '+' to upload...", accept_file="multiple")

if prompt_data:
    user_text = prompt_data.text
    uploaded_files = prompt_data.files  # Files from the '+' icon

    # Handle Uploaded Files
    if uploaded_files:
        for file in uploaded_files:
            if file.type.startswith("image/"):
                img = Image.open(file)
                st.image(img, caption="VibeOS Visual Feed", width=400)
                with st.chat_message("assistant"):
                    with st.spinner("Analyzing pixels..."):
                        res = model.generate_content(["What is in this image?", img])
                        st.markdown(res.text)
                        st.session_state.messages.append({"role": "assistant", "content": res.text})

    # Handle Text and URLs
    if user_text:
        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown(user_text)

        # Detect URL for Auto-Download
        url_match = re.search(r'(https?://\S+)', user_text)
        if url_match:
            video_url = url_match.group(1)
            with st.chat_message("assistant"):
                try:
                    with st.spinner(f"Intercepting media from {video_url}..."):
                        file_path = download_video(video_url)
                        with open(file_path, "rb") as f:
                            st.download_button("💾 DOWNLOAD DETECTED VIDEO", f, file_name=os.path.basename(file_path))
                except Exception as e:
                    st.write("I detected a link, but I couldn't fetch the video.")

        # Regular AI Response
        else:
            with st.chat_message("assistant"):
                context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
                response = model.generate_content(f"Context: {context}\nUser: {user_text}")
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
