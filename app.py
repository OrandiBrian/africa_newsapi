import streamlit as st
import feedparser
import time
import re
from datetime import datetime
from google import genai

# --- CONFIGURATION ---
st.set_page_config(
    page_title="African Story Radar", 
    layout="wide", 
    page_icon="🌍",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
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
        border-color: #4DA6FF; color: #4DA6FF; background-color: #0E1117;
    }
    
    /* Section Headers in Sidebar */
    .sidebar-region-header {
        color: #8b92a9;
        font-size: 13px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 25px;
        margin-bottom: 10px;
        border-bottom: 1px solid #4A4A4A;
        padding-bottom: 5px;
    }

    .img-placeholder {
        background-color: #262730; height: 120px; border-radius: 8px; 
        display: flex; align-items: center; justify-content: center; 
        color: #888; border: 1px solid #4A4A4A;
    }
    a { color: #4DA6FF !important; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'bookmarks' not in st.session_state:
    st.session_state.bookmarks = []
if 'generated_copy' not in st.session_state:
    st.session_state.generated_copy = {}

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

# --- GEMINI AI (V2.5) ---
def generate_ai_copy(api_key, story_title, story_summary, source):
    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""
        You are a top social media manager for an African media agency.
        Write a punchy, engaging LinkedIn/Instagram caption for this news story.
        Headline: {story_title}
        Source: {source}
        Summary: {story_summary}
        Guidelines: Tone: Professional but exciting. Length: Under 100 words. Include 3 hashtags.
        """
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# --- DATA FETCHING ---
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

# --- EXTENSIVE DATA SOURCES ---
FEEDS_BY_REGION = {
    "Pan-African & Tech": {
        "The Africa Report": "https://www.theafricareport.com/feed/",
        "BBC News Africa": "https://feeds.bbci.co.uk/news/world/africa/rss.xml",
        "TechCabal": "https://techcabal.com/feed/",
        "Buzzroom": "https://buzzcentral.co.ke/feed/",
        "The Guardian": "https://www.theguardian.com/world/africa/rss",
    },
    "Sahel (English)": {
        "HumAngle": "https://humanglemedia.com/feed/",
        "New Humanitarian": "https://www.thenewhumanitarian.org/rss/africa.xml",
        "Voice of America": "https://www.voanews.com/api/zgbpvevmoq"
    },
    "East Africa": {
        "Daily Nation (KE)": "https://nation.africa/service/rss/kenya",
        "East African": "https://www.theeastafrican.co.ke/service/rss/news",
        "Monitor (UG)": "https://www.monitor.co.ug/service/rss/uganda",
        "New Times (RW)": "https://www.newtimes.co.rw/rss",
        "AllAfrica (East)": "https://allafrica.com/tools/headlines/rdf/eastafrica/headlines.rdf"
    },
    "West Africa": {
        "Punch (NG)": "https://punchng.com/feed/",
        "Vanguard (NG)": "https://www.vanguardngr.com/feed/",
        "MyJoyOnline (GH)": "https://www.myjoyonline.com/feed/",
        "AllAfrica (West)": "https://allafrica.com/tools/headlines/rdf/westafrica/headlines.rdf"
    },
    "Southern Africa": {
        "News24 (ZA)": "https://feeds.news24.com/articles/news24/TopStories/rss",
        "Mail & Guardian": "https://mg.co.za/feed/",
        "The Herald (ZW)": "https://www.herald.co.zw/feed/",
        "AllAfrica (South)": "https://allafrica.com/tools/headlines/rdf/southernafrica/headlines.rdf"
    },
    "North Africa": {
        "Ahram Online (EG)": "https://english.ahram.org.eg/News/RSS/1.aspx",
        "Morocco World": "https://www.moroccoworldnews.com/feed",
        "AllAfrica (North)": "https://allafrica.com/tools/headlines/rdf/northafrica/headlines.rdf"
    },
    "Central Africa": {
        "AllAfrica (Central)": "https://allafrica.com/tools/headlines/rdf/centralafrica/headlines.rdf"
    }
}

AFRICAN_COUNTRIES = sorted([
    "Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi", 
    "Cabo Verde", "Cameroon", "Central African Republic", "Chad", "Comoros", 
    "Democratic Republic of the Congo", "Republic of the Congo", "Cote d'Ivoire", 
    "Djibouti", "Egypt", "Equatorial Guinea", "Eritrea", "Eswatini", "Ethiopia", 
    "Gabon", "Gambia", "Ghana", "Guinea", "Guinea-Bissau", "Kenya", "Lesotho", 
    "Liberia", "Libya", "Madagascar", "Malawi", "Mali", "Mauritania", "Mauritius", 
    "Morocco", "Mozambique", "Namibia", "Niger", "Nigeria", "Rwanda", 
    "Sao Tome and Principe", "Senegal", "Seychelles", "Sierra Leone", "Somalia", 
    "South Africa", "South Sudan", "Sudan", "Tanzania", "Togo", "Tunisia", 
    "Uganda", "Zambia", "Zimbabwe"
])

# --- SIDEBAR ---
with st.sidebar:
    st.title("Radar Controls")
    
    with st.expander("✨ Gemini Settings", expanded=False):
        gemini_key = st.text_input("API Key", type="password", placeholder="Paste Google Key Here")

    st.markdown("---")
    
    # --- UNIVERSAL SELECT ALL ---
    # This single checkbox controls everything
    universal_all = st.checkbox("SELECT ALL SOURCES", value=False)
    
    st.markdown("---")
    
    selected_feeds = []

    # --- FLAT LIST LOGIC (NO DROPDOWNS) ---
    for region, feeds in FEEDS_BY_REGION.items():
        # 1. Region Header
        st.markdown(f"<div class='sidebar-region-header'>{region}</div>", unsafe_allow_html=True)
        
        # 2. Logic:
        # If Universal All is checked -> We auto-select everything and hide checkboxes (cleaner).
        # If Universal All is OFF -> We show checkboxes for manual picking.
        
        if universal_all:
            # Add all feeds silently
            for name, url in feeds.items():
                selected_feeds.append((name, url))
            st.caption(f"⚡ {len(feeds)} sources active")
        else:
            # Show individual checkboxes
            for name, url in feeds.items():
                # Pre-select Pan-African ones by default for good UX
                is_default = True if "Pan-African" in region else False
                
                if st.checkbox(name, value=is_default, key=f"chk_{name}"):
                    selected_feeds.append((name, url))

    st.markdown("---")
    if st.button("🔄 Check Updates", type="primary"):
        st.cache_data.clear()
        st.rerun()

# --- MAIN APP ---
st.title("Africa Story Radar")

# --- SMART SEARCH ---
with st.container():
    c1, c2 = st.columns([2, 1])
    with c1:
        search_query = st.text_input("🔍 Search Keyword", placeholder="e.g. Coup, Gold, Cotton...")
    with c2:
        selected_countries = st.multiselect("🏳️ Filter by Country", options=AFRICAN_COUNTRIES)

# --- APP LOGIC ---
if not selected_feeds:
    st.info("👈 Select sources in the sidebar (or check 'SELECT ALL') to start.")
else:
    all_stories = []
    with st.spinner(f'Scanning {len(selected_feeds)} sources...'):
        for name, url in selected_feeds:
            stories = fetch_feed_data(url, name)
            all_stories.extend(stories)

    # DEDUPLICATION
    seen_urls = set()
    unique_stories = []
    for story in all_stories:
        if story['link'] not in seen_urls:
            unique_stories.append(story)
            seen_urls.add(story['link'])
    all_stories = unique_stories

    # FILTER LOGIC
    filtered_stories = []
    if not search_query and not selected_countries:
        filtered_stories = all_stories
    else:
        for story in all_stories:
            match_keyword = True
            match_country = True
            
            if search_query:
                query = search_query.lower()
                if query not in story['title'].lower() and query not in story['summary'].lower():
                    match_keyword = False
            
            if selected_countries:
                found_country = False
                for country in selected_countries:
                    c_lower = country.lower()
                    if (c_lower in story['title'].lower() or 
                        c_lower in story['summary'].lower() or 
                        c_lower in story['source'].lower()):
                        found_country = True
                        break
                match_country = found_country
            
            if match_keyword and match_country:
                filtered_stories.append(story)

    filtered_stories = sorted(filtered_stories, key=lambda x: x['timestamp'], reverse=True)

    if not filtered_stories:
        st.warning("No stories found matching your criteria.")
    else:
        st.caption(f"Found {len(filtered_stories)} stories.")
        
        for story in filtered_stories:
            with st.container():
                c1, c2 = st.columns([1, 3])
                with c1:
                    if story['image']:
                        st.image(story['image'], use_container_width=True)
                    else:
                        st.markdown("""<div class="img-placeholder">📷 No Image</div>""", unsafe_allow_html=True)
                
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
                    
                    st.write("") 
                    col_a, col_b = st.columns([1, 3])
                    with col_a:
                        st.link_button("🔗 Read", story['link'])
                    with col_b:
                        draft_key = f"draft_{story['link']}"
                        if st.button("✨ Draft with Gemini", key=draft_key):
                            if not gemini_key:
                                st.error("👈 Please enter API Key in sidebar!")
                            else:
                                with st.spinner("Writing..."):
                                    ai_text = generate_ai_copy(gemini_key, story['title'], story['summary'], story['source'])
                                    st.session_state.generated_copy[story['link']] = ai_text
                        
                        if story['link'] in st.session_state.generated_copy:
                            st.success("Draft Generated:")
                            st.code(st.session_state.generated_copy[story['link']], language="markdown")
                
                st.divider()