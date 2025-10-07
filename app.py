import streamlit as st
import docx2txt
import pdfplumber
import pandas as pd
import re
import spacy
from PIL import Image
import easyocr  # EasyOCR for local OCR


# Load spaCy model
nlp = spacy.load("en_core_web_sm")
reader = easyocr.Reader(['en'])  # Initialize EasyOCR reader

# Risk keywords
risk_keywords = {
    "high": [
        "termination", "breach", "damages", "lawsuit", "insolvency", "bankruptcy",
        "regulatory violations", "change of control", "force majeure", "negligence", "wrongful acts",
        "fraud","penalties","liability cap breach","intellectual property" ,"infringement","non-compete",
        "non-solicitation","governing law conflicts","irrevocable license","covenant not to sue","waiver of rights","class action waiver"
    ],
    "medium": [
        "indemnification", "limitation of liability", "dispute resolution", "confidentiality",
        "non-disclosure", "obligation", "compliance", "remedies", "arbitration", "mediation",
        "audit rights","assignment clauses","return of confidential information","exceptions clauses",
        "restricted use","applicable law","jurisdiction","third-party rights","data protection","GDPR compliance"

    ],
    "low": [
        "payment terms", "notice period", "duration", "renewal", "exit fees",
        "interest on late payment", "negotiation", "service level agreement","effective date",
        "governing language","contract structure","headers/subheaders","document type","aliases/roles of parties"
    ]
}

# Extract text from DOCX
def extract_text_docx(file):
    return docx2txt.process(file)

# Extract text from PDF (text-based)
def extract_text_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

# Extract text from scanned PDF using EasyOCR
import numpy as np

def extract_text_scanned_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            image = page.to_image(resolution=300).original
            image_np = np.array(image)  # Convert PIL image to NumPy array
            result = reader.readtext(image_np)
            text += "\n".join([item[1] for item in result]) + "\n"
    return text

# Extract text from TXT
def extract_text_txt(file):
    return file.read().decode("utf-8")

# Extract text from CSV
def extract_text_csv(file):
    df = pd.read_csv(file)
    clauses = []
    for col in df.columns:
        clauses.extend(df[col].dropna().astype(str).tolist())
    return "\n".join(clauses)

# Simplify clause using spaCy lemmatization
def simplify_clause_spacy(text):
    doc = nlp(text)
    return " ".join([token.lemma_ for token in doc])

# Detect risk level using keyword matching
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

# Analyze clauses

def analyze_clauses(document_text, keyword):
    sentences = re.split(r'(?<=[.!?])\s+', document_text)
    keyword_lower = keyword.lower()
    results = []
    for sentence in sentences:
        if keyword_lower in sentence.lower():
            risk = detect_risk_clause_based(sentence)
            simplified = simplify_clause_spacy(sentence)
            results.append({
                "clause": sentence.strip(),
                "risk": risk,
                "simplified": simplified
            })
    return results






# ✅ Rule-based clause explainer using spaCy
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




# Streamlit UI
st.set_page_config(page_title="Clause Risk Analyzer", layout="wide")
st.title("📄 Financial Legal Clause Risk Analyzer (Offline NLP with spaCy + EasyOCR)")

uploaded_file = st.file_uploader("📤 Upload a document (PDF, DOCX, TXT, CSV)", type=["pdf", "docx", "txt", "csv"])
document_text = ""

if uploaded_file:
    if uploaded_file.name.endswith(".pdf"):
        document_text = extract_text_pdf(uploaded_file)
        if not document_text.strip():
            st.warning("No text found in PDF. Trying OCR for scanned content...")
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

    st.success("✅ Document uploaded and processed.")
    st.text_area("📄 Full Document Text (Read-only)", value=document_text, height=300, disabled=True)

    keyword = st.text_input("🔍 Enter a keyword or hint (e.g., indemnity, liability, termination)")
    if keyword and len(keyword.strip()) > 2:
        if st.button("🔍 Analyze"):
            with st.spinner("Analyzing document..."):
                results = analyze_clauses(document_text, keyword)
                if results:
                    st.markdown("### 🧠 Analysis Results")
                    for i, res in enumerate(results, 1):
                        explanation = explain_clause_spacy(res['clause'])
                        st.markdown(f"**Clause {i}:**")
                        st.markdown(f"- 🔍 **Original:** {res['clause']}")
                        st.markdown(f"- ⚠️ **Risk Level:** `{res['risk'].capitalize()}`")
                        st.markdown(f"- 📘 **Explanation:** {'; '.join(explanation)}")
                        st.markdown("---")
                else:
                    st.warning("No relevant clauses found for the given keyword.")