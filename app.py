import streamlit as st
import feedparser
import time
import re
from datetime import datetime

# --- CONFIGURATION (FORCE DARK THEME) ---
st.set_page_config(
    page_title="African Story Radar", 
    layout="wide", 
    page_icon="🌍",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS (DARK MODE) ---
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    [data-testid="stSidebar"] { background-color: #262730; }
    .stMarkdown { color: #FAFAFA; }
    
    /* Buttons */
    div.stButton > button:first-child {
        width: 100%; border-radius: 8px; border: 1px solid #4A4A4A;
        background-color: #262730; color: #FAFAFA; font-weight: 500;
    }
    div.stButton > button:first-child:hover {
        border-color: #ff4b4b; color: #ff4b4b; background-color: #0E1117;
    }
    
    /* Image Placeholder */
    .img-placeholder {
        background-color: #262730; height: 120px; border-radius: 8px; 
        display: flex; align-items: center; justify-content: center; 
        color: #888; border: 1px solid #4A4A4A;
    }
    
    /* Links & Accents */
    a { color: #4DA6FF !important; }
    hr { border-color: #4A4A4A; }
    
    /* Custom Scrollbar for cleaner look */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #0E1117; }
    ::-webkit-scrollbar-thumb { background: #4A4A4A; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'bookmarks' not in st.session_state:
    st.session_state.bookmarks = []

# --- HELPER FUNCTIONS ---
def extract_image_url(entry):
    if hasattr(entry, 'media_content'):
        for media in entry.media_content:
            if media.get('medium') == 'image' or media.get('type', '').startswith('image'):
                return media['url']
    if hasattr(entry, 'media_thumbnail'):
         if entry.media_thumbnail:
            return entry.media_thumbnail[0]['url']
    if hasattr(entry, 'enclosures'):
        for enclosure in entry.enclosures:
            if enclosure.get('type', '').startswith('image'):
                return enclosure['href']
    if hasattr(entry, 'summary'):
        img_match = re.search(r'<img[^>]+src="([^">]+)"', entry.summary)
        if img_match:
            return img_match.group(1)
    return None

def format_display_date(entry):
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        return time.strftime("%d %b • %H:%M", entry.published_parsed)
    return "Recent"

def get_relative_time(entry):
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        published_ts = time.mktime(entry.published_parsed)
        now_ts = time.time()
        delta_seconds = now_ts - published_ts
        
        if delta_seconds < 60: return "Just now"
        elif delta_seconds < 3600: return f"{int(delta_seconds/60)}m ago"
        elif delta_seconds < 86400: return f"{int(delta_seconds/3600)}h ago"
        else: return f"{int(delta_seconds/86400)}d ago"
    return ""

def parse_date(entry):
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        return time.mktime(entry.published_parsed)
    return 0

# --- DATA FETCHING (Cached) ---
@st.cache_data(ttl=300, show_spinner=False)
def fetch_feed_data(url, source_name):
    try:
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries[:6]: 
            summary = entry.get('summary', 'No summary.')
            summary = re.sub('<[^<]+?>', '', summary) 
            if "Guardian" in source_name and "<" in summary:
                summary = summary.split("<")[0]

            articles.append({
                'title': entry.title,
                'link': entry.link,
                'summary': summary,
                'published_display': format_display_date(entry),
                'relative_time': get_relative_time(entry),
                'timestamp': parse_date(entry),
                'source': source_name,
                'image': extract_image_url(entry)
            })
        return articles
    except:
        return []

# --- DATA SOURCES ---
SOURCE_MAP = {
    "Buzzroom (Buzz Central)": "https://buzzcentral.co.ke/feed/",
    "The Africa Report": "https://www.theafricareport.com/feed/",
    "BBC News Africa": "https://feeds.bbci.co.uk/news/world/africa/rss.xml",
    "The Guardian (Africa)": "https://www.theguardian.com/world/africa/rss",
    "Africanews": "https://www.africanews.com/feed/rss",
    "Quartz Africa": "https://qz.com/africa/rss",
    "Daily Nation (KE)": "https://nation.africa/service/rss/kenya",
    "The East African": "https://www.theeastafrican.co.ke/service/rss/news",
    "The Standard (KE)": "https://www.standardmedia.co.ke/rss/headlines.php",
    "Vanguard (NG)": "https://www.vanguardngr.com/feed/",
    "Punch (NG)": "https://punchng.com/feed/",
    "MyJoyOnline (GH)": "https://www.myjoyonline.com/feed/",
    "News24 (ZA)": "https://feeds.news24.com/articles/news24/TopStories/rss",
    "Mail & Guardian (ZA)": "https://mg.co.za/feed/",
    "TechCabal": "https://techcabal.com/feed/",
    "Business Daily": "https://businessdailyafrica.com/service/rss/bd/news",
    "Disrupt Africa": "https://disrupt-africa.com/feed/",
    "BellaNaija": "https://www.bellanaija.com/feed/",
    "OkayAfrica": "https://www.okayafrica.com/feed/"
}

# --- SIDEBAR ---
with st.sidebar:
    st.header("Radar Controls")
    
    # BOOKMARKS
    if st.session_state.bookmarks:
        st.subheader(f"⭐ Saved ({len(st.session_state.bookmarks)})")
        for i, item in enumerate(st.session_state.bookmarks):
            st.markdown(f"<small>{i+1}. <a href='{item['link']}' style='color:#FF4B4B'>{item['title'][:30]}...</a></small>", unsafe_allow_html=True)
            if st.button("x", key=f"del_{i}"):
                del st.session_state.bookmarks[i]
                st.rerun()
        st.divider()

    # SOURCE SELECTOR
    st.subheader("Select Sources")
    all_source_names = sorted(list(SOURCE_MAP.keys()))
    
    # Pre-select Buzzroom so she sees it immediately
    default_selection = ["Buzzroom (Buzz Central)", "The Guardian (Africa)", "TechCabal"]
    
    selected_sources = st.multiselect(
        "Sources:",
        options=all_source_names,
        default=default_selection
    )
    
    if st.button("🔄 Force Refresh", type="primary"):
        st.cache_data.clear()
        st.rerun()

    st.divider()

    # FILTER & SORT
    search_query = st.text_input("🔍 Search", placeholder="e.g. Climate, AI...")
    sort_option = st.radio("Sort By", ["🕒 Newest First", "🕓 Oldest First", "🔤 Source Name"], index=0)

# --- MAIN APP ---
st.title("Africa Story Radar 🌙")

if not selected_sources:
    st.info("👈 Please select at least one source in the sidebar.")
else:
    # 1. FETCH
    all_stories = []
    
    with st.spinner(f'Checking {len(selected_sources)} sources...'):
        for source_name in selected_sources:
            url = SOURCE_MAP[source_name]
            stories = fetch_feed_data(url, source_name)
            all_stories.extend(stories)

    # 2. FILTER
    if search_query:
        query = search_query.lower()
        all_stories = [s for s in all_stories if query in s['title'].lower() or query in s['summary'].lower()]

    # 3. SORT
    if sort_option == "🕒 Newest First":
        all_stories = sorted(all_stories, key=lambda x: x['timestamp'], reverse=True)
    elif sort_option == "🕓 Oldest First":
        all_stories = sorted(all_stories, key=lambda x: x['timestamp'], reverse=False)
    elif sort_option == "🔤 Source Name":
        all_stories = sorted(all_stories, key=lambda x: x['source'])

    # 4. DISPLAY
    if not all_stories:
        st.warning("No stories found.")
    else:
        st.caption(f"Showing {len(all_stories)} stories.")
        
        for story in all_stories:
            with st.container():
                c1, c2 = st.columns([1, 3])
                
                with c1:
                    if story['image']:
                        st.image(story['image'], use_container_width=True)
                    else:
                        st.markdown("""
                            <div class="img-placeholder">
                                📷 No Image
                            </div>
                            """, unsafe_allow_html=True)
                
                with c2:
                    st.markdown(
                        f"**{story['source']}** • "
                        f"<span style='color:#FF4B4B; font-weight:bold'>{story['published_display']}</span> "
                        f"<span style='color:#AAA; font-size:0.9em'>({story['relative_time']})</span>", 
                        unsafe_allow_html=True
                    )
                    
                    st.subheader(f"[{story['title']}]({story['link']})")
                    
                    if len(story['summary']) > 5:
                        st.markdown(f"<span style='color:#B0B0B0'>{story['summary'][:200]}...</span>", unsafe_allow_html=True)
                    
                    # ACTION BUTTONS
                    st.write("") 
                    col_a, col_b, col_c = st.columns([1, 1, 2])
                    
                    with col_a:
                        st.link_button("🔗 Read", story['link'])
                    
                    with col_b:
                        is_saved = any(b['link'] == story['link'] for b in st.session_state.bookmarks)
                        if is_saved:
                            st.button("✅ Saved", key=f"saved_{story['link']}", disabled=True)
                        else:
                            if st.button("⭐ Save", key=f"save_{story['link']}"):
                                st.session_state.bookmarks.append(story)
                                st.rerun()

                    with col_c:
                         if st.button("✨ Draft Copy", key=f"draft_{story['link']}"):
                            st.caption("Copy this:")
                            st.code(f"🌍 NEW STORY: {story['title']}\n\n"
                                    f"Trend alert from {story['source']}: {story['summary'][:100]}...\n"
                                    f"#Africa #{story['source'].replace(' ', '')}")
                
                st.divider()