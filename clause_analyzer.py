import streamlit as st
import docx
import pdfplumber
import pandas as pd
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Load Google API Key securely
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # For local use
# GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]  # For Streamlit Cloud

# Extract text from DOCX
def extract_text_docx(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

# Extract text from PDF
def extract_text_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
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

# Query Google PaLM 2 via Vertex AI
def query_google_llm(prompt):
    url = "https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText"
    headers = {"Content-Type": "application/json"}
    payload = {
        "prompt": {"text": prompt},
        "temperature": 0.7,
        "candidateCount": 1
    }
    response = requests.post(f"{url}?key={GOOGLE_API_KEY}", headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()["candidates"][0]["output"]
    else:
        return f"❌ Error: {response.status_code} - {response.text}"

# Streamlit UI
st.set_page_config(page_title="Clause Analyzer", layout="wide")
st.title("📄 Financial Legal Clause Analyzer (Google PaLM 2)")

# Upload document
st.subheader("📤 Upload a financial legal document")
uploaded_file = st.file_uploader("Supported formats: PDF, DOCX, TXT, CSV", type=["pdf", "docx", "txt", "csv"])

document_text = ""
if uploaded_file:
    if uploaded_file.name.endswith(".pdf"):
        document_text = extract_text_pdf(uploaded_file)
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

# Manual clause input
st.subheader("✍️ Enter a Clause to Analyze")
manual_clause = st.text_area("Paste a clause from the uploaded document here:")

if manual_clause and len(manual_clause.strip()) > 30:
    prompt = f"""
    Analyze the following clause:
    \"\"\"{manual_clause}\"\"\"

    Tasks:
    1. Detect the risk level (low, medium, high) and explain why.
    2. Explain the clause in simple language for a non-lawyer.
    """
    with st.spinner("Analyzing your clause..."):
        result = query_google_llm(prompt)
    st.markdown("### 🧠 Analysis Result")
    st.markdown(result)