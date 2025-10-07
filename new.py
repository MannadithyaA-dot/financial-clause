import streamlit as st
import docx2txt
import pdfplumber
import pandas as pd
import numpy as np
import spacy
import easyocr
from google import genai

# ✅ Initialize Gemini Client
client = genai.Client(api_key="AIzaSyBNT3byK-prnOAfwcsqSD_6eKOfNJsSafE")

# ✅ Load spaCy NLP model
try:
    nlp = spacy.load("en_core_web_sm")
except:
    nlp = spacy.blank("en")  # fallback if model isn't available

# ✅ Initialize EasyOCR reader
reader = easyocr.Reader(['en'])

# --- Text Extraction ---
def extract_text_docx(file):
    return docx2txt.process(file)

def extract_text_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def extract_text_scanned_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            image = page.to_image(resolution=300).original
            image_np = np.array(image)
            result = reader.readtext(image_np)
            text += "\n".join([item[1] for item in result]) + "\n"
    return text

def extract_text_txt(file):
    return file.read().decode("utf-8")

def extract_text_csv(file):
    df = pd.read_csv(file)
    clauses = []
    for col in df.columns:
        clauses.extend(df[col].dropna().astype(str).tolist())
    return "\n".join(clauses)

# --- Gemini AI Clause Analysis ---
def analyze_clause_with_gemini(clause):
    prompt = f"""
    Analyze the following legal clause:
    Clause: "{clause}"

    1. Classify its risk level (high, medium, low).
    2. Simplify the clause.
    3. Explain the clause in terms of subject, action, object, and modifiers.

    Respond in structured JSON format:
    {{
        "risk": "...",
        "simplified": "...",
        "explanation": "..."
    }}
    """
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        return eval(response.text)
    except Exception as e:
        print("Gemini error:", e)
        return {
            "risk": "unknown",
            "simplified": "Could not simplify",
            "explanation": "Could not explain"
        }

# --- Streamlit UI ---
st.set_page_config(page_title="Dynamic Clause Risk Analyzer", layout="wide")
st.title("📄 Dynamic Financial Legal Clause Risk Analyzer (Powered by Gemini AI)")

uploaded_file = st.file_uploader("📤 Upload a document", type=["pdf", "docx", "txt", "csv"])
document_text = ""

if uploaded_file:
    if uploaded_file.name.endswith(".pdf"):
        document_text = extract_text_pdf(uploaded_file)
        if not document_text.strip():
            st.warning("No text found. Trying OCR...")
            document_text = extract_text_scanned_pdf(uploaded_file)
    elif uploaded_file.name.endswith(".docx"):
        document_text = extract_text_docx(uploaded_file)
    elif uploaded_file.name.endswith(".txt"):
        document_text = extract_text_txt(uploaded_file)
    elif uploaded_file.name.endswith(".csv"):
        document_text = extract_text_csv(uploaded_file)
    else:
        st.error("Unsupported file type.")
        st.stop()

    st.success("✅ Text extracted successfully.")
    st.text_area("📄 Extracted Document Text", value=document_text, height=300, disabled=True)

    keyword = st.text_input("🔍 Enter a keyword to analyze (optional)")
    if st.button("🧠 Analyze Clauses"):
        with st.spinner("Analyzing with Gemini AI..."):
            doc = nlp(document_text)
            results = []
            for sent in doc.sents:
                sentence_text = sent.text.strip()
                if (
                    len(sentence_text) > 30 and
                    any(tok.pos_ == "VERB" for tok in nlp(sentence_text)) and
                    (not keyword or keyword.lower() in sentence_text.lower())
                ):
                    result = analyze_clause_with_gemini(sentence_text)
                    results.append({
                        "clause": sentence_text,
                        **result
                    })

        if results:
            st.markdown("### 🧠 Analysis Results")
            for i, res in enumerate(results, 1):
                st.markdown(f"**Clause {i}:**")
                st.markdown(f"- 🔍 **Original:** {res['clause']}")
                st.markdown(f"- ⚠️ **Risk Level:** `{res['risk'].capitalize()}`")
                st.markdown(f"- 🧾 **Simplified:** {res['simplified']}")
                st.markdown(f"- 📘 **Explanation:** {res['explanation']}")
                st.markdown("---")
        else:
            st.warning("No relevant clauses found.")