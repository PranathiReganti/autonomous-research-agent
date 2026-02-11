import streamlit as st
import os
import requests
from groq import Groq

# ========== CONFIG ==========
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

# ========== WEB SEARCH ==========
def web_search(query):
    url = "https://google.serper.dev/search"
    payload = {"q": query}
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    results = response.json()

    snippets = []
    for item in results.get("organic", [])[:5]:
        snippets.append(f"{item['title']}: {item['snippet']}")

    return "\n".join(snippets)


# ========== PLANNER AGENT ==========
def planner_agent(topic):
    prompt = f"""
You are a research planning agent.

Your job:
1. Break the topic into structured research sections.
2. Identify what must be searched online.
3. Create a step-by-step research strategy.
4. Output:
   - Research Outline
   - Search Queries List
   - Report Structure

Topic: {topic}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content


# ========== RESEARCH AGENT ==========
def research_agent(plan):
    search_prompt = f"""
From this research plan:

{plan}

Extract ONLY the search queries needed.
Return them as a Python list.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": search_prompt}],
    )

    queries_text = response.choices[0].message.content

    # Basic parsing
    queries = queries_text.replace("[", "").replace("]", "").replace('"', '').split(",")

    research_data = ""

    for q in queries[:2]:
        research_data += f"\nSearch Results for: {q.strip()}\n"
        research_data += web_search(q.strip())
        research_data += "\n\n"

    return research_data


# ========== WRITER AGENT ==========
def writer_agent(topic, research_data):
    prompt = f"""
You are a professional research writer.

Using the topic and real research data below:

TOPIC:
{topic}

RESEARCH DATA:
{research_data}

Write a structured professional research report 
between 700–900 words with:


1. Executive Summary
2. Background
3. Key Findings
4. Data Insights
5. Challenges
6. Future Outlook
7. Conclusion

Include citations like:
(Source: Title)

Make it professional and analytical.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content


# ========== STREAMLIT UI ==========
st.title(" Advanced Autonomous Research Agent")
st.write("Multi-Agent AI System with Planning, Web Search, and Structured Writing")

topic = st.text_input("Enter Research Topic")

if st.button("Generate Advanced Report"):

    progress = st.progress(0)
    status = st.empty()

    status.write(" Planner Agent analyzing topic...")
    progress.progress(20)
    plan = planner_agent(topic)

    status.write(" Research Agent gathering sources...")
    progress.progress(50)
    research = research_agent(plan)

    status.write(" Writer Agent composing structured report...")
    progress.progress(80)
    final_report = writer_agent(topic, research)

    progress.progress(100)
    status.write(" Report generation complete!")

    st.subheader(" Final Research Report")
    st.write(final_report)
