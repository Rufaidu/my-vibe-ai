import streamlit as st
import google.generativeai as genai
from PIL import Image
import yt_dlp
import os
import re
import json

# --- 1. PAGE CONFIG & INTEGRATED UI CSS ---
st.set_page_config(page_title="VibeOS", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #00f2ff; }
    h1 { color: #00f2ff; text-shadow: 0 0 10px #00f2ff; text-align: center; margin-top: -50px; }
    
    /* THE MAGIC: Pinned Bottom Bar */
    .fixed-bottom {
        position: fixed;
        bottom: 30px;
        left: 50%;
        transform: translateX(-50%);
        width: 90%;
        max-width: 800px;
        z-index: 1000;
        display: flex;
        align-items: center;
        background: #161b22;
        padding: 10px;
        border-radius: 30px;
        border: 2px solid #00f2ff;
        box-shadow: 0 0 15px rgba(0, 242, 255, 0.4);
    }

    /* Shrink the File Uploader to look like a small button */
    .stFileUploader { width: 50px !important; }
    .stFileUploader section { padding: 0 !important; min-height: unset !important; border: none !important; }
    .stFileUploader label { display: none; }
    .stFileUploader div div { background-color: transparent !important; }
    
    /* Custom Chat Input Adjustments */
    .stChatInput { border: none !important; background: transparent !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. BRAIN & HISTORY LOGIC ---
HISTORY_FILE = "vibe_history.json"

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
    # Dynamic Model Discovery to fix "NotFound" errors
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    active_model = next((m for m in models if "flash" in m), models[0])
    model = genai.GenerativeModel(active_model)
else:
    st.error("API Key Missing in Secrets!")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = load_history()

# --- 3. VIDEO DOWNLOADER (HUMAN BYPASS) ---
def download_video(url):
    if not os.path.exists('downloads'): os.makedirs('downloads')
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# --- 4. MAIN INTERFACE ---
st.title("🧠 VibeOS")

# Scrollable container for chat history
chat_holder = st.container()
with chat_holder:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# --- 5. THE INTEGRATED FOOTER (PLUS + CHAT) ---
# Using columns to put the file uploader (Plus) and text box on one line
footer_col1, footer_col2 = st.columns([0.1, 0.9])

with footer_col1:
    # This acts as your "Plus" button
    uploaded_file = st.file_uploader("+", type=["jpg", "png", "jpeg"], key="plus")

with footer_col2:
    prompt = st.chat_input("Message VibeOS...")

# Handle Logic
if uploaded_file:
    img = Image.open(uploaded_file)
    with chat_holder:
        st.image(img, width=200)
        if st.button("🚀 Analyze"):
            res = model.generate_content(["Describe this image for VibeOS", img])
            st.session_state.messages.append({"role": "assistant", "content": res.text})
            save_history(st.session_state.messages)
            st.rerun()

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_history(st.session_state.messages)
    
    # URL Detection for Videos
    url_match = re.search(r'(https?://\S+)', prompt)
    if url_match:
        with chat_holder:
            try:
                path = download_video(url_match.group(1))
                with open(path, "rb") as f:
                    st.download_button("💾 DOWNLOAD VIDEO", f, file_name=os.path.basename(path))
            except:
                st.write("Fetch failed.")
    else:
        with chat_holder:
            context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-5:]])
            response = model.generate_content(f"History:\n{context}\nUser: {prompt}")
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            save_history(st.session_state.messages)
    st.rerun()
# --- 2. TOOLS & BRAIN SETUP ---
def download_video(url):
    if not os.path.exists('downloads'): os.makedirs('downloads')
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# Fix for "Missing API Key" (image 1000050777.jpg)
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Dynamic discovery to avoid "NotFound" errors
    available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    active_model = next((m for m in available if "flash" in m), available[0])
    model = genai.GenerativeModel(active_model)
else:
    st.error("API Key Missing! Go to Streamlit -> Settings -> Secrets and add GOOGLE_API_KEY")
    st.stop()

# --- 3. HISTORY LOGIC ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 4. MAIN UI ---
st.title("🧠 VibeOS")

# Scrollable Chat Area
chat_container = st.container()
with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# --- 5. THE INTEGRATED FOOTER (PLUS + CHAT) ---
# This container is pinned to the bottom by the CSS above
with st.container():
    col1, col2 = st.columns([0.15, 0.85])
    
    with col1:
        # The "Plus" button (hidden label uploader)
        uploaded_file = st.file_uploader("Upload", type=["jpg", "png", "jpeg"], key="plus_btn")
    
    with col2:
        prompt = st.chat_input("Command VibeOS or paste a URL...")

# Handle Image Upload
if uploaded_file:
    img = Image.open(uploaded_file)
    with chat_container:
        st.image(img, width=250, caption="Visual Input Received")
        if st.button("🚀 Analyze Pixels"):
            res = model.generate_content(["Describe this image for VibeOS", img])
            st.session_state.messages.append({"role": "assistant", "content": res.text})
            st.rerun()

# Handle Chat & Links
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # URL Detection
    url_match = re.search(r'(https?://\S+)', prompt)
    if url_match:
        with chat_container:
            with st.chat_message("assistant"):
                try:
                    path = download_video(url_match.group(1))
                    with open(path, "rb") as f:
                        st.download_button("💾 DOWNLOAD VIDEO", f, file_name=os.path.basename(path))
                except:
                    st.write("Link detected, but the human-bypass failed.")
    else:
        # Standard Chat
        with chat_container:
            with st.chat_message("assistant"):
                context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-5:]])
                response = model.generate_content(f"History:\n{context}\nUser: {prompt}")
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
    st.rerun()
