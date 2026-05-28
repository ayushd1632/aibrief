import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ────────────────────────────────────────────
# AGENT 1: Synthesis Agent
# Role: Read all raw sources, pick the best 5, explain in plain English.
# Returns: A list of 5 structured dicts (one per item).
# ────────────────────────────────────────────
def run_synthesis_agent(
    papers: list,
    hn_stories: list,
    news_items: list,
    focus_area: str
) -> list:

    # Build one big text block containing all source material
    sources_text = ""

    for p in papers[:8]:
        sources_text += (
            f"\n[RESEARCH PAPER]\n"
            f"Title: {p['title']}\n"
            f"Abstract: {p['abstract']}\n"
            f"Link: {p.get('link', '')}\n"
        )

    for s in hn_stories[:6]:
        sources_text += (
            f"\n[HACKER NEWS DISCUSSION]\n"
            f"Title: {s['title']}\n"
            f"Community signal: {s['score']} upvotes, {s['comments']} comments\n"
            f"URL: {s.get('url', '')}\n"
        )

    for n in news_items[:6]:
        sources_text += (
            f"\n[INDUSTRY NEWS]\n"
            f"Title: {n['title']}\n"
            f"URL: {n.get('url', '')}\n"
            f"Content: {n['content']}\n"
        )

    if not sources_text.strip():
        return []

    prompt = f"""You are creating a weekly AI digest for business professionals and MBA students.
Your audience is smart but not ML engineers. Zero jargon. Every explanation must be clear to someone in finance or strategy.

From the sources below, select the 5 MOST interesting and important AI developments this week.
Prioritize: surprising results, clear business impact, major new capabilities, significant product releases.
Avoid: purely incremental academic work, pure benchmark comparisons with no real-world angle.

Focus area for this digest: {focus_area}

You MUST return ONLY a valid JSON object with no other text before or after it.
Use exactly this structure:
{{
  "items": [
    {{
      "headline": "8-12 word plain-English headline — no jargon, make it compelling",
      "what_happened": "2-3 sentences explaining what happened for a business professional. No jargon.",
      "why_it_matters": "1 sentence on the real-world business or career implication",
      "category": "Research",
      "difficulty": "Technical",
      "source_title": "copy the exact original title from the sources",
      "source_url": "copy the exact URL or Link value from the sources above — must start with http, copy it verbatim, do not invent or shorten it",
      "source_type": "arXiv or Hacker News or News",
      "estimated_reading_time": 2
    }}
  ]
}}

Rules for each field:
- category: must be exactly one of: Research, Industry, Tool, Policy
- difficulty: must be exactly one of: Technical, Business, General
- source_type: must be exactly one of: arXiv, Hacker News, News
- estimated_reading_time: integer between 1 and 5

Sources to analyze:
{sources_text}"""

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1800,
        response_format={"type": "json_object"},
    )

    try:
        result = json.loads(response.choices[0].message.content)
        items = result.get("items", [])
        # Validate that we have 5 or fewer items and required fields
        valid_items = []
        for item in items[:5]:
            if item.get("headline") and item.get("what_happened"):
                valid_items.append(item)
        return valid_items
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Synthesis agent JSON parse error: {e}")
        return []


# ────────────────────────────────────────────
# AGENT 2: Newsletter Agent
# Role: Take the 5 items and write a personalized club newsletter.
# Returns: Formatted email text as a string.
# ────────────────────────────────────────────
def run_newsletter_agent(
    digest_items: list,
    focus_area: str,
    user_name: str,
    org_name: str
) -> str:

    if not digest_items:
        return "No content to generate newsletter from."

    items_text = json.dumps(digest_items, indent=2)

    prompt = f"""Write a weekly AI newsletter email.

Sender: {user_name} (leader of {org_name})
Audience: Members of {org_name} — MBA students and business professionals who want to stay current on AI without reading papers
Tone: Smart, engaging, like a trusted friend in tech explaining what matters this week

Format the newsletter EXACTLY as follows (keep all the dashes and formatting):

Subject: [Compelling subject line referencing the most interesting item this week — under 60 characters]

Hi {org_name} community,

[2-sentence introduction connecting this week's AI news to a larger trend or theme. Be specific — reference what's in the digest.]

────────────────────────────

[For EACH of the 5 items, write:]
📌 [Repeat the item's headline in bold — copy it exactly]
[2 sentences: what happened in plain English + why an MBA student or business professional should care]

────────────────────────────

[1 closing sentence that invites engagement — ask one thought-provoking question related to the week's content]

Warm regards,
{user_name}
{org_name}

─────
Generated by AIBrief · Reply to unsubscribe

Here are the 5 items:
{items_text}

Write the complete newsletter now. Keep it under 550 words total."""

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=1000,
    )

    return response.choices[0].message.content


# ────────────────────────────────────────────
# AGENT 3: LinkedIn Agent
# Role: Write 2 LinkedIn post options from this week's top items.
# Post A: AI practitioners. Post B: Business/executive audience.
# Returns: Dict with 'technical' and 'business' keys.
# ────────────────────────────────────────────
def run_linkedin_agent(digest_items: list, focus_area: str) -> dict:

    if not digest_items:
        return {"technical": "", "business": ""}

    # Use the top 2 items for LinkedIn content
    top_items = json.dumps(digest_items[:2], indent=2)

    prompt = f"""Write 2 LinkedIn posts about this week's most interesting AI developments.
The author is an MBA student who leads an AI & Data Analytics Club.

POST A — For AI practitioners (people who work in/with AI):
Rules:
- 160-200 words
- Start with a surprising insight or counterintuitive observation — NOT "Excited to share"
- Reference the specific AI development concisely
- End with a genuine question that invites thoughtful comments
- 4-5 hashtags at the end (mix: #LLM #AIAgents #AI #FutureOfWork #MachineLearning)
- Professional but not stiff

POST B — For business executives, MBA peers, non-technical audience:
Rules:
- 110-150 words
- Start with a business implication or leadership insight
- ZERO technical jargon — explain AI as a tool that changes business
- End with a practical takeaway or question a business leader would find genuinely useful
- 3-4 hashtags at the end (#AI #Leadership #MBA #BusinessStrategy)

Return ONLY valid JSON:
{{
  "technical": "full text of Post A — must include hashtags",
  "business": "full text of Post B — must include hashtags"
}}

This week's top AI developments:
{top_items}"""

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=900,
        response_format={"type": "json_object"},
    )

    try:
        result = json.loads(response.choices[0].message.content)
        return {
            "technical": result.get("technical", ""),
            "business": result.get("business", ""),
        }
    except (json.JSONDecodeError, KeyError):
        return {"technical": "", "business": ""}