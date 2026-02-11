import os
import requests
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from io import BytesIO

# Load environment variables
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

st.set_page_config(page_title="Autonomous Research Agent", layout="wide")

st.title("🤖 Autonomous Research Agent")
st.write("Generate structured research reports with real-time web sources and download as PDF.")


# ---------------------------
# 🔍 Web Search Function
# ---------------------------
def search_web(query):
    url = "https://google.serper.dev/search"

    payload = {
        "q": query,
        "num": 5
    }

    headers = {
        "X-API-KEY": os.getenv("SERPER_API_KEY"),
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    results = response.json()

    sources = []
    snippets = []

    if "organic" in results:
        for item in results["organic"]:
            title = item.get("title", "")
            link = item.get("link", "")
            snippet = item.get("snippet", "")

            snippets.append(snippet)
            sources.append((title, link))

    return "\n".join(snippets), sources


# ---------------------------
# 🧠 Generate Research Plan
# ---------------------------
def generate_plan(topic):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are an expert research planner."},
            {"role": "user", "content": f"""
Create a structured research plan with 5 main sections 
for the topic: {topic}.
Only return section titles in numbered format.
"""}
        ],
        temperature=0.5,
    )

    return response.choices[0].message.content


# ---------------------------
# ✍ Expand Each Section
# ---------------------------
def expand_section(topic, section_title):
    search_results, sources = search_web(f"{topic} {section_title}")

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a professional research writer. Use ONLY the provided search results."},
            {"role": "user", "content": f"""
Topic: {topic}
Section: {section_title}

Search Results:
{search_results}

Write a detailed, factual section based only on the search results.
"""}
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content, sources


# ---------------------------
# 📄 PDF Generator
# ---------------------------
def generate_pdf(content):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    for line in content.split("\n"):
        elements.append(Paragraph(line, styles["Normal"]))
        elements.append(Spacer(1, 6))

    doc.build(elements)
    buffer.seek(0)
    return buffer


# ---------------------------
# 🚀 UI Logic
# ---------------------------

topic = st.text_input("Enter Research Topic")

if st.button("Generate Report") and topic:

    st.subheader("📌 Generating Research Plan...")
    plan = generate_plan(topic)
    sections = plan.split("\n")

    st.markdown("## 📋 Research Plan")
    st.write(plan)

    all_sources = []
    full_text_report = f"Research Report on {topic}\n\n"

    st.markdown("## 📄 Detailed Report")

    for section in sections:
        if section.strip() != "":
            content, sources = expand_section(topic, section)
            st.markdown(f"### {section}")
            st.write(content)

            full_text_report += f"{section}\n{content}\n\n"
            all_sources.extend(sources)

    # Remove duplicate sources
    unique_sources = list(set(all_sources))

    st.markdown("## 🔗 References")

    for idx, (title, link) in enumerate(unique_sources, 1):
        st.markdown(f"{idx}. [{title}]({link})")
        full_text_report += f"{idx}. {title} - {link}\n"

    # PDF Download Button
    pdf_file = generate_pdf(full_text_report)

    st.download_button(
        label="📥 Download Report as PDF",
        data=pdf_file,
        file_name="research_report.pdf",
        mime="application/pdf"
    )
