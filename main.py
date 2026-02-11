import os
import requests
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ---------------------------
#  Web Search Function
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
#  Generate Research Plan
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
#  Expand Each Section
# ---------------------------
def expand_section(topic, section_title):
    search_results, sources = search_web(f"{topic} {section_title}")

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a professional research writer. Use ONLY the provided search results to write factual content."},
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
#  Main Execution
# ---------------------------
if __name__ == "__main__":
    topic = input("Enter research topic: ")

    print("\nGenerating research plan...\n")
    plan = generate_plan(topic)
    print("Research Plan:")
    print(plan)

    sections = plan.split("\n")

    print("\nGenerating detailed report...\n")

    final_report = f"# Research Report on {topic}\n\n"
    all_sources = []

    for section in sections:
        if section.strip() != "":
            content, sources = expand_section(topic, section)
            final_report += f"\n## {section}\n"
            final_report += content + "\n"
            all_sources.extend(sources)

    # Remove duplicate sources
    unique_sources = list(set(all_sources))

    final_report += "\n\n## References\n"

    for idx, (title, link) in enumerate(unique_sources, 1):
        final_report += f"{idx}. {title} - {link}\n"

    print("\n===== FINAL RESEARCH REPORT =====\n")
    print(final_report)
