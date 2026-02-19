import streamlit as st
import google.generativeai as genai
import yt_dlp
import os
import re
import json

# --- 1. THE DEEPSEEK CLONE INTERFACE (CSS) ---
st.set_page_config(page_title="Vibe AI", page_icon="🧠", layout="centered")

st.markdown("""
<style>
    /* DeepSeek Aesthetic: Clean & Spaced */
    .stApp { background-color: #f4f4f7; color: #1a1a1a; }
    [data-theme="dark"] .stApp { background-color: #0e1117; color: #e0e0e0; }

    /* Centered Content Area */
    .main .block-container { max-width: 800px; padding-top: 2rem; }

    /* THE FLOATING INPUT BAR */
    .stChatInput { 
        position: fixed; 
        bottom: 30px; 
        z-index: 1000; 
        background: transparent !important;
    }
    [data-testid="stChatInput"] { 
        border: 1px solid #d1d5db !important; 
        border-radius: 16px !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08) !important;
        background-color: white !important;
    }

    /* THE PLUS ICON: Integrated next to the input */
    .stFileUploader {
        position: fixed;
        bottom: 38px;
        left: calc(50% - 380px); /* Adjust based on centered layout */
        width: 40px !important;
        z-index: 1001;
    }
    @media (max-width: 800px) { .stFileUploader { left: 10px; } }

    /* Hide the 'Drag and Drop' text - make it just an icon */
    .stFileUploader section { padding: 0 !important; min-height: unset !important; border: none !important; background: transparent !important; }
    .stFileUploader label, .stFileUploader span, .stFileUploader small { display: none !important; }
    .stFileUploader button {
        background-color: #f9fafb !important;
        color: #4b5563 !important;
        border: 1px solid #d1d5db !important;
        border-radius: 50% !important;
        height: 40px !important;
        width: 40px !important;
        font-size: 20px !important;
    }

    /* Message Bubbles */
    .stChatMessage { border-radius: 15px; margin-bottom: 1rem; border: none !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. THE ENGINE ---
HISTORY_FILE = "vibe_history.json"

def save_history(messages):
    with open(HISTORY_FILE, "w") as f: json.dump(messages, f)

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f: return json.load(f)
        except: return []
    return []

def download_video(url):
    """Simplified Downloader"""
    if not os.path.exists('downloads'): os.makedirs('downloads')
    ydl_opts = {'format': 'best', 'outtmpl': 'downloads/%(title)s.%(ext)s', 'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# --- 3. AI SETUP ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = next((m for m in available if "flash" in m), available[0])
        model = genai.GenerativeModel(model_name)
    except:
        st.error("Brain Connection Failed.")
        st.stop()
else:
    st.error("Missing API Key in Secrets!")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = load_history()

# --- 4. TOP BAR ---
col_logo, col_new = st.columns([0.8, 0.2])
with col_logo:
    st.title("Vibe AI")
with col_new:
    if st.button("＋ New Chat"):
        st.session_state.messages = []
        if os.path.exists(HISTORY_FILE): os.remove(HISTORY_FILE)
        st.rerun()

# --- 5. CHAT DISPLAY ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. INPUTS (UNIQUE KEYS TO PREVENT DUPLICATE ID ERROR) ---
uploaded_file = st.file_uploader("+", type=["jpg", "png", "pdf", "txt"], key="vibe_plus_v3")
prompt = st.chat_input("How can I help you today?", key="vibe_chat_v3")

# --- 7. LOGIC ---
if uploaded_file:
    st.session_state.messages.append({"role": "user", "content": f"📎 Attached: {uploaded_file.name}"})
    save_history(st.session_state.messages)
    st.rerun()

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # URL Detection Logic
    url_match = re.search(r'(https?://\S+)', prompt)
    if url_match:
        with st.chat_message("assistant"):
            try:
                with st.spinner("Analyzing link..."):
                    path = download_video(url_match.group(1))
                    with open(path, "rb") as f:
                        st.download_button("💾 Download Detected File", f, file_name=os.path.basename(path))
            except:
                st.write("I found a link, but I couldn't download it. Please check the URL.")
    else:
        # Standard AI Response
        with st.chat_message("assistant"):
            context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-5:]])
            response = model.generate_content(f"System: You are Vibe AI. \n{context}\nUser: {prompt}")
            st.session_state.messages.append({"role": "assistant", "content": response.text})
    
    save_history(st.session_state.messages)
    st.rerun()
