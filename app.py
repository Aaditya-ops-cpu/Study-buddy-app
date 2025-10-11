import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="📚 Study Buddy - Gemini AI Tutor", layout="wide")

st.markdown(
    """
    <style>
    body {
        background-color: whitesmoke;
    }
    .title {
        font-size: 40px;
        text-align: center;
        color: white;
        background: linear-gradient(90deg, deepskyblue, dodgerblue);
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 30px;
    }
    .chat-bubble-user {
        background-color: steelblue;
        color: white;
        border-radius: 12px;
        padding: 10px 15px;
        margin: 8px 0;
        text-align: right;
        max-width: 80%;
        margin-left: auto;
    }
    .chat-bubble-ai {
        background-color: aliceblue;
        color: black;
        border-radius: 12px;
        padding: 10px 15px;
        margin: 8px 0;
        text-align: left;
        max-width: 80%;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="title">🤖 Study Buddy - Gemini AI Tutor</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Enter your Google Gemini API Key", type="password")
    st.markdown("---")
    st.caption("💡 Get your key from [Google AI Studio](https://aistudio.google.com/app/apikey)")

if not api_key:
    st.info("Please enter your Google Gemini API key in the sidebar to start.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.markdown("💬 Chat with your AI Study Partner")

user_input = st.chat_input("Ask your question here...")

if user_input:
    st.session_state.chat_history.append({"role": "user", "text": user_input})
    with st.spinner("Thinking..."):
        response = model.generate_content(user_input)
        st.session_state.chat_history.append({"role": "ai", "text": response.text})

for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        st.markdown(f"<div class='chat-bubble-user'>{msg['text']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='chat-bubble-ai'>{msg['text']}</div>", unsafe_allow_html=True)
