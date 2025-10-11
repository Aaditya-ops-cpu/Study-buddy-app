import os
import json
import requests
import streamlit as st
from io import StringIO
from typing import Optional
try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None


GEMINI_MODEL = "gemini-2.5-flash"  # change model string if you want different model
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
API_KEY_ENV = "GEMINI_API_KEY"

def get_api_key() -> Optional[str]:
    return os.environ.get(API_KEY_ENV)

def call_gemini(prompt: str, temperature: float = 0.2, max_output_tokens: int = 800) -> str:
    """
    Simple POST to Gemini REST generateContent endpoint.
    Uses x-goog-api-key header per Gemini docs.
    """
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError(f"Gemini API key not found. Please set environment variable {API_KEY_ENV}")

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ],
        "temperature": temperature,
        "max_output_tokens": max_output_tokens
    }

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }

    resp = requests.post(GEMINI_ENDPOINT, headers=headers, json=payload, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"Gemini API request failed ({resp.status_code}): {resp.text}")

    data = resp.json()
    def find_first_text(d):
        if isinstance(d, dict):
            for k, v in d.items():
                if k == "text" and isinstance(v, str):
                    return v
                found = find_first_text(v)
                if found:
                    return found
        elif isinstance(d, list):
            for item in d:
                found = find_first_text(item)
                if found:
                    return found
        return None

    text = find_first_text(data)
    if text:
        return text.strip()

    return json.dumps(data, indent=2)

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
    .stApp {
        background-color: honeydew;
        color: midnightblue;
    }

    .card {
        background-color: white;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.06);
        border: 1px solid lightgray;
    }

    .header {
        background-color: lightblue;
        color: navy;
        padding: 18px;
        border-radius: 12px;
    }

    .small-muted {
        color: gray;
        font-size: 12px;
    }

    button[data-baseweb="button"] {
        border-radius: 10px;
        padding: 10px 18px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="header"><h1 style="margin:6px 0;">AI Study Buddy</h1>'
            '<div style="font-size:14px;color:darkslategray">Explain topics • Summarize notes • Create quizzes & flashcards</div></div>',
            unsafe_allow_html=True)

api_key = get_api_key()
if not api_key:
    st.warning(f"Gemini API key not found. Set environment variable `{API_KEY_ENV}` before running. See instructions below.")
    with st.expander("How to set GEMINI_API_KEY (quick)"):
        st.markdown("""
        1. Create an API key in Google AI Studio / Gemini settings (or your Gemini provider console).  
        2. Locally (macOS / Linux): `export GEMINI_API_KEY='YOUR_KEY'`  
           On Windows (PowerShell): `$env:GEMINI_API_KEY='YOUR_KEY'`  
        3. In deployment (Streamlit Cloud / VPS), set an environment variable named `GEMINI_API_KEY`.  
        The Gemini REST endpoint accepts the key in header `x-goog-api-key`. :contentReference[oaicite:1]{index=1}
        """, unsafe_allow_html=True)

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Input")
    mode = st.selectbox("Choose action", ["Explain topic", "Summarize notes", "Generate quiz & flashcards"])
    st.write("")  # spacing

    topic = st.text_input("Enter topic / question", placeholder="e.g. 'How does a CPU work?' or 'Integration by parts'")

    st.markdown("**Attach notes (optional)** — paste text or upload a file (.txt or .pdf).")
    pasted = st.text_area("Or paste your notes here", height=150)

    uploaded_file = st.file_uploader("Upload text or PDF file (optional)", type=["txt", "pdf", "md"])

    st.markdown("---")
    st.subheader("Options")
    simple_level = st.selectbox("Explain level", ["Beginner (simple)", "Intermediate", "Advanced"], index=0)
    num_questions = st.slider("Number of quiz questions", 1, 10, 5)
    generate_answers = st.checkbox("Include answers with quiz", value=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    run_btn = st.button("Generate")

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Result")
    result_area = st.empty()
    st.markdown("</div>", unsafe_allow_html=True)

with st.container():
    st.markdown("""
    <div style="margin-top:12px;">
    <span class="small-muted">Tip: For best results, include a short context (2-5 sentences) in the notes box or the topic field. The app sends your prompt to the Gemini API — keep sensitive info out.</span>
    </div>
    """, unsafe_allow_html=True)

if run_btn:
    # build combined notes text
    notes_text = ""
    if pasted:
        notes_text += pasted + "\n\n"

    if uploaded_file:
        fname = uploaded_file.name.lower()
        if fname.endswith(".txt") or fname.endswith(".md"):
            try:
                raw = uploaded_file.read().decode("utf-8")
            except Exception:
                raw = uploaded_file.getvalue().decode("utf-8", errors="ignore")
            notes_text += raw + "\n\n"
        elif fname.endswith(".pdf"):
            if PdfReader is None:
                st.error("PDF support requires PyPDF2. Install PyPDF2 in requirements.")
            else:
                try:
                    text = extract_text_from_pdf(uploaded_file)
                    notes_text += text + "\n\n"
                except Exception as e:
                    st.error(f"Failed to extract text from PDF: {e}")
    if mode == "Explain topic":
        level_map = {
            "Beginner (simple)": "Explain the following topic in simple terms using easy-to-understand language and analogies. Include a short example and 3-step summary.",
            "Intermediate": "Explain the topic with some mathematical/formal detail and a concise example. Include a 3-step summary.",
            "Advanced": "Provide an advanced explanation with technical details, edge cases, and further reading suggestions."
        }
        instruction = level_map.get(simple_level, "")
        prompt = f"{instruction}\n\nTopic: {topic}\n\nNotes and context: {notes_text}\n\nFormat: Use headings 'Explanation', 'Example', '3-step summary'. Keep answer clear and teachable."
    elif mode == "Summarize notes":
        prompt = f"Summarize the following study notes into a clean study guide of about 200-350 words. Use bullet-like numbered steps (but not bullet points — use short paragraphs), highlight key formulas or lines, and provide 3 follow-up practice prompts the student can try. Notes:\n\n{topic}\n\n{notes_text}"
    else:  # Generate quiz & flashcards
        # Ensure there is context
        context = notes_text if notes_text.strip() else topic
        prompt = (
            f"Create a study quiz and flashcards from the following topic/context. "
            f"Produce {num_questions} multiple-choice questions (4 options each) with one correct answer and a brief explanation (1-2 sentences). "
            f"Then produce flashcards: for each question produce 'Term: <term>' and 'Definition: <definition>'. "
            f"If requested, include answers. Context:\n\n{context}\n\nFormat the response clearly with headings: QUIZ, ANSWERS (if selected), FLASHCARDS."
        )

    with st.spinner("Contacting Gemini model and generating content..."):
        try:
            output_text = call_gemini(prompt)
            # Simple post-processing: if Gemini returns JSON or lists, just show text
            result_area.code(output_text, language="text")
        except Exception as e:
            st.error(f"Generation failed: {e}")
st.markdown(
    """
    <div style="margin-top:18px; padding:12px; border-radius:8px; background-color: white;">
    <strong>About the Gemini API usage:</strong> This app uses the Gemini REST `generateContent` endpoint and passes your API key in the `x-goog-api-key` header as shown in the official docs. Make sure your key has permissions and quota. :contentReference[oaicite:2]{index=2}
    </div>
    """,
    unsafe_allow_html=True
)
