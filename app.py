import streamlit as st
from datetime import datetime
import time
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
# ════════════════════════════════════════════════════════
def render_digest_card(item: dict) -> None:
    """Renders a single digest item as a beautiful dark card."""

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

    # Escape curly braces in content to avoid f-string conflicts
    headline = item.get("headline", "").replace("{", "{{").replace("}", "}}")
    what_happened = item.get("what_happened", "").replace("{", "{{").replace("}", "}}")
    why_matters = item.get("why_it_matters", "").replace("{", "{{").replace("}", "}}")
    source_title = item.get("source_title", "")[:65]
    if len(item.get("source_title", "")) > 65:
        source_title += "..."

    st.markdown(f"""
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
</div>
""", unsafe_allow_html=True)


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

    # ── Progress container ──
    progress_container = st.container()

    with progress_container:
        progress_label = st.empty()
        progress_bar = st.progress(0)
        stats_bar = st.empty()

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

    # ── Stage 5: Newsletter Agent ──
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
            "<div style='color:#94A3B8; font-size:14px; margin-bottom:20px; font-family:Inter,sans-serif;'>"
            "Ready-to-send email draft · Copy the text below and paste into your email client"
            "</div>",
            unsafe_allow_html=True,
        )

        if r["newsletter"]:
            # Try to extract subject line for display
            lines = r["newsletter"].strip().split("\n")
            subject_line = ""
            body_start = 0
            for i, line in enumerate(lines):
                if line.lower().startswith("subject:"):
                    subject_line = line.replace("Subject:", "").replace("subject:", "").strip()
                    body_start = i + 1
                    break

            if subject_line:
                st.markdown(
                    f"<div style='background:#1A1A2E; border:1px solid #7C3AED44; border-radius:8px; "
                    f"padding:12px 16px; margin-bottom:16px;'>"
                    f"<span style='color:#475569; font-size:11px; font-weight:700; "
                    f"letter-spacing:1px; font-family:Inter,sans-serif;'>SUBJECT LINE</span><br>"
                    f"<span style='color:#E2E8F0; font-size:15px; font-weight:600; "
                    f"font-family:Inter,sans-serif;'>{subject_line}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                body_text = "\n".join(lines[body_start:]).strip()
            else:
                body_text = r["newsletter"]

            # Email preview frame
            # Use st.text_area for easy selecting + copying
            st.markdown(
                "<div style='color:#64748B; font-size:12px; margin-bottom:8px; "
                "font-family:Inter,sans-serif;'>Email body — select all text and copy:</div>",
                unsafe_allow_html=True,
            )
            st.text_area(
                "newsletter_body",
                value=body_text,
                height=420,
                label_visibility="collapsed",
                key="newsletter_text_area",
            )

            col_dl, col_code = st.columns([1, 2])
            with col_dl:
                st.download_button(
                    "⬇️ Download as .txt",
                    data=r["newsletter"],
                    file_name=f"newsletter_{datetime.now().strftime('%Y_%m_%d')}.txt",
                    mime="text/plain",
                )

        else:
            st.warning("Newsletter generation failed. Try regenerating.")

    # ─── TAB 3: LINKEDIN ───
    with tab_linkedin:
        st.markdown(
            "<div style='color:#94A3B8; font-size:14px; margin-bottom:20px; font-family:Inter,sans-serif;'>"
            "Two post options · Choose the one that fits the audience you're targeting"
            "</div>",
            unsafe_allow_html=True,
        )

        li_col_a, li_col_b = st.columns(2, gap="large")

        with li_col_a:
            st.markdown("""
<div style="
    background: linear-gradient(135deg, #150A35, #1A1040);
    border: 1px solid #7C3AED44;
    border-radius: 12px;
    padding: 16px 18px 12px 18px;
    margin-bottom: 12px;
">
    <div style="color:#7C3AED; font-size:11px; font-weight:700;
                letter-spacing:0.8px; font-family:Inter,sans-serif; margin-bottom:6px;">
        ⚡ POST A — FOR AI PRACTITIONERS
    </div>
    <div style="color:#94A3B8; font-size:12px; font-family:Inter,sans-serif;">
        Slightly technical · Thought leadership tone
    </div>
</div>
""", unsafe_allow_html=True)
            if r["linkedin_a"]:
                st.code(r["linkedin_a"], language=None)
            else:
                st.warning("Post A not available.")

        with li_col_b:
            st.markdown("""
<div style="
    background: linear-gradient(135deg, #0C2040, #0F1A30);
    border: 1px solid #0284C744;
    border-radius: 12px;
    padding: 16px 18px 12px 18px;
    margin-bottom: 12px;
">
    <div style="color:#0284C7; font-size:11px; font-weight:700;
                letter-spacing:0.8px; font-family:Inter,sans-serif; margin-bottom:6px;">
        💼 POST B — FOR BUSINESS LEADERS
    </div>
    <div style="color:#94A3B8; font-size:12px; font-family:Inter,sans-serif;">
        Zero jargon · Executive / MBA audience
    </div>
</div>
""", unsafe_allow_html=True)
            if r["linkedin_b"]:
                st.code(r["linkedin_b"], language=None)
            else:
                st.warning("Post B not available.")

        st.markdown(
            "<div style='color:#334155; font-size:12px; margin-top:8px; font-family:Inter,sans-serif;'>"
            "💡 Tip: Click the copy icon in the top-right corner of each post to copy to clipboard."
            "</div>",
            unsafe_allow_html=True,
        )

    # ─── TAB 4: SOURCES ───
    with tab_sources:
        st.markdown(
            f"<div style='color:#94A3B8; font-size:14px; margin-bottom:20px; font-family:Inter,sans-serif;'>"
            f"Everything this brief was built from · {stats['papers']} papers + "
            f"{stats['hn']} HN stories + {stats['news']} news articles"
            f"</div>",
            unsafe_allow_html=True,
        )

        if r["digest"]:
            st.markdown(
                "<div style='color:#7C3AED; font-size:12px; font-weight:700; "
                "letter-spacing:0.8px; font-family:Inter,sans-serif; margin-bottom:12px;'>"
                "SOURCES USED IN THIS DIGEST</div>",
                unsafe_allow_html=True,
            )
            for item in r["digest"]:
                source_icon = {"arXiv": "📄", "Hacker News": "🟠", "News": "📰"}.get(
                    item.get("source_type", "News"), "🌐"
                )
                st.markdown(
                    f"<div style='padding: 8px 0; border-bottom: 1px solid #1E1E2E;'>"
                    f"<span style='color:#475569; font-size:12px; font-family:Inter,sans-serif;'>"
                    f"{source_icon} {item.get('source_type','Web')} &nbsp;·&nbsp; "
                    f"</span>"
                    f"<span style='color:#94A3B8; font-size:13px; font-family:Inter,sans-serif;'>"
                    f"{item.get('source_title','')}"
                    f"</span></div>",
                    unsafe_allow_html=True,
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