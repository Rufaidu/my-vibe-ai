import streamlit as st
import google.generativeai as genai
from PIL import Image
import yt_dlp
import os

# --- 1. PAGE CONFIG & DARK THEME CSS ---
st.set_page_config(page_title="VibeOS Ultra", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #00f2ff; }
    [data-testid="stSidebar"] { background-color: #161b22 !important; border-right: 2px solid #00f2ff; }
    .stButton>button {
        background-color: transparent; color: #00f2ff; border: 2px solid #00f2ff;
        box-shadow: 0 0 10px #00f2ff; border-radius: 20px; font-weight: bold; width: 100%;
    }
    .stButton>button:hover { background-color: #00f2ff; color: black; box-shadow: 0 0 25px #00f2ff; }
    [data-testid="stChatMessage"] { background-color: #1c2128; border: 1px solid #30363d; border-radius: 15px; }
    h1, h2, h3 { color: #00f2ff; text-shadow: 0 0 10px #00f2ff; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SET UP THE BRAIN ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Missing API Key! Add it to Streamlit Secrets.")
    st.stop()

# --- 3. VIDEO DOWNLOAD FUNCTION ---
def download_video(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloaded_video.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# --- 4. MEMORY & SIDEBAR ---
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("📟 VibeOS Tools")
    
    # VIDEO DOWNLOADER SECTION
    st.subheader("🎥 Media Fetcher")
    video_url = st.text_input("Paste Video URL (YouTube, etc.)")
    if st.button("Get Download Link"):
        if video_url:
            with st.spinner("Fetching media..."):
                try:
                    file_path = download_video(video_url)
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label="💾 DOWNLOAD NOW",
                            data=f,
                            file_name=file_path,
                            mime="video/mp4"
                        )
                    st.success("Ready for download!")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please paste a URL first.")

    st.divider()
    
    # IMAGE ANALYSIS SECTION
    st.subheader("🔍 Visual Scanner")
    uploaded_file = st.file_uploader("Upload image", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, use_container_width=True)
        if st.button("🚀 SCAN IMAGE"):
            response = model.generate_content(["What is in this image?", img])
            st.info(response.text)

# --- 5. MAIN CHAT INTERFACE ---
st.title("🧠 VibeOS Central Brain")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Command the Brain..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
        response = model.generate_content(f"History context:\n{context}\n\nUser: {prompt}")
        st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
