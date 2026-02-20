import streamlit as st
import requests
import uuid

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Vibe AI", page_icon="🧠", layout="wide")

# ================= SESSION STATE =================
if "chats" not in st.session_state:
    st.session_state.chats = {}

if "current_chat" not in st.session_state:
    new_id = str(uuid.uuid4())
    st.session_state.chats[new_id] = {"title": "New Chat", "messages": []}
    st.session_state.current_chat = new_id

if "is_generating" not in st.session_state:
    st.session_state.is_generating = False

current_chat = st.session_state.chats[st.session_state.current_chat]

# ================= HUGGING FACE SETTINGS =================
HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"
HF_TOKEN = st.secrets["HF_API_KEY"]
API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

# ================= FUNCTIONS =================
def query_hf(prompt):
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 300}
    }
    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
        data = response.json()
        return data[0]["generated_text"]
    except:
        return "⚠️ Model is busy or something went wrong. Try again."

# ================= CUSTOM UI =================
st.markdown("""
<style>
.stApp { background-color: #0f172a; color: white; }
[data-testid="stSidebar"] { background-color: #111827; }

.chat-bubble-user {
    background: #1e293b;
    padding: 14px;
    border-radius: 14px;
    margin-bottom: 10px;
    text-align: right;
}

.chat-bubble-bot {
    background: #111827;
    padding: 14px;
    border-radius: 14px;
    margin-bottom: 10px;
    text-align: left;
}

.center-title {
    text-align: center;
    margin-top: 20vh;
    font-size: 42px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ================= SIDEBAR =================
with st.sidebar:
    st.title("🧠 Vibe AI")

    if st.button("➕ New Chat"):
        new_id = str(uuid.uuid4())
        st.session_state.chats[new_id] = {"title": "New Chat", "messages": []}
        st.session_state.current_chat = new_id
        st.rerun()

    st.markdown("### Chats")
    for chat_id, chat_data in st.session_state.chats.items():
        if st.button(chat_data["title"], key=chat_id):
            st.session_state.current_chat = chat_id
            st.rerun()

# ================= LANDING =================
if not current_chat["messages"]:
    st.markdown("<div class='center-title'>🧠 Vibe AI</div>", unsafe_allow_html=True)
    st.markdown("<center>Your intelligent AI companion</center>", unsafe_allow_html=True)

# ================= DISPLAY CHAT =================
for msg in current_chat["messages"]:
    if msg["role"] == "user":
        st.markdown(f"<div class='chat-bubble-user'>{msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='chat-bubble-bot'>{msg['content']}</div>", unsafe_allow_html=True)

# ================= CHAT INPUT =================
prompt = st.chat_input(
    "Message Vibe AI...",
    disabled=st.session_state.is_generating
)

# ================= MEDIA UPLOAD (MOVE BELOW INPUT) =================
uploaded_file = st.file_uploader("Upload a file (image, PDF, TXT)", type=["png","jpg","jpeg","pdf","txt"])

if uploaded_file:
    if uploaded_file.type.startswith("image/"):
        st.image(uploaded_file, caption=f"Uploaded Image: {uploaded_file.name}", use_column_width=True)
        st.session_state.last_uploaded_text = f"User uploaded an image named {uploaded_file.name}"
    elif uploaded_file.type == "application/pdf":
        import PyPDF2
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        pdf_text = ""
        for page in pdf_reader.pages:
            pdf_text += page.extract_text() + "\n"
        st.session_state.last_uploaded_text = f"User uploaded PDF '{uploaded_file.name}' with content:\n{pdf_text}"
    elif uploaded_file.type in ["text/plain"]:
        text = uploaded_file.read().decode("utf-8")
        st.session_state.last_uploaded_text = f"User uploaded text file '{uploaded_file.name}':\n{text}"
    else:
        st.session_state.last_uploaded_text = None

# ================= GENERATE RESPONSE =================
if prompt and not st.session_state.is_generating:

    st.session_state.is_generating = True

    # Save user message
    current_chat["messages"].append({
        "role": "user",
        "content": prompt
    })

    if current_chat["title"] == "New Chat":
        current_chat["title"] = prompt[:30]

    # Build conversation context (last 5 messages + uploaded file text)
    conversation = ""
    for msg in current_chat["messages"][-5:]:
        role = "User" if msg["role"] == "user" else "Assistant"
        conversation += f"{role}: {msg['content']}\n"

    if "last_uploaded_text" in st.session_state and st.session_state.last_uploaded_text:
        conversation += st.session_state.last_uploaded_text + "\n"

    # Show thinking placeholder
    placeholder = st.empty()
    placeholder.markdown(
        "<div class='chat-bubble-bot'><em>🧠 Vibe AI is thinking...</em></div>",
        unsafe_allow_html=True
    )

    # Query Hugging Face model
    with st.spinner("🧠 Generating response..."):
        bot_reply = query_hf(conversation)

    # Display bot response
    placeholder.markdown(
        f"<div class='chat-bubble-bot'>{bot_reply}</div>",
        unsafe_allow_html=True
    )

    # Save bot message
    current_chat["messages"].append({
        "role": "assistant",
        "content": bot_reply
    })

    st.session_state.is_generating = False

    # Auto scroll
    st.markdown(
        """
        <script>
        window.scrollTo(0, document.body.scrollHeight);
        </script>
        """,
        unsafe_allow_html=True
    )

    st.rerun()
