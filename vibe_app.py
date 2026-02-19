import streamlit as st
import google.generativeai as genai
from PIL import Image
import yt_dlp
import os
import re
import json

# --- 1. VIBE AI UI SETUP ---
st.set_page_config(page_title="Vibe AI", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #00f2ff; padding-bottom: 100px; }
    h1 { color: #00f2ff; text-shadow: 0 0 10px #00f2ff; text-align: center; }

    /* INTEGRATED PLUS BUTTON */
    /* Shrinks the huge drag-and-drop box into a small icon */
    .stFileUploader { 
        position: fixed; 
        bottom: 25px; 
        left: 20px; 
        width: 50px !important; 
        z-index: 1001; 
    }
    .stFileUploader section { padding: 0 !important; min-height: unset !important; border: none !important; }
    .stFileUploader label, .stFileUploader span, .stFileUploader small { display: none !important; }
    
    /* Make the button look like a '+' */
    .stFileUploader button {
        background-color: #161b22 !important;
        color: #00f2ff !important;
        border: 2px solid #00f2ff !important;
        border-radius: 50% !important;
        height: 48px !important;
        width: 48px !important;
        font-size: 30px !important;
        font-weight: bold !important;
    }

    /* SLIM CHAT INPUT */
    .stChatInput { 
        position: fixed; 
        bottom: 20px; 
        left: 80px; 
        right: 20px; 
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

# --- 2. TOOLS & PERSISTENCE ---
HISTORY_FILE = "vibe_history.json"

def save_history(messages):
    with open(HISTORY_FILE, "w") as f:
        json.dump(messages, f)

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except: return []
    return []

def download_media(url):
    """Restored Video Downloader"""
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

# --- 3. BRAIN INITIALIZATION ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Dynamic model search to avoid the "NotFound" error
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        active_model = next((m for m in available if "flash" in m), "gemini-1.5-flash")
        model = genai.GenerativeModel(active_model)
    except:
        st.error("Brain unavailable.")
        st.stop()
else:
    st.error("Missing API Key!")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = load_history()

# --- 4. MAIN INTERFACE ---
st.title("🧠 Vibe AI")

# Scrollable Chat Display
chat_view = st.container()
with chat_view:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# --- 5. THE PLUS + CHAT INPUT ---
# This creates the file uploader as a small circular button
uploaded_file = st.file_uploader("+", type=["jpg", "png", "jpeg"], key="vibe_plus")
prompt = st.chat_input("Message Vibe AI...")

# --- 6. CORE LOGIC ---
if uploaded_file:
    img = Image.open(uploaded_file)
    with chat_view:
        st.image(img, width=150)
        if st.button("🚀 Analyze Upload"):
            res = model.generate_content(["Describe this for Vibe AI", img])
            st.session_state.messages.append({"role": "assistant", "content": res.text})
            save_history(st.session_state.messages)
            st.rerun()

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # URL Detection for Downloads
    url_match = re.search(r'(https?://\S+)', prompt)
    if url_match:
        with chat_view:
            with st.chat_message("assistant"):
                try:
                    with st.spinner("Fetching media..."):
                        path = download_media(url_match.group(1))
                        with open(path, "rb") as f:
                            st.download_button("💾 DOWNLOAD DETECTED VIDEO", f, file_name=os.path.basename(path))
                except:
                    st.write("Link detected, but download failed.")
    else:
        # Standard Chat
        with chat_view:
            context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-5:]])
            response = model.generate_content(f"History:\n{context}\nUser: {prompt}")
            st.session_state.messages.append({"role": "assistant", "content": response.text})
    
    save_history(st.session_state.messages)
    st.rerun()
        border-radius: 12px !important;
        height: 48px !important;
        width: 48px !important;
        position: relative;
    }
    
    /* Add the '+' sign manually using CSS */
    .stFileUploader button::after {
        content: '+';
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        color: #00f2ff !important;
        font-size: 32px !important;
        font-weight: bold;
    }

    /* SLIM CHAT BAR: Fixed to bottom next to Plus icon */
    .stChatInput { 
        position: fixed; 
        bottom: 15px; 
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

# --- 2. HISTORY & AI SETUP ---
HISTORY_FILE = "vibe_history.json"

def save_history(messages):
    with open(HISTORY_FILE, "w") as f:
        json.dump(messages, f)

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except: return []
    return []

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    try:
        # Dynamic model discovery to fix "NotFound" errors
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        active_model = next((m for m in available if "flash" in m), "gemini-1.5-flash")
        model = genai.GenerativeModel(active_model)
    except:
        st.error("AI Brain connection issue.")
        st.stop()
else:
    st.error("Missing API Key!")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = load_history()

# --- 3. MAIN UI ---
st.title("🧠 Vibe AI")

chat_view = st.container()
with chat_view:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# --- 4. THE INTEGRATED INPUTS ---
uploaded_file = st.file_uploader("", type=["jpg", "png", "jpeg"], key="plus_vibe")
prompt = st.chat_input("Message Vibe AI...")

# --- 5. LOGIC ---
if uploaded_file:
    img = Image.open(uploaded_file)
    with chat_view:
        st.image(img, width=150)
        if st.button("🚀 Analyze Pixels"):
            res = model.generate_content(["Describe this image for Vibe AI", img])
            st.session_state.messages.append({"role": "assistant", "content": res.text})
            save_history(st.session_state.messages)
            st.rerun()

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    url_match = re.search(r'(https?://\S+)', prompt)
    if url_match:
        with chat_view:
            st.info("Link Detected—fetching media...")
            # Video download tool runs here if triggered
    else:
        with chat_view:
            context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-5:]])
            response = model.generate_content(f"History:\n{context}\nUser: {prompt}")
            st.session_state.messages.append({"role": "assistant", "content": response.text})
    
    save_history(st.session_state.messages)
    st.rerun()
