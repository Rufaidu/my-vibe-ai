import streamlit as st
import google.generativeai as genai
import yt_dlp
import os

# --- 1. CONFIG & PREMIUM DARK VIBE ---
st.set_page_config(page_title="VibeOS", page_icon="🧠", layout="centered")

st.markdown("""
    <style>
    /* Main Background and Font */
    .stApp {
        background: radial-gradient(circle at top, #0d1b2a 0%, #000000 100%);
        color: #e0e1dd;
        font-family: 'Inter', sans-serif;
    }

    /* Input Box Styling */
    .stTextInput input, .stChatInput textarea {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid #415a77 !important;
        border-radius: 12px !important;
        color: #00d4ff !important;
    }

    /* Buttons with a Neon Glow */
    .stButton button {
        background: linear-gradient(135deg, #00b4d8 0%, #0077b6 100%);
        border: none;
        border-radius: 10px;
        color: white;
        font-weight: 700;
        transition: all 0.3s ease;
        box-shadow: 0px 4px 15px rgba(0, 180, 216, 0.3);
    }

    .stButton button:hover {
        box-shadow: 0px 0px 20px rgba(0, 212, 255, 0.6);
        transform: translateY(-2px);
    }

    /* Chat Bubbles */
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.03);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 10px;
        margin-bottom: 10px;
    }

    /* Custom Header */
    h1 {
        color: #00d4ff;
        text-shadow: 0px 0px 10px rgba(0, 212, 255, 0.5);
        font-weight: 800;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #0b0d17;
        border-right: 1px solid #1b263b;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SET UP THE BRAIN (MANUAL OVERRIDE) ---
# Change it back to this in vibe_app.py:
api_key = st.secrets["GOOGLE_API_KEY"]

try:
    genai.configure(api_key=api_key)
    # Using 'gemini-1.5-flash' as it's the most stable during outages
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.warning("Google servers are currently unstable. Retrying connection...")

# --- 3. THE FETCH ENGINE ---
def download_media(url):
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        # THIS IS THE FIX FOR 403 FORBIDDEN:
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# --- 4. INTERFACE ---
st.title("🧠 VibeOS")
st.caption("AI Chat + Universal Media Fetcher")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# User Interaction
if prompt := st.chat_input("Say something or paste a link..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # ACTION: If a link is detected
    if "http" in prompt:
        with st.chat_message("assistant"):
            st.write("📡 **Link detected. Accessing datastreams...**")
            try:
                # Find the URL in the text
                url = [w for w in prompt.split() if "http" in w][0]
                file_path = download_media(url)
                
                with open(file_path, "rb") as f:
                    st.success(f"✅ Vibe Captured: {os.path.basename(file_path)}")
                    st.download_button(
                        label="💾 SAVE TO DEVICE",
                        data=f,
                        file_name=os.path.basename(file_path),
                        mime="application/octet-stream"
                    )
            except Exception as e:
                st.error(f"Download failed: {str(e)}")

    # ACTION: Chat response
    elif api_key:
        with st.chat_message("assistant"):
            try:
                response = model.generate_content(prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error("The brain is tired. Check your API key or limits.")
