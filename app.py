import streamlit as st
from datetime import datetime
import time
import json
import html as html_lib
from harvesters import fetch_arxiv_papers, fetch_hn_ai_stories, fetch_industry_news
from agents import run_synthesis_agent, run_newsletter_agent, run_linkedin_agent

# ════════════════════════════════════════════════════════
# PAGE CONFIG — must be the very first Streamlit command
# ════════════════════════════════════════════════════════
st.set_page_config(
    page_title="AIBrief",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ════════════════════════════════════════════════════════
# CUSTOM CSS — dark AI-tech theme
# ════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Global background + font ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}
.stApp {
    background-color: #0A0A0F;
}
section[data-testid="stSidebar"] {
    background-color: #0F0F1A;
    border-right: 1px solid #1E1E2E;
}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Button styling ── */
.stButton > button {
    background: linear-gradient(135deg, #7C3AED, #6366F1) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 16px !important;
    padding: 14px 28px !important;
    transition: all 0.2s ease !important;
    font-family: 'Inter', sans-serif !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #6D28D9, #4F46E5) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 25px rgba(124, 58, 237, 0.35) !important;
}

/* ── Text input + textarea ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background-color: #13131F !important;
    border: 1px solid #2D2D44 !important;
    border-radius: 8px !important;
    color: #E2E8F0 !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #7C3AED !important;
    box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.2) !important;
}

/* ── Labels ── */
.stTextInput label, .stTextArea label, .stSelectbox label,
.stRadio label, p {
    color: #94A3B8 !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Tab styling ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background-color: #13131F;
    padding: 6px;
    border-radius: 12px;
    border: 1px solid #1E1E2E;
}
.stTabs [data-baseweb="tab"] {
    color: #64748B !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    border-radius: 8px !important;
    padding: 8px 18px !important;
    background: transparent !important;
    border: none !important;
    font-family: 'Inter', sans-serif !important;
}
.stTabs [aria-selected="true"] {
    color: #E2E8F0 !important;
    background: linear-gradient(135deg, #7C3AED22, #6366F122) !important;
    border-bottom: none !important;
}

/* ── Progress bar ── */
.stProgress > div > div > div {
    background: linear-gradient(135deg, #7C3AED, #6366F1) !important;
    border-radius: 4px !important;
}

/* ── Divider ── */
hr { border-color: #1E1E2E !important; }

/* ── Expander ── */
.streamlit-expanderHeader {
    background-color: #13131F !important;
    border: 1px solid #1E1E2E !important;
    border-radius: 8px !important;
    color: #94A3B8 !important;
}

/* ── Code blocks (used for copy-friendly text) ── */
.stCode {
    background-color: #13131F !important;
    border: 1px solid #1E1E2E !important;
    border-radius: 8px !important;
}

/* ── Sidebar headers ── */
.sidebar-section-header {
    color: #475569;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    margin: 20px 0 8px 0;
    font-family: 'Inter', sans-serif;
}

/* ── Download button ── */
.stDownloadButton > button {
    background: #13131F !important;
    color: #94A3B8 !important;
    border: 1px solid #2D2D44 !important;
    font-size: 13px !important;
    padding: 8px 16px !important;
    border-radius: 8px !important;
}
.stDownloadButton > button:hover {
    border-color: #7C3AED !important;
    color: #A78BFA !important;
    background: #1A0533 !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0A0A0F; }
::-webkit-scrollbar-thumb { background: #2D2D44; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #7C3AED; }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# HELPER: RENDER A DIGEST CARD
# Uses st.html() to bypass Streamlit's markdown sanitiser,
# which corrupts complex nested HTML on Streamlit Cloud.
# ════════════════════════════════════════════════════════
def render_digest_card(item: dict) -> None:
    """Renders a single digest item as a beautiful dark card with a clickable source link."""

    category_config = {
        "Research": {"color": "#7C3AED", "bg": "#2D1B69", "border": "#7C3AED55", "icon": "🔬"},
        "Industry": {"color": "#059669", "bg": "#064E3B", "border": "#05966955", "icon": "🏢"},
        "Tool":     {"color": "#0284C7", "bg": "#0C4A6E", "border": "#0284C755", "icon": "🛠️"},
        "Policy":   {"color": "#DC2626", "bg": "#450A0A", "border": "#DC262655", "icon": "⚖️"},
    }
    difficulty_icons = {
        "Technical": "⚡",
        "Business":  "💼",
        "General":   "📖",
    }
    source_icons = {
        "arXiv":        "📄",
        "Hacker News":  "🟠",
        "News":         "📰",
    }

    cat = item.get("category", "Research")
    diff = item.get("difficulty", "General")
    cfg = category_config.get(cat, category_config["Research"])
    diff_icon = difficulty_icons.get(diff, "📖")
    src_icon = source_icons.get(item.get("source_type", "News"), "🌐")
    reading_time = item.get("estimated_reading_time", 2)

    # Safely escape text for HTML
    headline = html_lib.escape(item.get("headline", ""))
    what_happened = html_lib.escape(item.get("what_happened", ""))
    why_matters = html_lib.escape(item.get("why_it_matters", ""))
    source_title_raw = item.get("source_title", "")
    source_title = html_lib.escape(source_title_raw[:65] + ("..." if len(source_title_raw) > 65 else ""))
    source_url = item.get("source_url", "").strip()

    # Build the clickable link row (only if we have a valid URL)
    # Build the clickable link row (only if we have a valid URL)
    if source_url and source_url.startswith("http"):
        link_html = f'<a href="{source_url}" target="_blank" rel="noopener noreferrer" style="color: #6366F1; font-size: 12px; font-family: Inter, sans-serif; text-decoration: none; font-weight: 500; letter-spacing: 0.2px; transition: color 0.15s;">Read original →</a>'
    else:
        link_html = ""

    st.html(f"""
<div style="
    background: linear-gradient(135deg, #111120, #161628);
    border: 1px solid {cfg['border']};
    border-left: 4px solid {cfg['color']};
    border-radius: 12px;
    padding: 20px 24px 18px 24px;
    margin-bottom: 14px;
">
    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;">
        <span style="
            background:{cfg['bg']};
            color:{cfg['color']};
            border:1px solid {cfg['border']};
            padding:3px 11px;
            border-radius:20px;
            font-size:11px;
            font-weight:700;
            letter-spacing:0.8px;
            font-family:Inter,sans-serif;
        ">{cfg['icon']} {cat.upper()}</span>
        <span style="color:#475569; font-size:12px; font-family:Inter,sans-serif;">
            {diff_icon} {diff} &nbsp;·&nbsp; {reading_time} min read
        </span>
    </div>
    <h3 style="
        color:#E2E8F0;
        font-size:17px;
        font-weight:700;
        margin:4px 0 12px 0;
        line-height:1.4;
        letter-spacing:-0.2px;
        font-family:Inter,sans-serif;
    ">{headline}</h3>
    <p style="
        color:#94A3B8;
        font-size:14px;
        line-height:1.8;
        margin-bottom:14px;
        font-family:Inter,sans-serif;
    ">{what_happened}</p>
    <div style="
        background:linear-gradient(135deg,#0F1B3D,#150F35);
        border-radius:8px;
        padding:12px 16px;
        border-left:3px solid #6366F1;
        margin-bottom:14px;
    ">
        <span style="color:#818CF8; font-size:13px; font-weight:600; font-family:Inter,sans-serif;">💡 Why it matters: </span>
        <span style="color:#C7D2FE; font-size:13px; line-height:1.6; font-family:Inter,sans-serif;">{why_matters}</span>
    </div>
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div style="display:flex; align-items:center; gap:8px;">
            <span style="
                background:#1E1E2E;
                color:#475569;
                padding:2px 9px;
                border-radius:4px;
                font-size:11px;
                font-family:Inter,sans-serif;
            ">{src_icon} {item.get('source_type','Web')}</span>
            <span style="color:#334155; font-size:11px; font-family:Inter,sans-serif;">{source_title}</span>
        </div>
        {link_html}
    </div>
</div>
""")


# ════════════════════════════════════════════════════════
# HELPER: ENRICH DIGEST ITEMS WITH SOURCE URLS
# Deterministically matches each item's source_title back
# to the original harvested sources to get the real URL.
# Never relies on the LLM copying URLs correctly.
# ════════════════════════════════════════════════════════
def enrich_digest_urls(
    digest_items: list,
    papers: list,
    hn_stories: list,
    news_items: list,
) -> list:

    lookup = []
    for p in papers:
        if p.get("link"):
            lookup.append((p["title"].lower().strip(), p["link"]))
    for s in hn_stories:
        if s.get("url"):
            lookup.append((s["title"].lower().strip(), s["url"]))
    for n in news_items:
        if n.get("url"):
            lookup.append((n["title"].lower().strip(), n["url"]))

    for item in digest_items:
        if item.get("source_url", "").strip().startswith("http"):
            continue

        query = item.get("source_title", "").lower().strip()
        if not query or len(query) < 8:
            continue

        matched = ""

        # Pass 1: exact match
        for orig, url in lookup:
            if query == orig:
                matched = url
                break

        # Pass 2: substring containment (handles LLM truncation / rewording)
        if not matched and len(query) >= 15:
            for orig, url in lookup:
                if query in orig or orig in query:
                    matched = url
                    break

        # Pass 3: first-25-character prefix match
        if not matched and len(query) >= 15:
            for orig, url in lookup:
                if query[:25] == orig[:25]:
                    matched = url
                    break

        if matched:
            item["source_url"] = matched

    return digest_items


# ════════════════════════════════════════════════════════
# HELPER: RENDER A LINKEDIN POST CARD
# Display-only card using st.html().
# Download button rendered separately in the tab code.
# ════════════════════════════════════════════════════════
def render_linkedin_card(
    post_text: str,
    card_id: str,
    accent_color: str,
    border_color: str,
    label: str,
    sublabel: str,
) -> None:
    safe_text = html_lib.escape(post_text)

    st.html(f"""
<div style="margin-bottom:6px;font-family:Inter,sans-serif;">
    <div style="
        background:linear-gradient(135deg,{accent_color}22,{accent_color}11);
        border:1px solid {accent_color}44;
        border-radius:12px;
        padding:12px 16px 10px 16px;
        margin-bottom:8px;
    ">
        <div style="
            color:{accent_color};font-size:11px;font-weight:700;
            letter-spacing:0.8px;text-transform:uppercase;margin-bottom:4px;
        ">{label}</div>
        <div style="color:#64748B;font-size:12px;">{sublabel}</div>
    </div>
    <div style="
        background:#111120;
        border:1px solid {border_color};
        border-radius:12px;
        padding:20px;
        min-height:120px;
    ">
        <div style="
            color:#94A3B8;font-size:14px;line-height:1.85;
            white-space:pre-wrap;word-wrap:break-word;overflow-wrap:break-word;
        ">{safe_text}</div>
    </div>
</div>
""")


# ════════════════════════════════════════════════════════
# SESSION STATE INITIALISATION
# ════════════════════════════════════════════════════════
if "history" not in st.session_state:
    st.session_state.history = []          # Stores last 3 digests
if "last_results" not in st.session_state:
    st.session_state.last_results = None   # Stores most recent result
if "last_stats" not in st.session_state:
    st.session_state.last_stats = None


# ════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════
with st.sidebar:

    # Logo / title
    st.markdown("""
<div style="padding: 10px 0 20px 0;">
    <span style="
        font-size: 28px;
        font-weight: 800;
        background: linear-gradient(135deg, #A78BFA, #818CF8, #C084FC);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: Inter, sans-serif;
        letter-spacing: -1px;
    ">⚡ AIBrief</span>
    <div style="color: #475569; font-size: 12px; margin-top: 4px; font-family: Inter, sans-serif;">
        Weekly AI intelligence, automated.
    </div>
</div>
""", unsafe_allow_html=True)

    st.divider()

    # ── Personalization ──
    st.markdown('<div class="sidebar-section-header">Personalization</div>', unsafe_allow_html=True)

    user_name = st.text_input(
        "Your name",
        value="Ayush",
        label_visibility="collapsed",
        placeholder="Your first name",
        key="user_name_input",
    )

    org_name = st.text_input(
        "Your club / organization",
        value="UW Foster AI & Data Analytics Club",
        label_visibility="collapsed",
        placeholder="Your club or org name",
        key="org_name_input",
    )

    # ── Focus Area ──
    st.markdown('<div class="sidebar-section-header">Focus Area</div>', unsafe_allow_html=True)

    focus_options = [
        "General AI",
        "AI Agents",
        "Voice AI",
        "LLMs & Foundation Models",
        "AI in Finance",
        "Computer Vision",
        "AI Safety & Ethics",
    ]
    focus_area = st.selectbox(
        "Focus area",
        options=focus_options,
        index=0,
        label_visibility="collapsed",
        key="focus_area_select",
    )

    # ── Output Tone ──
    st.markdown('<div class="sidebar-section-header">Newsletter Tone</div>', unsafe_allow_html=True)

    tone = st.radio(
        "Tone",
        options=["Business-friendly", "Technical", "Mixed"],
        index=0,
        label_visibility="collapsed",
        key="tone_radio",
    )

    st.divider()

    # ── Session History ──
    if st.session_state.history:
        st.markdown('<div class="sidebar-section-header">This Session\'s Briefs</div>', unsafe_allow_html=True)
        for i, h in enumerate(reversed(st.session_state.history[-3:])):
            with st.expander(f"📅 {h['timestamp']} — {h['focus']}", expanded=False):
                st.markdown(
                    f"<span style='color:#64748B; font-size:12px; font-family:Inter,sans-serif;'>"
                    f"📚 {h['papers']} papers · 💬 {h['hn']} HN · 📰 {h['news']} news"
                    f"</span>",
                    unsafe_allow_html=True,
                )
                if st.button(f"View Brief #{len(st.session_state.history) - i}", key=f"history_btn_{i}"):
                    st.session_state.last_results = h["results"]
                    st.session_state.last_stats = h["stats"]
    else:
        st.markdown(
            "<div style='color:#334155; font-size:12px; font-family:Inter,sans-serif;'>"
            "No briefs yet this session.</div>",
            unsafe_allow_html=True,
        )

    st.divider()

    # ── About ──
    with st.expander("About AIBrief", expanded=False):
        st.markdown(
            """<div style='color:#64748B; font-size:12px; line-height:1.7; font-family:Inter,sans-serif;'>
            AIBrief aggregates AI intelligence from arXiv papers, Hacker News discussions,
            and industry news — then uses 3 AI agents to synthesize, explain, and turn it into
            a newsletter and LinkedIn posts.<br><br>
            Built by <strong style='color:#94A3B8;'>Ayush Deshwal</strong> for
            UW Foster's AI & Data Analytics Club.<br><br>
            Sources used: arXiv API · HN Firebase API · Tavily<br>
            LLM: Groq (llama-3.3-70b-versatile)
            </div>""",
            unsafe_allow_html=True,
        )


# ════════════════════════════════════════════════════════
# HERO SECTION
# ════════════════════════════════════════════════════════
st.markdown("""
<div style="
    background: linear-gradient(135deg, #0A0A0F 0%, #1A0533 45%, #100A2A 75%, #0A0A0F 100%);
    border: 1px solid #2D1B69;
    border-radius: 16px;
    padding: 40px 48px 36px 48px;
    margin-bottom: 32px;
">
    <div style="
        font-size: 46px;
        font-weight: 800;
        background: linear-gradient(135deg, #A78BFA, #818CF8, #C084FC);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -2px;
        line-height: 1.1;
        font-family: Inter, sans-serif;
        margin-bottom: 12px;
    ">⚡ AIBrief</div>
    <div style="
        color: #94A3B8;
        font-size: 18px;
        font-weight: 400;
        line-height: 1.5;
        max-width: 680px;
        font-family: Inter, sans-serif;
        margin-bottom: 16px;
    ">
        Your weekly AI intelligence, automatically synthesized from research papers,
        community discussions, and industry news.
    </div>
    <div style="display: flex; gap: 24px; flex-wrap: wrap;">
        <span style="color: #475569; font-size: 13px; font-family: Inter, sans-serif;">
            📄 arXiv papers
        </span>
        <span style="color: #2D2D44; font-size: 13px;">|</span>
        <span style="color: #475569; font-size: 13px; font-family: Inter, sans-serif;">
            🟠 Hacker News
        </span>
        <span style="color: #2D2D44; font-size: 13px;">|</span>
        <span style="color: #475569; font-size: 13px; font-family: Inter, sans-serif;">
            📰 Industry news
        </span>
        <span style="color: #2D2D44; font-size: 13px;">|</span>
        <span style="color: #475569; font-size: 13px; font-family: Inter, sans-serif;">
            🤖 3 AI agents
        </span>
    </div>
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════
# GENERATE BUTTON
# ════════════════════════════════════════════════════════
generate_col, info_col = st.columns([2, 3])

with generate_col:
    generate_clicked = st.button(
        f"⚡  Generate This Week's Brief",
        use_container_width=True,
        key="generate_btn",
    )

with info_col:
    st.markdown(
        f"""<div style="
            color: #475569;
            font-size: 13px;
            line-height: 1.8;
            padding: 10px 0;
            font-family: Inter, sans-serif;
        ">
        Focused on: <strong style="color:#A78BFA;">{focus_area}</strong><br>
        Newsletter for: <strong style="color:#94A3B8;">{user_name} · {org_name}</strong>
        </div>""",
        unsafe_allow_html=True,
    )

st.divider()


# ════════════════════════════════════════════════════════
# GENERATE WORKFLOW
# ════════════════════════════════════════════════════════
if generate_clicked:

    start_time = time.time()

    progress_label = st.empty()
    progress_bar   = st.progress(0)
    stats_bar      = st.empty()

    papers, hn_stories, news_items = [], [], []

    # ── Stage 1: arXiv ──
    progress_label.markdown(
        "<div style='color:#94A3B8; font-size:14px; font-family:Inter,sans-serif;'>"
        "📄 Harvesting arXiv research papers...</div>",
        unsafe_allow_html=True,
    )
    progress_bar.progress(10)
    papers = fetch_arxiv_papers(focus_area)

    # ── Stage 2: Hacker News ──
    progress_label.markdown(
        "<div style='color:#94A3B8; font-size:14px; font-family:Inter,sans-serif;'>"
        "🟠 Scanning Hacker News AI discussions...</div>",
        unsafe_allow_html=True,
    )
    progress_bar.progress(30)
    hn_stories = fetch_hn_ai_stories()

    # ── Stage 3: Industry news ──
    progress_label.markdown(
        "<div style='color:#94A3B8; font-size:14px; font-family:Inter,sans-serif;'>"
        "📰 Fetching industry news...</div>",
        unsafe_allow_html=True,
    )
    progress_bar.progress(50)
    news_items = fetch_industry_news(focus_area)

    # Check that at least one source returned content
    total_sources = len(papers) + len(hn_stories) + len(news_items)
    if total_sources == 0:
        progress_bar.empty()
        progress_label.empty()
        st.error(
            "⚠️ All three sources returned empty results. "
            "This usually means a network issue. "
            "Check that your TAVILY_API_KEY is set correctly and try again."
        )
        st.stop()

    # Show live source count
    stats_bar.markdown(
        f"<div style='color:#475569; font-size:12px; font-family:Inter,sans-serif;'>"
        f"Found: 📄 {len(papers)} papers · 🟠 {len(hn_stories)} HN stories · "
        f"📰 {len(news_items)} news articles</div>",
        unsafe_allow_html=True,
    )

    # ── Stage 4: Synthesis Agent ──
    progress_label.markdown(
        "<div style='color:#94A3B8; font-size:14px; font-family:Inter,sans-serif;'>"
        "🤖 Agent 1: Selecting and synthesizing top 5 items...</div>",
        unsafe_allow_html=True,
    )
    progress_bar.progress(65)

    digest_items = run_synthesis_agent(papers, hn_stories, news_items, focus_area)

    if not digest_items:
        progress_bar.empty()
        progress_label.empty()
        stats_bar.empty()
        st.error(
            "⚠️ The Synthesis Agent returned no items. "
            "This may be a temporary Groq rate limit — wait 60 seconds and try again."
        )
        st.stop()

    # Deterministically attach source URLs by matching titles back to original sources.
    # This is reliable; asking the LLM to copy URLs is not.
    digest_items = enrich_digest_urls(digest_items, papers, hn_stories, news_items)

    # Stage 5: Newsletter Agent
    progress_label.markdown(
        "<div style='color:#94A3B8; font-size:14px; font-family:Inter,sans-serif;'>"
        "✉️ Agent 2: Writing your personalized newsletter...</div>",
        unsafe_allow_html=True,
    )
    progress_bar.progress(80)
    newsletter = run_newsletter_agent(digest_items, focus_area, user_name, org_name)

    # ── Stage 6: LinkedIn Agent ──
    progress_label.markdown(
        "<div style='color:#94A3B8; font-size:14px; font-family:Inter,sans-serif;'>"
        "💼 Agent 3: Writing LinkedIn posts...</div>",
        unsafe_allow_html=True,
    )
    progress_bar.progress(95)
    linkedin = run_linkedin_agent(digest_items, focus_area)

    # ── Done ──
    progress_bar.progress(100)
    elapsed = round(time.time() - start_time)

    progress_label.empty()
    progress_bar.empty()
    stats_bar.empty()

    # Assemble results
    results = {
        "digest":     digest_items,
        "newsletter": newsletter,
        "linkedin_a": linkedin.get("technical", ""),
        "linkedin_b": linkedin.get("business", ""),
    }

    stats = {
        "papers":  len(papers),
        "hn":      len(hn_stories),
        "news":    len(news_items),
        "elapsed": elapsed,
        "date":    datetime.now().strftime("%B %d, %Y"),
    }

    # Save to session
    st.session_state.last_results = results
    st.session_state.last_stats = stats
    st.session_state.history.append({
        "timestamp": datetime.now().strftime("%b %d, %H:%M"),
        "focus":     focus_area,
        "results":   results,
        "stats":     stats,
        "papers":    stats["papers"],
        "hn":        stats["hn"],
        "news":      stats["news"],
    })


# ════════════════════════════════════════════════════════
# RESULTS DISPLAY
# (Shows whenever last_results is set — either fresh or from history)
# ════════════════════════════════════════════════════════
if st.session_state.last_results:

    r     = st.session_state.last_results
    stats = st.session_state.last_stats

    # ── Stats banner ──
    st.markdown(f"""
<div style="
    background: linear-gradient(135deg, #0F1B3D, #150F35);
    border: 1px solid #1E2D5A;
    border-radius: 10px;
    padding: 12px 20px;
    margin-bottom: 24px;
    display: flex;
    flex-wrap: wrap;
    gap: 24px;
    align-items: center;
">
    <span style="color:#10B981; font-size:13px; font-weight:600; font-family:Inter,sans-serif;">✅ Brief ready</span>
    <span style="color:#2D2D44;">|</span>
    <span style="color:#64748B; font-size:13px; font-family:Inter,sans-serif;">📄 {stats['papers']} papers</span>
    <span style="color:#64748B; font-size:13px; font-family:Inter,sans-serif;">🟠 {stats['hn']} HN stories</span>
    <span style="color:#64748B; font-size:13px; font-family:Inter,sans-serif;">📰 {stats['news']} articles</span>
    <span style="color:#2D2D44;">|</span>
    <span style="color:#475569; font-size:13px; font-family:Inter,sans-serif;">⏱ {stats['elapsed']}s</span>
    <span style="color:#2D2D44;">|</span>
    <span style="color:#475569; font-size:13px; font-family:Inter,sans-serif;">📅 {stats['date']}</span>
</div>
""", unsafe_allow_html=True)

    # ── 4 Tabs ──
    tab_digest, tab_newsletter, tab_linkedin, tab_sources = st.tabs([
        "📰  Digest",
        "✉️  Newsletter",
        "💼  LinkedIn",
        "🔗  Sources",
    ])

    # ─── TAB 1: DIGEST ───
    with tab_digest:
        st.markdown(
            f"<div style='color:#94A3B8; font-size:14px; margin-bottom:20px; font-family:Inter,sans-serif;'>"
            f"Top 5 AI developments this week · Focus: <strong style='color:#A78BFA;'>{focus_area}</strong>"
            f"</div>",
            unsafe_allow_html=True,
        )
        if r["digest"]:
            for item in r["digest"]:
                render_digest_card(item)
        else:
            st.warning("No digest items to display.")

    # ─── TAB 2: NEWSLETTER ───
    with tab_newsletter:
        st.markdown(
            "<div style='color:#94A3B8;font-size:14px;margin-bottom:20px;"
            "font-family:Inter,sans-serif;'>"
            "Ready-to-send email draft &middot; Sources appended automatically &middot; "
            "Download below"
            "</div>",
            unsafe_allow_html=True,
        )

        if r["newsletter"]:
            # ── Extract subject line ──
            lines = r["newsletter"].strip().split("\n")
            subject_line = ""
            body_start = 0
            for i, line in enumerate(lines):
                if line.lower().startswith("subject:"):
                    subject_line = line.replace("Subject:", "").replace("subject:", "").strip()
                    body_start = i + 1
                    break

            body_text = "\n".join(lines[body_start:]).strip() if subject_line else r["newsletter"]

            # ── Build sources block from digest items ──
            sources_lines = []
            for idx, digest_item in enumerate(r["digest"], 1):
                src_title = digest_item.get("source_title", "Unknown source")
                src_url   = digest_item.get("source_url", "").strip()
                if src_url and src_url.startswith("http"):
                    sources_lines.append(f"{idx}. {src_title}\n   {src_url}")
                else:
                    sources_lines.append(f"{idx}. {src_title}")

            sources_block = (
                "\n\n" + "\u2500" * 44 + "\n"
                + "\U0001f4da Sources & Further Reading:\n\n"
                + "\n\n".join(sources_lines)
            ) if sources_lines else ""

            full_newsletter_text = body_text + sources_block

            # ── Subject line display ──
            if subject_line:
                st.markdown(
                    f"<div style='background:#1A1A2E; border:1px solid #7C3AED44; border-radius:8px; "
                    f"padding:12px 16px; margin-bottom:16px;'>"
                    f"<span style='color:#475569; font-size:11px; font-weight:700; "
                    f"letter-spacing:1px; font-family:Inter,sans-serif;'>SUBJECT LINE</span><br>"
                    f"<span style='color:#E2E8F0; font-size:15px; font-weight:600; "
                    f"font-family:Inter,sans-serif;'>{html_lib.escape(subject_line)}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            # ── Email body display ──
            st.markdown(
                "<div style='color:#64748B; font-size:12px; margin-bottom:8px; "
                "font-family:Inter,sans-serif;'>"
                "Email body with sources &mdash; select all text and copy, or download below:"
                "</div>",
                unsafe_allow_html=True,
            )
            st.text_area(
                "newsletter_body",
                value=full_newsletter_text,
                height=480,
                label_visibility="collapsed",
                key="newsletter_text_area",
            )

            st.download_button(
                "⬇️ Download Newsletter as .txt",
                data=full_newsletter_text,
                file_name=f"newsletter_{datetime.now().strftime('%Y_%m_%d')}.txt",
                mime="text/plain",
            )

            if sources_lines:
                st.markdown(
                    "<div style='color:#334155; font-size:12px; margin-top:6px; "
                    "font-family:Inter,sans-serif;'>"
                    f"✅ {len(sources_lines)} source link{'s' if len(sources_lines) != 1 else ''} "
                    "appended to the bottom of your newsletter"
                    "</div>",
                    unsafe_allow_html=True,
                )

        else:
            st.warning("Newsletter generation failed. Try regenerating.")

    # ─── TAB 3: LINKEDIN ───
    with tab_linkedin:
        st.markdown(
            "<div style='color:#94A3B8;font-size:14px;margin-bottom:20px;"
            "font-family:Inter,sans-serif;'>"
            "Two post options &middot; Click "
            "<strong style='color:#E2E8F0;'>&#x2B07;&#xFE0F; Download</strong> "
            "below each card to save as a .txt file"
            "</div>",
            unsafe_allow_html=True,
        )

        li_col_a, li_col_b = st.columns(2, gap="large")

        with li_col_a:
            if r["linkedin_a"]:
                render_linkedin_card(
                    post_text=r["linkedin_a"],
                    card_id="post_a",
                    accent_color="#7C3AED",
                    border_color="#7C3AED33",
                    label="⚡ POST A — FOR AI PRACTITIONERS",
                    sublabel="Slightly technical · Thought leadership tone",
                )
                st.download_button(
                    label="⬇️ Download Post A",
                    data=r["linkedin_a"],
                    file_name=f"linkedin_post_a_{datetime.now().strftime('%Y_%m_%d')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="dl_post_a",
                )
            else:
                st.warning("Post A not available.")

        with li_col_b:
            if r["linkedin_b"]:
                render_linkedin_card(
                    post_text=r["linkedin_b"],
                    card_id="post_b",
                    accent_color="#0284C7",
                    border_color="#0284C733",
                    label="💼 POST B — FOR BUSINESS LEADERS",
                    sublabel="Zero jargon · Executive / MBA audience",
                )
                st.download_button(
                    label="⬇️ Download Post B",
                    data=r["linkedin_b"],
                    file_name=f"linkedin_post_b_{datetime.now().strftime('%Y_%m_%d')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="dl_post_b",
                )
            else:
                st.warning("Post B not available.")

    # ── TAB 4: SOURCES ──
    with tab_sources:
        st.markdown(
            f"<div style='color:#94A3B8;font-size:14px;margin-bottom:20px;"
            f"font-family:Inter,sans-serif;'>"
            f"Everything this brief was built from &middot; "
            f"{stats['papers']} papers + {stats['hn']} HN stories + {stats['news']} news articles"
            f"</div>",
            unsafe_allow_html=True,
        )

        if r["digest"]:
            rows_html = ""
            for item in r["digest"]:
                src_type  = item.get("source_type", "Web")
                src_icon  = {"arXiv": "📄", "Hacker News": "🟠", "News": "📰"}.get(src_type, "🌐")
                src_url   = item.get("source_url", "").strip()
                src_title = html_lib.escape(item.get("source_title", ""))

                if src_url and src_url.startswith("http"):
                    title_part = (
                        f'<a href="{src_url}" target="_blank" rel="noopener noreferrer" '
                        f'style="color:#94A3B8;font-size:13px;font-family:Inter,sans-serif;'
                        f'text-decoration:none;border-bottom:1px solid #2D2D44;">'
                        f'{src_title}</a>'
                        f'<span style="color:#6366F1;font-size:11px;margin-left:6px;">&#x2197;</span>'
                    )
                else:
                    title_part = (
                        f'<span style="color:#94A3B8;font-size:13px;'
                        f'font-family:Inter,sans-serif;">{src_title}</span>'
                    )

                rows_html += (
                    f'<div style="padding:10px 0;border-bottom:1px solid #1A1A2E;'
                    f'display:flex;align-items:center;gap:8px;">'
                    f'<span style="color:#475569;font-size:12px;font-family:Inter,sans-serif;'
                    f'white-space:nowrap;">{src_icon} {src_type} &nbsp;&middot;&nbsp;</span>'
                    f'{title_part}'
                    f'</div>'
                )

            st.html(
                f'<div style="font-family:Inter,sans-serif;">'
                f'<div style="color:#7C3AED;font-size:12px;font-weight:700;'
                f'letter-spacing:0.8px;margin-bottom:12px;">SOURCES USED IN THIS DIGEST</div>'
                f'{rows_html}'
                f'</div>'
            )


# ════════════════════════════════════════════════════════
# EMPTY STATE (first load, no results yet)
# ════════════════════════════════════════════════════════
else:
    st.markdown("""
<div style="
    text-align: center;
    padding: 48px 32px;
    color: #334155;
    font-family: Inter, sans-serif;
">
    <div style="font-size: 52px; margin-bottom: 16px;">⚡</div>
    <div style="font-size: 18px; font-weight: 600; color: #475569; margin-bottom: 8px;">
        Ready when you are
    </div>
    <div style="font-size: 14px; line-height: 1.7; max-width: 420px; margin: 0 auto;">
        Set your focus area and personalization in the sidebar,<br>
        then click <strong style="color: #7C3AED;">Generate This Week's Brief</strong>.
    </div>
    <div style="margin-top: 32px; display: flex; justify-content: center; gap: 32px; flex-wrap: wrap;">
        <div style="text-align: center;">
            <div style="font-size: 24px;">📄</div>
            <div style="font-size: 12px; color: #334155; margin-top: 4px;">arXiv Papers</div>
        </div>
        <div style="text-align: center;">
            <div style="font-size: 24px;">🟠</div>
            <div style="font-size: 12px; color: #334155; margin-top: 4px;">Hacker News</div>
        </div>
        <div style="text-align: center;">
            <div style="font-size: 24px;">📰</div>
            <div style="font-size: 12px; color: #334155; margin-top: 4px;">Industry News</div>
        </div>
        <div style="text-align: center;">
            <div style="font-size: 24px;">🤖</div>
            <div style="font-size: 12px; color: #334155; margin-top: 4px;">3 AI Agents</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)