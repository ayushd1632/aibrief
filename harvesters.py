import feedparser
import requests
import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

# ── Keywords used to filter Hacker News for AI-related stories ──
AI_KEYWORDS = [
    "llm", "large language model", "gpt", "claude", "gemini", "llama",
    "openai", "anthropic", "mistral", "ai agent", "artificial intelligence",
    "machine learning", "neural network", "transformer", "diffusion",
    "chatgpt", "copilot", "multimodal", "rag", "retrieval augmented",
    "vector database", "embedding", "fine-tuning", "alignment",
    "voice ai", "speech model", "foundation model", "ai safety"
]


# ────────────────────────────────────────────
# SOURCE 1: arXiv Research Papers
# Free API. No key needed. Returns latest AI papers.
# ────────────────────────────────────────────
def fetch_arxiv_papers(focus_area: str = "General AI", max_results: int = 15) -> list:

    # Map focus area to arXiv category filters
    focus_map = {
        "General AI":           "cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CL",
        "AI Agents":            "cat:cs.AI+AND+ti:agent",
        "Voice AI":             "cat:cs.SD+OR+cat:eess.AS+OR+(cat:cs.CL+AND+ti:speech)",
        "LLMs & Foundation Models": "cat:cs.CL+AND+(ti:language+model+OR+ti:LLM)",
        "AI in Finance":        "cat:cs.AI+AND+(ti:finance+OR+ti:financial)",
        "Computer Vision":      "cat:cs.CV",
        "AI Safety & Ethics":   "cat:cs.AI+AND+(ti:safety+OR+ti:alignment+OR+ti:ethics)",
    }

    query = focus_map.get(focus_area, focus_map["General AI"])
    url = (
        f"https://export.arxiv.org/api/query?"
        f"search_query={query}"
        f"&sortBy=submittedDate"
        f"&sortOrder=descending"
        f"&max_results={max_results}"
    )

    try:
        feed = feedparser.parse(url)

        if not feed.entries:
            return []

        papers = []
        for entry in feed.entries:
            papers.append({
                "title": entry.title.replace("\n", " ").strip(),
                "abstract": entry.summary.replace("\n", " ")[:500].strip(),
                "authors": [a.name for a in entry.authors[:3]] if entry.authors else ["Unknown"],
                "link": entry.link,
                "source": "arXiv",
                "source_type": "arXiv",
                "type": "research",
            })

        return papers

    except Exception as e:
        print(f"arXiv fetch error (non-fatal): {e}")
        return []


# ────────────────────────────────────────────
# SOURCE 2: Hacker News Top AI Stories
# Free Firebase API. No key needed.
# ────────────────────────────────────────────
def fetch_hn_ai_stories(max_to_check: int = 35) -> list:

    try:
        # Step 1: Get the IDs of the current top stories
        ids_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        response = requests.get(ids_url, timeout=10)
        top_ids = response.json()[:max_to_check]

        ai_stories = []

        # Step 2: Fetch each story and filter for AI relevance
        for story_id in top_ids:
            try:
                story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                story = requests.get(story_url, timeout=5).json()

                if not story or not story.get("title"):
                    continue

                title_lower = story["title"].lower()

                if any(kw in title_lower for kw in AI_KEYWORDS):
                    ai_stories.append({
                        "title": story["title"],
                        "url": story.get("url", ""),
                        "score": story.get("score", 0),
                        "comments": story.get("descendants", 0),
                        "source": "Hacker News",
                        "source_type": "Hacker News",
                        "type": "community",
                    })

            except Exception:
                continue  # Skip stories that fail — don't let one bad story crash the whole fetch

        # Return top 8 by score (most upvoted AI stories)
        return sorted(ai_stories, key=lambda x: x["score"], reverse=True)[:8]

    except Exception as e:
        print(f"HN fetch error (non-fatal): {e}")
        return []


# ────────────────────────────────────────────
# SOURCE 3: Industry News via Tavily
# Free tier: 1000 searches/month
# ────────────────────────────────────────────
def fetch_industry_news(focus_area: str = "General AI") -> list:

    tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

    # Build a search query based on focus area
    if focus_area == "General AI":
        query = "artificial intelligence AI news breakthrough this week 2025"
    else:
        query = f"{focus_area} artificial intelligence news 2025"

    try:
        results = tavily.search(
            query=query,
            search_depth="basic",
            max_results=8,
            include_answer=False,
        )

        news_items = []
        for r in results.get("results", []):
            if r.get("title") and r.get("content"):
                news_items.append({
                    "title": r["title"],
                    "content": r["content"][:450].strip(),
                    "url": r.get("url", ""),
                    "source": "News",
                    "source_type": "News",
                    "type": "industry",
                })

        return news_items

    except Exception as e:
        print(f"Tavily fetch error (non-fatal): {e}")
        return []