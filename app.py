import streamlit as st
import os
import requests
from groq import Groq
from fpdf import FPDF

# ===============================
# SESSION STATE FOR MEMORY
# ===============================
if "history" not in st.session_state:
    st.session_state.history = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "current_report" not in st.session_state:
    st.session_state.current_report = ""


# ===============================
# CONFIG
# ===============================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

# ===============================
# WEB SEARCH FUNCTION
# ===============================
def web_search(query):
    url = "https://google.serper.dev/search"

    payload = {"q": query}
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers, timeout=10)

    if response.status_code != 200:
        return "Search API error."

    results = response.json()

    snippets = []
    for item in results.get("organic", [])[:3]:
        snippets.append(f"{item['title']}: {item['snippet']}")

    return "\n".join(snippets)


# ===============================
# PLANNER AGENT
# ===============================
def planner_agent(topic):

    prompt = f"""
You are an advanced research planning agent.

Break the topic into:
1. Key research sections
2. Required search queries
3. Logical structure

Return:
- Research Outline
- Search Queries (comma separated)
- Suggested Report Sections

Topic: {topic}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=800
    )

    return response.choices[0].message.content


# ===============================
# RESEARCH AGENT
# ===============================
def research_agent(plan):

    search_prompt = f"""
From the plan below, extract ONLY the search queries.
Return them as comma-separated list.

Plan:
{plan}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": search_prompt}],
        temperature=0.2,
        max_tokens=300
    )

    queries_text = response.choices[0].message.content
    queries = queries_text.split(",")

    research_data = ""

    for q in queries[:2]:  # limit to 2 for speed
        research_data += f"\nSearch Results for: {q.strip()}\n"
        research_data += web_search(q.strip())
        research_data += "\n\n"

    return research_data


# ===============================
# WRITER AGENT
# ===============================
def writer_agent(topic, research_data):

    prompt = f"""
You are a professional research analyst.

Using the topic and research data below,
write a structured research report.

Include:
1. Executive Summary
2. Background
3. Key Insights
4. Data Findings
5. Challenges
6. Future Outlook
7. Conclusion

Add citations like (Source: Title)

TOPIC:
{topic}

RESEARCH DATA:
{research_data}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=1200
    )

    return response.choices[0].message.content


# ===============================
# PDF GENERATOR
# ===============================
def generate_pdf(report_text):

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    pdf.set_font("Arial", size=11)

    for line in report_text.split("\n"):
        pdf.multi_cell(0, 8, line)

    file_path = "research_report.pdf"
    pdf.output(file_path)
    return file_path


# ===============================
# STREAMLIT UI
# ===============================
st.set_page_config(page_title="Autonomous Research Agent", layout="wide")

st.title(" Advanced Autonomous Research Agent")
st.write("Multi-Agent AI System with Real-Time Web Search & PDF Export")

topic = st.text_input("Enter Research Topic")

if st.button("Generate Advanced Report"):

    if not topic:
        st.warning("Please enter a research topic.")
    else:
        progress = st.progress(0)
        status = st.empty()

        status.write(" Planner Agent analyzing topic...")
        progress.progress(20)
        plan = planner_agent(topic)

        status.write(" Research Agent gathering sources...")
        progress.progress(50)
        research = research_agent(plan)

        status.write(" Writer Agent composing report...")
        progress.progress(80)
        final_report = writer_agent(topic, research)

        progress.progress(100)
        status.write(" Report generation complete!")

        st.subheader(" Final Research Report")
        st.write(final_report)
        st.session_state.current_report = final_report


        # Save to history safely
        st.session_state.history.append({
            "topic": topic,
            "report": final_report
        })

        # Generate PDF safely
        pdf_path = generate_pdf(final_report)

        with open(pdf_path, "rb") as f:
            st.download_button(
                label=" Download as PDF",
                data=f,
                file_name="AI_Research_Report.pdf",
                mime="application/pdf"
            )
# ===============================
# FOLLOW-UP CHAT MODE
# ===============================

if st.session_state.current_report:

    st.markdown("---")
    st.subheader(" Refine or Ask Follow-up")

    follow_up = st.text_input("Ask something about this report")

    if st.button("Refine Report") and follow_up:

        refine_prompt = f"""
You are a research assistant.

Original Report:
{st.session_state.current_report}

User Request:
{follow_up}

Update or refine the report accordingly.
Return full updated version.
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": refine_prompt}],
            temperature=0.4,
            max_tokens=1200
        )

        updated_report = response.choices[0].message.content

        st.session_state.current_report = updated_report
        st.session_state.chat_history.append((follow_up, updated_report))

        st.subheader(" Updated Report")
        st.write(updated_report)


# ===============================
# SIDEBAR HISTORY
# ===============================
st.sidebar.title("📚 Research History")

if st.session_state.history:
    for i, item in enumerate(st.session_state.history):
        if st.sidebar.button(item["topic"], key=f"history_{i}"):
            st.subheader(f" Previous Report: {item['topic']}")
            st.write(item["report"])
else:
    st.sidebar.write("No research history yet.")
