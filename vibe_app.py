import streamlit as st
import google.generativeai as genai
from PIL import Image
import yt_dlp
import os
import re
import json

# --- 1. THE VIBE AI INTERFACE (CSS) ---
st.set_page_config(page_title="Vibe AI", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    /* Dark Theme */
    .stApp { background-color: #0e1117; color: #00f2ff; padding-bottom: 100px; }
    h1 { color: #00f2ff; text-shadow: 0 0 10px #00f2ff; text-align: center; }

    /* INTEGRATED PLUS BUTTON: Shrinks giant box to a small icon */
    .stFileUploader { 
        position: fixed; 
        bottom: 32px; 
        left: 20px; 
        width: 50px !important; 
        z-index: 1001; 
    }
    .stFileUploader section { padding: 0 !important; min-height: unset !important; border: none !important; }
    .stFileUploader label { display: none; }
    /* Circular Plus Icon look */
    .stFileUploader div div { 
        background-color: #161b22 !important; 
        border: 2px solid #00f2ff !important; 
        border-radius: 50% !important; 
        height: 48px; 
        width: 48px; 
    }

    /* SLIM CHAT BOX: Anchored to bottom right */
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
        border-radius: 30px !important; 
        background: #161b22 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. PERSIStENT HISTORY LOGIC ---
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

# --- 3. BRAIN SETUP ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Dynamic model discovery to fix the "NotFound" error
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        active_model = next((m for m in available if "flash" in m), "gemini-1.5-flash")
        model = genai.GenerativeModel(active_model)
    except:
        st.error("Connection to AI Brain failed.")
        st.stop()
else:
    st.error("Missing API Key!")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = load_history()

# --- 4. MAIN APP ---
st.title("🧠 Vibe AI")

# Scrollable Chat Container
chat_container = st.container()
with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# --- 5. THE PLUS + CHAT BAR ---
# The '+' Button (Hidden giant uploader)
uploaded_file = st.file_uploader("+", type=["jpg", "png", "jpeg"], key="vibe_plus")

# The Chat Input
prompt = st.chat_input("Message Vibe AI...")

# --- 6. LOGIC & TOOLS ---
if uploaded_file:
    img = Image.open(uploaded_file)
    with chat_container:
        st.image(img, width=150, caption="Analyzing...")
        if st.button("🚀 Analyze Image"):
            res = model.generate_content(["What is this?", img])
            st.session_state.messages.append({"role": "assistant", "content": res.text})
            save_history(st.session_state.messages)
            st.rerun()

if prompt:
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # URL Detection for Video Downloads
    url_match = re.search(r'(https?://\S+)', prompt)
    if url_match:
        # Note: Video download tool triggered here if needed
        with chat_container:
            with st.chat_message("assistant"):
                st.write(f"Detected link: {url_match.group(1)}")
    else:
        # Standard AI Reply
        with chat_container:
            context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-5:]])
            response = model.generate_content(f"History:\n{context}\nUser: {prompt}")
            st.session_state.messages.append({"role": "assistant", "content": response.text})
    
    save_history(st.session_state.messages)
    st.rerun()
