import os
import streamlit as st
import openai
from typing import List

st.set_page_config(page_title="Study Buddy App", layout="wide", page_icon="📚")

st.sidebar.title("⚙️ Settings")
model = st.sidebar.selectbox("Choose Model", ["gpt-3.5-turbo"], index=0)
max_tokens = st.sidebar.slider("Max Response Tokens", 150, 1500, 600, 50)

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_KEY:
    openai.api_key = OPENAI_KEY

def query_openai(messages: List[dict], model: str = "gpt-3.5-turbo", max_tokens: int = 500):
    try:
        resp = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"OpenAI request failed: {e}")
        return ""

st.markdown("<h1 style='text-align: center; color: #4B0082;'>📚 AI-Powered Study Buddy</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size:16px;'>Learn, Summarize, Quiz, and Memorize smarter with AI</p>", unsafe_allow_html=True)

tabs = st.tabs(["Explain a Topic", "Summarize Notes", "Generate Quiz", "Create Flashcards"])

with tabs[0]:
    topic = st.text_input("Enter Topic:", value="Binary Search")
    level = st.selectbox("Explain for:", ["High school", "Undergraduate", "Graduate"], index=0)
    length = st.selectbox("Length:", ["Short", "Medium", "Step-by-step"])
    if st.button("Explain Topic"):
        prompt = f"Explain the topic {topic} for {level}. "
        if length == "Short": prompt += "Keep it concise."
        elif length == "Medium": prompt += "Give clear explanation with example."
        else: prompt += "Step-by-step with example."
        messages = [{"role": "system", "content": "You are a helpful tutor."},
                    {"role": "user", "content": prompt}]
        with st.spinner("Generating explanation..."):
            answer = query_openai(messages, model=model, max_tokens=max_tokens)
        st.success("Explanation Ready:")
        st.markdown(f"{answer}")

with tabs[1]:
    context_text = st.text_area("Paste your notes:", height=300)
    tone = st.selectbox("Summary Tone:", ["Neutral", "Simple", "Exam-focused"], index=1)
    if st.button("Summarize Notes") and context_text.strip():
        prompt = f"Summarize the following text with tone {tone}:\n{context_text}"
        messages = [{"role": "system", "content": "You summarize study notes."},
                    {"role": "user", "content": prompt}]
        with st.spinner("Summarizing notes..."):
            out = query_openai(messages, model=model, max_tokens=max_tokens)
        st.success("Summary Ready:")
        st.markdown(f"{out}")

with tabs[2]:
    source_choice = st.radio("Source for Quiz:", ["Topic", "Text"], index=0, horizontal=True)
    num_q = st.slider("Number of questions", 1, 20, 5)
    difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=1)
    if source_choice == "Topic": topic = st.text_input("Quiz Topic:", value="Operating Systems")
    else: context_text = st.text_area("Paste text for quiz:", height=300)
    if st.button("Generate Quiz"):
        source = topic if source_choice == "Topic" else context_text
        if source.strip():
            prompt = f"Create {num_q} MCQs with answers and short explanations from: {source}"
            messages = [{"role": "system", "content": "You create quizzes."},
                        {"role": "user", "content": prompt}]
            with st.spinner("Generating quiz..."):
                out = query_openai(messages, model=model, max_tokens=max_tokens+200)
            st.success("Quiz Ready:")
            st.text(out)

with tabs[3]:
    source_choice = st.radio("Source for Flashcards:", ["Topic", "Text"], index=0, horizontal=True)
    num_cards = st.slider("Number of flashcards", 1, 50, 10)
    if source_choice == "Topic": topic = st.text_input("Flashcards Topic:", value="Networking fundamentals")
    else: context_text = st.text_area("Paste text for flashcards:", height=300)
    if st.button("Generate Flashcards"):
        source = topic if source_choice == "Topic" else context_text
        if source.strip():
            prompt = f"Create {num_cards} flashcards (Q/A) from: {source}"
            messages = [{"role": "system", "content": "You create flashcards."},
                        {"role": "user", "content": prompt}]
            with st.spinner("Generating flashcards..."):
                out = query_openai(messages, model=model, max_tokens=max_tokens+200)
            st.success("Flashcards Ready:")
            st.text(out)
