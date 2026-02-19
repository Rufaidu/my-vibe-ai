import streamlit as st
import google.generativeai as genai
from PIL import Image
import yt_dlp
import os
import re
import json

# --- 1. PAGE CONFIG & NEON FOOTER CSS ---
st.set_page_config(page_title="VibeOS", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #00f2ff; padding-bottom: 150px; }
    h1 { color: #00f2ff; text-shadow: 0 0 10px #00f2ff; text-align: center; font-size: 3rem; }
    
    /* Force the Input Area to the Bottom */
    div[data-testid="stVerticalBlock"] > div:last-child {
        position: fixed;
        bottom: 20px;
        left: 5%;
        right: 5%;
        background-color: #161b22;
        padding: 15px;
        border-radius: 25px;
        border: 2px solid #00f2ff;
        z-index: 1000;
        box-shadow: 0 -5px 15px rgba(0, 242, 255, 0.2);
    }

    /* Hide the default uploader labels to make it look like a Plus icon */
    .stFileUploader section { padding: 0; }
    .stFileUploader label { display: none; }
    </style>
""", unsafe_allow_html=True)

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
