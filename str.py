import streamlit as st
import docx2txt
import pdfplumber
import pandas as pd
import re
import spacy
import numpy as np
from PIL import Image
import easyocr

# Load NLP models
nlp = spacy.load("en_core_web_sm")
reader = easyocr.Reader(['en'])

# Risk keywords
risk_keywords = {
    "high": [...],  # same as your original list
    "medium": [...],
    "low": [...]
}

# --- Text Extraction Functions ---
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

# --- NLP Functions ---
def simplify_clause_spacy(text):
    doc = nlp(text)
    return " ".join([token.lemma_ for token in doc])

def detect_risk_clause_based(text):
    doc = nlp(text)
    risk_score = 0
    for sent in doc.sents:
        if any(tok.dep_ in ["neg", "advmod"] and tok.text.lower() in ["not", "never", "fail"] for tok in sent):
            risk_score += 2
        if any(tok.text.lower() in risk_keywords["high"] for tok in sent):
            risk_score += 3
        elif any(tok.text.lower() in risk_keywords["medium"] for tok in sent):
            risk_score += 2
        elif any(tok.text.lower() in risk_keywords["low"] for tok in sent):
            risk_score += 1
    if risk_score >= 4:
        return "high"
    elif risk_score >= 2:
        return "medium"
    else:
        return "low"

def keyword_in_sentence(sentence, keyword):
    keyword_lemma = nlp(keyword)[0].lemma_
    sentence_doc = nlp(sentence)
    return any(token.lemma_.lower() == keyword_lemma for token in sentence_doc)

def analyze_clauses(document_text, keyword):
    doc = nlp(document_text)
    results = []
    for sent in doc.sents:
        sent_text = sent.text.strip()
        if keyword_in_sentence(sent_text, keyword):
            risk = detect_risk_clause_based(sent_text)
            simplified = simplify_clause_spacy(sent_text)
            results.append({
                "clause": sent_text,
                "risk": risk,
                "simplified": simplified
            })
    return results

def explain_clause_spacy(text):
    doc = nlp(text)
    explanations = []
    for sent in doc.sents:
        subject = ""
        verb = ""
        obj = ""
        modifiers = []
        for token in sent:
            if token.dep_ == "nsubj":
                subject = token.text
            elif token.dep_ == "ROOT":
                verb = token.lemma_
            elif token.dep_ in ["dobj", "pobj"]:
                obj = token.text
            elif token.dep_ in ["amod", "advmod", "prep", "acl"]:
                modifiers.append(token.text)
        parts = []
        if subject:
            parts.append(f"Subject: {subject}")
        if verb:
            parts.append(f"Action: {verb}")
        if obj:
            parts.append(f"Object: {obj}")
        if modifiers:
            parts.append(f"Modifiers: {', '.join(modifiers)}")
        explanation = " | ".join(parts)
        explanations.append(explanation)
    return explanations

# --- Streamlit UI ---
st.set_page_config(page_title="Clause Risk Analyzer", layout="wide")
st.title("📄 Financial Legal Clause Risk Analyzer")

# Session state
if "document_text" not in st.session_state:
    st.session_state.document_text = ""
if "results" not in st.session_state:
    st.session_state.results = []

# Upload and extract
uploaded_file = st.file_uploader("📤 Upload a document", type=["pdf", "docx", "txt", "csv"])
if uploaded_file:
    if st.button("📥 Extract Text"):
        if uploaded_file.name.endswith(".pdf"):
            text = extract_text_pdf(uploaded_file)
            if not text.strip():
                st.warning("No text found. Trying OCR...")
                text = extract_text_scanned_pdf(uploaded_file)
        elif uploaded_file.name.endswith(".docx"):
            text = extract_text_docx(uploaded_file)
        elif uploaded_file.name.endswith(".txt"):
            text = extract_text_txt(uploaded_file)
        elif uploaded_file.name.endswith(".csv"):
            text = extract_text_csv(uploaded_file)
        else:
            st.error("Unsupported file type.")
            st.stop()
        st.session_state.document_text = text
        st.success("✅ Text extracted successfully.")

# Show extracted text
if st.session_state.document_text:
    st.text_area("📄 Extracted Document Text", value=st.session_state.document_text, height=300, disabled=True)

# Keyword input
keyword = st.text_input("🔍 Enter a keyword to analyze (e.g., indemnity, liability, termination)")

# Analyze button
if keyword and len(keyword.strip()) > 2:
    if st.button("🧠 Analyze Clauses"):
        with st.spinner("Analyzing..."):
            st.session_state.results = analyze_clauses(st.session_state.document_text, keyword)

# Show results
if st.session_state.results:
    st.markdown("### 🧠 Analysis Results")
    for i, res in enumerate(st.session_state.results, 1):
        explanation = explain_clause_spacy(res['clause'])
        st.markdown(f"**Clause {i}:**")
        st.markdown(f"- 🔍 **Original:** {res['clause']}")
        st.markdown(f"- ⚠️ **Risk Level:** `{res['risk'].capitalize()}`")
        st.markdown(f"- 🧾 **Simplified:** {res['simplified']}")
        st.markdown(f"- 📘 **Explanation:** {'; '.join(explanation)}")
        st.markdown("---")

# Reset button
if st.button("🔄 Reset All"):
    st.session_state.document_text = ""
    st.session_state.results = []
    st.experimental_rerun()
   