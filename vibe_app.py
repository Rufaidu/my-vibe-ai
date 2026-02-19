import streamlit as st
import google.generativeai as genai
from PIL import Image
import yt_dlp
import os
import re
import json

# --- 1. THE VIBE AI UI (FIXED CSS) ---
st.set_page_config(page_title="Vibe AI", page_icon="🧠", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #00f2ff; padding-bottom: 120px; }
    h1 { color: #00f2ff; text-shadow: 0 0 10px #00f2ff; text-align: center; }

    /* THE PLUS BUTTON: Shrunk to a small square icon */
    .stFileUploader { 
        position: fixed; 
        bottom: 25px; 
        left: 15px; 
        width: 50px !important; 
        z-index: 1001; 
    }
    .stFileUploader section { padding: 0 !important; min-height: unset !important; border: none !important; }
    .stFileUploader label, .stFileUploader span, .stFileUploader small { display: none !important; }
    
    .stFileUploader button {
        background-color: #161b22 !important;
        color: #00f2ff !important;
        border: 2px solid #00f2ff !important;
        border-radius: 12px !important;
        height: 48px !important;
        width: 48px !important;
        font-size: 28px !important;
        font-weight: bold !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* THE CHAT INPUT: Slimmed and pushed right of the Plus button */
    .stChatInput { 
        position: fixed; 
        bottom: 20px; 
        left: 75px; 
        right: 15px; 
        z-index: 1000; 
        width: auto !important; 
    }
    [data-testid="stChatInput"] { 
        border: 2px solid #00f2ff !important; 
        border-radius: 25px !important; 
        background: #161b22 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. TOOLS & PERSISTENT HISTORY ---
HISTORY_FILE = "vibe_history.json"

def save_history(messages):
    with open(HISTORY_FILE, "w") as f: json.dump(messages, f)

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f: return json.load(f)
        except: return []
    return []

def download_media(url):
    """Restored Video Downloader Tool"""
    if not os.path.exists('downloads'): os.makedirs('downloads')
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# --- 3. AI BRAIN ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        active_model = next((m for m in available if "flash" in m), available[0])
        model = genai.GenerativeModel(active_model)
    except:
        st.error("AI Brain connection failed.")
        st.stop()
else:
    st.error("Missing API Key in Secrets!")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = load_history()

# --- 4. MAIN INTERFACE ---
st.title("🧠 Vibe AI")

# Use a container so the layout stays consistent
chat_holder = st.container()
with chat_holder:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# --- 5. INPUTS (FIXED KEYS) ---
uploaded_file = st.file_uploader("+", type=["jpg", "png", "jpeg"], key="vibe_plus_final")
prompt = st.chat_input("Message Vibe AI...", key="vibe_chat_final")

# --- 6. LOGIC ---
if uploaded_file:
    img = Image.open(uploaded_file)
    with chat_holder:
        st.image(img, width=200)
        if st.button("🚀 Analyze Now"):
            res = model.generate_content(["What is this?", img])
            st.session_state.messages.append({"role": "assistant", "content": res.text})
            save_history(st.session_state.messages)
            st.rerun()

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    url_match = re.search(r'(https?://\S+)', prompt)
    if url_match:
        with chat_holder:
            with st.chat_message("assistant"):
                try:
                    with st.spinner("Fetching media..."):
                        path = download_media(url_match.group(1))
                        with open(path, "rb") as f:
                            # This renders the download button for you
                            st.download_button("💾 DOWNLOAD VIDEO", f, file_name=os.path.basename(path))
                except:
                    st.write("Link detected, but download failed.")
    else:
        with chat_holder:
            with st.chat_message("assistant"):
                # Memory logic: sends last 5 messages for context
                context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-5:]])
                response = model.generate_content(f"History:\n{context}\nUser: {prompt}")
                st.session_state.messages.append({"role": "assistant", "content": response.text})
    
    save_history(st.session_state.messages)
    st.rerun()
