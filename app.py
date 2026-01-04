import streamlit as st
import feedparser
import time
import re
from datetime import datetime
from google import genai
from textblob import TextBlob  # For Sentiment Analysis

# --- CONFIGURATION ---
st.set_page_config(
    page_title="African Story Radar Pro", 
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
    
    /* Sentiment Badges */
    .badge-pos { background-color: #1b4d3e; color: #4ade80; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }
    .badge-neg { background-color: #4d1b1b; color: #f87171; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }
    .badge-neu { background-color: #333; color: #ccc; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }

    /* Headers */
    .sidebar-region-header {
        color: #8b92a9; font-size: 13px; font-weight: 700; 
        text-transform: uppercase; letter-spacing: 1px; 
        margin-top: 25px; margin-bottom: 10px; 
        border-bottom: 1px solid #4A4A4A; padding-bottom: 5px;
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
if 'newsletter_queue' not in st.session_state:
    st.session_state.newsletter_queue = {} # Stores stories for the newsletter
if 'generated_copy' not in st.session_state:
    st.session_state.generated_copy = {}

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

# Create a flat list of all sources for the Favorites dropdown
ALL_SOURCES_FLAT = {}
for region, feeds in FEEDS_BY_REGION.items():
    for name, url in feeds.items():
        ALL_SOURCES_FLAT[name] = url

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

# --- HELPER FUNCTIONS ---
def get_sentiment(text):
    """Analyzes text for sentiment polarity."""
    try:
        blob = TextBlob(text)
        score = blob.sentiment.polarity
        if score > 0.1:
            return "Positive", "badge-pos", "🟢 Good News"
        elif score < -0.1:
            return "Negative", "badge-neg", "🔴 Crisis/Issue"
        else:
            return "Neutral", "badge-neu", "⚪ Neutral"
    except:
        return "Neutral", "badge-neu", "⚪ Neutral"

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

# --- GEMINI AI FUNCTIONS ---
def generate_single_post(api_key, story):
    """Generates a single social media post."""
    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""
        Write a punchy LinkedIn caption (under 100 words) for this story:
        Headline: {story['title']}
        Source: {story['source']}
        Summary: {story['summary']}
        Context: {story['sentiment_label']}
        """
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

def generate_newsletter(api_key, stories):
    """Generates a newsletter from multiple stories."""
    try:
        client = genai.Client(api_key=api_key)
        
        # Prepare the list of stories text
        stories_text = ""
        for i, s in enumerate(stories):
            stories_text += f"{i+1}. {s['title']} ({s['source']}): {s['summary'][:150]}...\n\n"
            
        prompt = f"""
        You are an editor for a leading African news brief. 
        Write a "Morning Briefing" newsletter based on these selected stories:
        
        {stories_text}
        
        Format:
        - A catchy Intro paragraph summarizing the mood.
        - Bullet points for the stories (rewrite them to be engaging).
        - A "Quote of the Day" or closing thought.
        """
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
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
            
            # CALCULATE SENTIMENT
            sent_score, sent_class, sent_label = get_sentiment(entry.title + " " + summary)

            articles.append({
                'title': entry.title,
                'link': entry.link,
                'summary': summary,
                'published_display': format_display_date(entry),
                'relative_time': get_relative_time(entry),
                'timestamp': parse_date(entry),
                'source': source_name,
                'image': extract_image_url(entry),
                'sentiment_class': sent_class,
                'sentiment_label': sent_label
            })
        return articles
    except:
        return []

# --- SIDEBAR UI ---
with st.sidebar:
    st.title("Radar Controls")
    
    with st.expander("✨ Gemini Settings", expanded=False):
        gemini_key = st.text_input("API Key", type="password", placeholder="Paste Google Key Here")

    st.markdown("---")
    
    # 1. FAVORITES SYSTEM
    st.markdown("### ❤️ My Favorites")
    favorite_selection = st.multiselect(
        "Auto-load these feeds:",
        options=sorted(list(ALL_SOURCES_FLAT.keys())),
        placeholder="Select your top reads..."
    )
    
    st.markdown("---")
    
    # 2. SOURCE SELECTOR
    universal_all = st.checkbox("✅ SELECT ALL SOURCES", value=False)
    
    selected_feeds = []

    # Add favorites first!
    for fav in favorite_selection:
        if fav in ALL_SOURCES_FLAT:
            selected_feeds.append((fav, ALL_SOURCES_FLAT[fav]))

    # Add manual selections
    for region, feeds in FEEDS_BY_REGION.items():
        st.markdown(f"<div class='sidebar-region-header'>{region}</div>", unsafe_allow_html=True)
        
        if universal_all:
            for name, url in feeds.items():
                # Avoid adding duplicates if already in favorites
                if name not in favorite_selection:
                    selected_feeds.append((name, url))
        else:
            for name, url in feeds.items():
                if name not in favorite_selection: # Don't show checkbox if already favorited
                    if st.checkbox(name, key=f"chk_{name}"):
                        selected_feeds.append((name, url))

    # 3. NEWSLETTER QUEUE
    st.markdown("---")
    if st.session_state.newsletter_queue:
        st.info(f"📝 **Newsletter Queue: {len(st.session_state.newsletter_queue)} items**")
        
        if st.button("🚀 Generate Newsletter"):
            if not gemini_key:
                st.error("Need API Key!")
            else:
                with st.spinner("Gemini is writing your morning brief..."):
                    newsletter_content = generate_newsletter(gemini_key, list(st.session_state.newsletter_queue.values()))
                    st.session_state['newsletter_result'] = newsletter_content

    if st.button("🔄 Refresh Radar", type="primary"):
        st.cache_data.clear()
        st.rerun()

# --- MAIN APP ---
st.title("Africa Story Radar Pro")

# --- NEWSLETTER RESULT DISPLAY ---
if 'newsletter_result' in st.session_state:
    with st.expander("📰 Your AI Generated Newsletter (Click to Copy)", expanded=True):
        st.code(st.session_state['newsletter_result'], language="markdown")
        if st.button("Clear Newsletter", key="clear_news"):
            del st.session_state['newsletter_result']
            st.session_state.newsletter_queue = {}
            st.rerun()

# --- SEARCH ---
with st.container():
    c1, c2 = st.columns([2, 1])
    with c1:
        search_query = st.text_input("🔍 Search Keyword", placeholder="e.g. Coup, Gold, Cotton...")
    with c2:
        selected_countries = st.multiselect("🏳️ Filter by Country", options=AFRICAN_COUNTRIES)

# --- FEED LOGIC ---
if not selected_feeds:
    st.info("👈 Select Favorites or check sources in the sidebar to begin.")
else:
    all_stories = []
    # Deduplicate sources just in case
    unique_feeds = list(set(selected_feeds))
    
    with st.spinner(f'Scanning {len(unique_feeds)} sources...'):
        for name, url in unique_feeds:
            stories = fetch_feed_data(url, name)
            all_stories.extend(stories)

    # DEDUPLICATION (Stories)
    seen_urls = set()
    unique_stories = []
    for story in all_stories:
        if story['link'] not in seen_urls:
            unique_stories.append(story)
            seen_urls.add(story['link'])
    all_stories = unique_stories

    # FILTERING
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
        st.warning("No stories found.")
    else:
        st.caption(f"Found {len(filtered_stories)} stories.")
        
        for story in filtered_stories:
            with st.container():
                c1, c2 = st.columns([1, 3])
                with c1:
                    if story['image']:
                        st.image(story['image'], width="stretch")
                    else:
                        st.markdown("""<div class="img-placeholder">📷 No Image</div>""", unsafe_allow_html=True)
                
                with c2:
                    # HEADER WITH SENTIMENT BADGE
                    st.markdown(
                        f"<span class='{story['sentiment_class']}'>{story['sentiment_label']}</span> "
                        f"**{story['source']}** • "
                        f"<span style='color:#AAA; font-size:0.9em'>{story['relative_time']}</span>", 
                        unsafe_allow_html=True
                    )
                    
                    st.subheader(f"[{story['title']}]({story['link']})")
                    
                    if len(story['summary']) > 5:
                        st.markdown(f"<span style='color:#B0B0B0'>{story['summary'][:200]}...</span>", unsafe_allow_html=True)
                    
                    st.write("") 
                    col_a, col_b, col_c = st.columns([1, 1, 1.5])
                    with col_a:
                        st.link_button("🔗 Read", story['link'])
                    
                    with col_b:
                        # NEWSLETTER TOGGLE
                        # Check if this specific link is already in the queue
                        is_in_queue = story['link'] in st.session_state.newsletter_queue
                        
                        if is_in_queue:
                             if st.button("❌ Remove", key=f"rem_{story['link']}"):
                                 del st.session_state.newsletter_queue[story['link']]
                                 st.rerun()
                        else:
                             if st.button("📝 Add to Brief", key=f"add_{story['link']}"):
                                 st.session_state.newsletter_queue[story['link']] = story
                                 st.rerun()

                    with col_c:
                        if st.button("✨ Draft Post", key=f"draft_{story['link']}"):
                            if not gemini_key:
                                st.error("Add API Key!")
                            else:
                                with st.spinner("Writing..."):
                                    ai_text = generate_single_post(gemini_key, story)
                                    st.session_state.generated_copy[story['link']] = ai_text
                        
                        if story['link'] in st.session_state.generated_copy:
                            st.code(st.session_state.generated_copy[story['link']], language="markdown")
                
                st.divider()