import os
import json
import requests
import streamlit as st
try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
API_KEY_ENV = "GEMINI_API_KEY"

def get_api_key():
    return os.environ.get(API_KEY_ENV)

def call_gemini(prompt: str, temperature: float = 0.4, max_output_tokens: int = 1024) -> str:
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError(f"Gemini API key not found. Please set environment variable {API_KEY_ENV}")

    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_output_tokens,
            "topP": 0.9
        }
    }

    headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}
    resp = requests.post(GEMINI_ENDPOINT, headers=headers, json=payload, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"Gemini API request failed ({resp.status_code}): {resp.text}")

    data = resp.json()
    try:
        parts = data["candidates"][0]["content"].get("parts", [])
        text_blocks = [p.get("text", "") for p in parts if "text" in p]
        text = "\n".join(text_blocks).strip()
        if text:
            return text
    except Exception:
        pass
    if data.get("candidates", [{}])[0].get("finishReason") == "MAX_TOKENS":
        return "⚠️ Gemini stopped early due to token limit (MAX_TOKENS). Try asking a shorter question."
    return f"(No text found)\n\nRaw response:\n{json.dumps(data, indent=2)}"

def extract_text_from_pdf(file_bytes) -> str:
    if PdfReader is None:
        raise RuntimeError("PyPDF2 is not available. Install PyPDF2 to enable PDF uploads.")
    reader = PdfReader(file_bytes)
    texts = []
    for page in reader.pages:
        try:
            texts.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(texts)

st.set_page_config(page_title="AI Study Buddy", page_icon="🎓", layout="wide")
st.markdown(
    """
    <style>
    .stApp { background-color: honeydew; color: midnightblue; }
    .card { background-color: white; border-radius: 12px; padding: 18px;
            box-shadow: 0 6px 18px rgba(0,0,0,0.06); border: 1px solid lightgray; }
    .header { background-color: lightblue; color: navy; padding: 18px; border-radius: 12px; }
    .small-muted { color: gray; font-size: 12px; }
    button[data-baseweb="button"] { border-radius: 10px; padding: 10px 18px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="header"><h1 style="margin:6px 0;">AI Study Buddy</h1>'
    '<div style="font-size:14px;color:darkslategray">'
    'Explain topics • Summarize notes • Create quizzes & flashcards'
    '</div></div>',
    unsafe_allow_html=True,
)

api_key = get_api_key()
if not api_key:
    st.warning(f"Gemini API key not found. Set environment variable `{API_KEY_ENV}` before running.")
    with st.expander("How to set GEMINI_API_KEY"):
        st.markdown("""
        1. Create an API key in Google AI Studio / Gemini settings.  
        2. macOS/Linux → `export GEMINI_API_KEY='YOUR_KEY'`  
           Windows (PowerShell) → `$env:GEMINI_API_KEY='YOUR_KEY'`  
        3. In Streamlit Cloud → set environment variable `GEMINI_API_KEY`.
        """)

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Input")
    mode = st.selectbox("Choose action", ["Explain topic", "Summarize notes", "Generate quiz & flashcards"])
    topic = st.text_input("Enter topic / question", placeholder="e.g. What is CPU?")
    st.markdown("**Attach notes (optional)** — paste text or upload a file (.txt or .pdf).")
    pasted = st.text_area("Or paste notes here", height=150)
    uploaded_file = st.file_uploader("Upload text or PDF file (optional)", type=["txt", "pdf", "md"])
    st.markdown("---")
    st.subheader("Options")
    simple_level = st.selectbox("Explain level", ["Beginner (simple)", "Intermediate", "Advanced"], index=0)
    num_questions = st.slider("Number of quiz questions", 1, 10, 5)
    generate_answers = st.checkbox("Include answers", value=True)
    st.markdown("</div>", unsafe_allow_html=True)
    run_btn = st.button("Generate")

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Result")
    result_area = st.empty()
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    "<div style='margin-top:12px;'><span class='small-muted'>Tip: Include some context for better accuracy.</span></div>",
    unsafe_allow_html=True,
)

if run_btn:
    notes_text = pasted or ""
    if uploaded_file:
        fname = uploaded_file.name.lower()
        if fname.endswith(".txt") or fname.endswith(".md"):
            try:
                notes_text += uploaded_file.read().decode("utf-8")
            except Exception:
                notes_text += uploaded_file.getvalue().decode("utf-8", errors="ignore")
        elif fname.endswith(".pdf"):
            notes_text += extract_text_from_pdf(uploaded_file)
    if mode == "Explain topic":
        level_map = {
            "Beginner (simple)": "Explain simply with analogies and short examples.",
            "Intermediate": "Explain with moderate detail and examples.",
            "Advanced": "Explain with technical detail and edge cases."
        }
        instruction = level_map[simple_level]
        prompt = f"{instruction}\n\nTopic: {topic}\n\nNotes:\n{notes_text}"
    elif mode == "Summarize notes":
        prompt = f"Summarize the following notes clearly and concisely with 3 key takeaways:\n\n{topic}\n{notes_text}"
    else:
        context = notes_text if notes_text.strip() else topic
        prompt = (
            f"Create a study quiz and flashcards from this content:\n\n{context}\n\n"
            f"Generate {num_questions} multiple-choice questions with answers and explanations. "
            f"Then produce flashcards (Term: ..., Definition: ...)."
        )
    with st.spinner("Generating with Gemini..."):
        try:
            output_text = call_gemini(prompt)
            result_area.markdown(f"```text\n{output_text}\n```")
        except Exception as e:
            st.error(f"Error: {e}")

st.markdown(
    "<div style='margin-top:18px; padding:12px; border-radius:8px; background-color:white;'>"
    "<strong>Note:</strong> This app uses Gemini REST API via x-goog-api-key header. "
    "Ensure your API key is valid and quota available."
    "</div>",
    unsafe_allow_html=True,
)
