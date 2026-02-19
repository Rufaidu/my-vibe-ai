import streamlit as st
import google.generativeai as genai
from PIL import Image
import yt_dlp
import os
import re
import json # Used for saving/loading history

# --- 1. PAGE CONFIG & DESIGN ---
st.set_page_config(page_title="VibeOS", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #00f2ff; }
    h1 { color: #00f2ff; text-shadow: 0 0 10px #00f2ff; text-align: center; }
    [data-testid="stChatInput"] { border: 2px solid #00f2ff; border-radius: 20px; box-shadow: 0 0 10px #00f2ff; }
    </style>
""", unsafe_allow_html=True)

# --- 2. THE BRAIN & HISTORY TOOLS ---
HISTORY_FILE = "vibe_chat_history.json"

def save_history(messages):
    with open(HISTORY_FILE, "w") as f:
        json.dump(messages, f)

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Dynamic Model Picker (Fixed for 2026)
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    active_model = next((m for m in available_models if "flash" in m), available_models[0])
    model = genai.GenerativeModel(active_model)
else:
    st.error("Missing API Key!")
    st.stop()

# Load history into the app session on startup
if "messages" not in st.session_state:
    st.session_state.messages = load_history()

# --- 3. VIDEO DOWNLOADER ---
def download_video(url):
    if not os.path.exists('downloads'): os.makedirs('downloads')
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# --- 4. MAIN INTERFACE ---
st.title("🧠 VibeOS")

# Display persistent history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Layout for PLUS icon and Chat
col1, col2 = st.columns([0.1, 0.9])
with col1:
    uploaded_file = st.file_uploader(" ", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
with col2:
    prompt = st.chat_input("Command VibeOS or paste a URL...")

# Process Image Analysis
if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="VibeOS Visual Stream", width=300)
    if st.button("🚀 Analyze"):
        with st.chat_message("assistant"):
            res = model.generate_content(["Analyze this image.", img])
            st.markdown(res.text)
            st.session_state.messages.append({"role": "assistant", "content": res.text})
            save_history(st.session_state.messages) # SAVE

# Process Chat & URL Detection
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # URL Check
    url_match = re.search(r'(https?://\S+)', prompt)
    if url_match:
        video_url = url_match.group(1)
        with st.chat_message("assistant"):
            try:
                with st.spinner("Intercepting..."):
                    path = download_video(video_url)
                    with open(path, "rb") as f:
                        st.download_button("💾 DOWNLOAD VIDEO", f, file_name=os.path.basename(path))
            except:
                st.write("Could not fetch video.")
    else:
        # Chat Brain
        with st.chat_message("assistant"):
            context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-10:]])
            response = model.generate_content(f"History:\n{context}\nUser: {prompt}")
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
    
    # Save the conversation after every message
    save_history(st.session_state.messages)

# Clear History Button (Optional Sidebar)
if st.sidebar.button("🗑️ Wipe All History"):
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
    st.session_state.messages = []
    st.rerun()
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
