import streamlit as st
import requests
import uuid
import PyPDF2

st.set_page_config(page_title="Vibe AI", page_icon="🧠", layout="wide")

# ====== SESSION STATE ======
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "current_chat" not in st.session_state:
    new_id = str(uuid.uuid4())
    st.session_state.chats[new_id] = {"title": "New Chat", "messages": []}
    st.session_state.current_chat = new_id
if "is_generating" not in st.session_state:
    st.session_state.is_generating = False
if "plus_click" not in st.session_state:
    st.session_state.plus_click = False

current_chat = st.session_state.chats[st.session_state.current_chat]

# ====== HUGGING FACE SETTINGS ======
HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"
HF_TOKEN = st.secrets["HF_API_KEY"]
API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

def query_hf(prompt):
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": 300}}
    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
        data = response.json()
        return data[0]["generated_text"]
    except:
        return "⚠️ Model busy or something went wrong."

# ====== DISPLAY CHAT ======
for msg in current_chat["messages"]:
    if msg["role"] == "user":
        st.markdown(f"<div style='background:#1e293b;padding:14px;border-radius:14px;margin-bottom:10px;text-align:right'>{msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='background:#111827;padding:14px;border-radius:14px;margin-bottom:10px;text-align:left'>{msg['content']}</div>", unsafe_allow_html=True)

# ====== CHAT INPUT WITH PLUS BUTTON ======
col_plus, col_input, col_send = st.columns([0.5,4,1])

with col_plus:
    if st.button("➕"):
        st.session_state.plus_click = True

# Hidden file uploader triggered by plus button
if st.session_state.plus_click:
    uploaded_file = st.file_uploader("Select file", type=["png","jpg","jpeg","pdf","txt"], key="hidden_uploader")
    if uploaded_file:
        if uploaded_file.type.startswith("image/"):
            st.session_state.last_uploaded_text = f"User uploaded an image named {uploaded_file.name}"
        elif uploaded_file.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            pdf_text = "".join([page.extract_text() for page in pdf_reader.pages])
            st.session_state.last_uploaded_text = f"User uploaded PDF '{uploaded_file.name}' with content:\n{pdf_text}"
        elif uploaded_file.type in ["text/plain"]:
            text = uploaded_file.read().decode("utf-8")
            st.session_state.last_uploaded_text = f"User uploaded text file '{uploaded_file.name}':\n{text}"
        st.session_state.plus_click = False

with col_input:
    prompt = st.text_input("Message Vibe AI...", disabled=st.session_state.is_generating, key="chat_input")

with col_send:
    send_clicked = st.button("Send")

# ====== GENERATE RESPONSE ======
if send_clicked and prompt and not st.session_state.is_generating:
    st.session_state.is_generating = True
    current_chat["messages"].append({"role":"user","content":prompt})
    if current_chat["title"]=="New Chat": current_chat["title"] = prompt[:30]

    conversation = ""
    for msg in current_chat["messages"][-5:]:
        role = "User" if msg["role"]=="user" else "Assistant"
        conversation += f"{role}: {msg['content']}\n"
    if "last_uploaded_text" in st.session_state and st.session_state.last_uploaded_text:
        conversation += st.session_state.last_uploaded_text + "\n"

    placeholder = st.empty()
    placeholder.markdown("<div style='background:#111827;padding:14px;border-radius:14px;margin-bottom:10px;text-align:left'><em>🧠 Vibe AI is thinking...</em></div>", unsafe_allow_html=True)

    with st.spinner("🧠 Generating response..."):
        bot_reply = query_hf(conversation)

    placeholder.markdown(f"<div style='background:#111827;padding:14px;border-radius:14px;margin-bottom:10px;text-align:left'>{bot_reply}</div>", unsafe_allow_html=True)
    current_chat["messages"].append({"role":"assistant","content":bot_reply})
    st.session_state.is_generating = False
    st.experimental_rerun()
