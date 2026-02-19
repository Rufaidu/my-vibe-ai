import streamlit as st
import google.generativeai as genai
import yt_dlp
import os
import re
import json

# --- 1. DEEPSEEK STYLE UI (MINIMALIST) ---
st.set_page_config(page_title="Vibe AI", page_icon="🧠", layout="centered")

st.markdown("""
<style>
    /* Main Background */
    .stApp { background-color: #ffffff; color: #1a1a1a; }
    [data-theme="dark"] .stApp { background-color: #0e1117; color: #ffffff; }

    /* Hide default Streamlit elements for a clean look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* THE FLOATING BOTTOM BAR (The DeepSeek Look) */
    .stChatInput { 
        position: fixed; 
        bottom: 30px; 
        z-index: 1000; 
        padding: 0 5%;
    }
    
    /* Integrated Plus Button positioning */
    .stFileUploader {
        position: fixed;
        bottom: 38px;
        left: calc(50% - 340px); /* Adjust based on chat width */
        width: 45px !important;
        z-index: 1001;
    }
    
    @media (max-width: 800px) {
        .stFileUploader { left: 20px; }
    }

    /* Styling the Plus Button to be a simple '+' */
    .stFileUploader section { padding: 0 !important; min-height: unset !important; border: none !important; }
    .stFileUploader label, .stFileUploader span, .stFileUploader small { display: none !important; }
    .stFileUploader button {
        background-color: transparent !important;
        color: #888 !important;
        border: 1px solid #ddd !important;
        border-radius: 8px !important;
        height: 40px !important;
        width: 40px !important;
        font-size: 20px !important;
    }

    /* Chat Input Styling */
    [data-testid="stChatInput"] {
        border-radius: 12px !important;
        border: 1px solid #ddd !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. THE TOOLS (DOWNLOADER & MEMORY) ---
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
    if not os.path.exists('downloads'): os.makedirs('downloads')
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# --- 3. BRAIN SETUP ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        active_model = next((m for m in available if "flash" in m), available[0])
        model = genai.GenerativeModel(active_model)
    except:
        st.error("Brain Connection Error.")
        st.stop()
else:
    st.error("Missing API Key.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = load_history()

# --- 4. TOP NAV BAR ---
col_logo, col_new = st.columns([0.8, 0.2])
with col_logo:
    st.subheader("Vibe AI")
with col_new:
    if st.button("＋ New Chat"):
        st.session_state.messages = []
        if os.path.exists(HISTORY_FILE): os.remove(HISTORY_FILE)
        st.rerun()

# --- 5. CHAT DISPLAY ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. FLOATING INPUTS ---
# Plus button for files
uploaded_file = st.file_uploader("+", type=["jpg", "png", "pdf", "txt"], key="plus_vibe")
# Main Chat bar
prompt = st.chat_input("How can Vibe AI help you today?")

# --- 7. PROCESSING ---
if uploaded_file:
    st.session_state.messages.append({"role": "user", "content": f"📎 Attached file: {uploaded_file.name}"})
    save_history(st.session_state.messages)
    st.rerun()

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # URL Detection for Downloads
    url_match = re.search(r'(https?://\S+)', prompt)
    if url_match:
        with st.chat_message("assistant"):
            try:
                with st.spinner("Processing media link..."):
                    path = download_media(url_match.group(1))
                    with open(path, "rb") as f:
                        st.download_button("💾 Download File", f, file_name=os.path.basename(path))
            except:
                st.write("Link detected, but download is unavailable for this site.")
    else:
        # Standard Chat
        with st.chat_message("assistant"):
            context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-5:]])
            response = model.generate_content(f"You are Vibe AI, a helpful assistant. History:\n{context}\nUser: {prompt}")
            st.session_state.messages.append({"role": "assistant", "content": response.text})
    
    save_history(st.session_state.messages)
    st.rerun()
