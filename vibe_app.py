import streamlit as st
import google.generativeai as genai
from PIL import Image
import yt_dlp
import os

# --- 1. PAGE CONFIG & NEON CSS ---
st.set_page_config(page_title="VibeOS Ultra", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    /* Dark Theme Foundation */
    .stApp { background-color: #0e1117; color: #00f2ff; }
    
    /* Neon Sidebar */
    [data-testid="stSidebar"] {
        background-color: #161b22 !important;
        border-right: 2px solid #00f2ff;
    }

    /* Glowing Buttons */
    .stButton>button {
        background-color: transparent; color: #00f2ff;
        border: 2px solid #00f2ff; box-shadow: 0 0 10px #00f2ff;
        border-radius: 20px; font-weight: bold; width: 100%;
    }
    .stButton>button:hover {
        background-color: #00f2ff; color: black; box-shadow: 0 0 25px #00f2ff;
    }

    /* Chat Styling */
    [data-testid="stChatMessage"] {
        background-color: #1c2128; border: 1px solid #30363d; border-radius: 15px;
    }
    
    h1, h2, h3 { color: #00f2ff; text-shadow: 0 0 10px #00f2ff; }
    </style>
""", unsafe_allow_html=True)

# --- 2. THE BRAIN (API SECRETS) ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Try the most stable version first
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
    except:
        # Fallback if 'flash-latest' isn't in your region yet
        model = genai.GenerativeModel('gemini-pro')
else:
    st.error("Missing API Key! Please add it to your Streamlit Secrets.")
    st.stop()

# --- 3. VIDEO DOWNLOADER LOGIC ---
def download_media(url):
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }
    
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
st.title("🧠 VibeOS Brain")

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
