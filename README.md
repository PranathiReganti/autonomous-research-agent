#  Autonomous Research Agent (RAG-Based)

An AI-powered Autonomous Research Agent that generates structured, source-grounded research reports using real-time web search.

## Features

- Multi-step research planning
- Real-time web search integration (Serper API)
- Retrieval-Augmented Generation (RAG)
- Source-grounded content
- Clickable references
- Streamlit web interface
- PDF download functionality

##  Tech Stack

- Python
- Groq LLM (LLaMA 3.1)
- Serper API (Google Search)
- Streamlit
- ReportLab

##  Architecture

1. User enters topic
2. LLM generates structured research plan
3. Each section triggers web search
4. Retrieved snippets are fed into LLM
5. Final structured report generated
6. References extracted and displayed
7. Optional PDF export

##  How to Run

```bash
pip install -r requirements.txt
streamlit run app.py
