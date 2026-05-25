# ⚡ AIBrief — Weekly AI Intelligence, Automated

> Built because staying current on AI while leading an MBA club and doing a full course load is genuinely impossible to do manually.

## 🎯 What It Does

AIBrief automatically aggregates the week's most interesting AI developments from three live sources, runs them through 3 specialized AI agents, and produces a ready-to-use digest, newsletter, and LinkedIn posts — in 90 seconds.

**Built for:** Club leaders, researchers, and business professionals who need to stay current on AI without spending hours on it.

## 🚀 Live Demo

**[Open AIBrief →](YOUR_STREAMLIT_URL_HERE)**

## 🤖 The 3 AI Agents

| Agent | Role | Output |
|-------|------|--------|
| 🔬 Synthesis Agent | Reads all sources, selects top 5, explains in plain English | 5 structured digest cards with category + difficulty tags |
| ✉️ Newsletter Agent | Takes the 5 items, writes personalized club email | Ready-to-send newsletter draft with subject line |
| 💼 LinkedIn Agent | Takes top 2 items, writes two post versions | Post A (practitioners) + Post B (executives) |

## 🏗️ Architecture
Live Sources
├── arXiv API (free, no key)         → Research papers
├── Hacker News Firebase API (free)   → Community discussions
└── Tavily Search API (free tier)     → Industry news
↓
Agent 1: Synthesis  →  5 items (JSON)
↓
Agent 2: Newsletter  →  Email draft
Agent 3: LinkedIn    →  2 posts
↓
Streamlit app (dark theme, card UI)

## ✨ Features

- **Focus area selector** — General AI, AI Agents, Voice AI, LLMs, AI in Finance, Computer Vision, AI Safety
- **Personalization** — Your name and club/org carried through into every output
- **Card-based digest** — Category tags, difficulty indicators, reading time estimates
- **Email preview** — Newsletter displayed in clean email-style frame
- **Dual LinkedIn posts** — Technical and business versions, one-click copy
- **Session history** — Last 3 digests accessible from sidebar
- **Source attribution** — Every item links back to its original source

## 🛠️ Tech Stack

- LLM: Groq API (llama-3.3-70b-versatile) — JSON response mode for reliable structured output
- Web search: Tavily API
- Paper feed: arXiv Atom API (free, no key)
- Community: HN Firebase API (free, no key)
- UI: Streamlit with custom CSS (Inter font, dark theme, gradient cards)
- Deployment: Streamlit Community Cloud

## 📖 Context

I co-president UW Foster's AI & Data Analytics Club (200+ members). My job is to be the person who knows what's happening in AI. Manually keeping up means reading arXiv daily, tracking HN, monitoring news — 2–3 hours every week just to find content. AIBrief does it in 90 seconds every Sunday morning.

## 💻 Run Locally

```bash
git clone https://github.com/YOUR_USERNAME/aibrief
cd aibrief
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Create .env with GROQ_API_KEY and TAVILY_API_KEY
streamlit run app.py
```