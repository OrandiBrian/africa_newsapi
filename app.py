import streamlit as st
import math
import concurrent.futures
from config import FEEDS_BY_REGION, ALL_SOURCES_FLAT, AFRICAN_COUNTRIES, ITEMS_PER_PAGE
from services import fetch_feed_data, generate_single_post, generate_newsletter, fetch_all_feeds

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
    st.session_state.newsletter_queue = {} 
if 'generated_copy' not in st.session_state:
    st.session_state.generated_copy = {}
if 'current_page' not in st.session_state:
    st.session_state.current_page = 0

# --- SIDEBAR ---
with st.sidebar:
    st.title("Radar Controls")
    
    with st.expander("✨ Gemini Settings"):
        gemini_key = st.text_input("API Key", type="password", placeholder="Paste Google Key Here")

    st.markdown("---")
    
    # FAVORITES
    st.markdown("### ❤️ Favorites")
    favorite_selection = st.multiselect("Top Picks:", options=sorted(list(ALL_SOURCES_FLAT.keys())))
    
    st.markdown("---")
    
    # SOURCES
    universal_all = st.checkbox("✅ SELECT ALL SOURCES", value=False)
    selected_feeds = []

    # Add favorites
    for fav in favorite_selection:
        if fav in ALL_SOURCES_FLAT: selected_feeds.append((fav, ALL_SOURCES_FLAT[fav]))

    # Add manual selections
    for region, feeds in FEEDS_BY_REGION.items():
        st.markdown(f"<div class='sidebar-region-header'>{region}</div>", unsafe_allow_html=True)
        if universal_all:
            for name, url in feeds.items():
                if name not in favorite_selection: selected_feeds.append((name, url))
        else:
            for name, url in feeds.items():
                if name not in favorite_selection:
                    if st.checkbox(name, key=f"chk_{name}"): selected_feeds.append((name, url))

    # NEWSLETTER
    st.markdown("---")
    if st.session_state.newsletter_queue:
        st.info(f"📝 **Queue: {len(st.session_state.newsletter_queue)} items**")
        if st.button("🚀 Generate Newsletter"):
            if not gemini_key: st.error("Need API Key!")
            else:
                with st.spinner("Writing..."):
                    st.session_state['newsletter_result'] = generate_newsletter(gemini_key, list(st.session_state.newsletter_queue.values()))

    if st.button("🔄 Refresh Radar", type="primary"):
        st.cache_data.clear()
        st.session_state.current_page = 0 # Reset page on refresh
        st.rerun()

# --- MAIN APP ---
st.title("Africa Story Radar Pro")

# --- NEWSLETTER RESULT ---
if 'newsletter_result' in st.session_state:
    with st.expander("📰 Your Newsletter (Click to Copy)", expanded=True):
        st.code(st.session_state['newsletter_result'], language="markdown")
        if st.button("Clear"):
            del st.session_state['newsletter_result']
            st.session_state.newsletter_queue = {}
            st.rerun()

# --- SEARCH ---
with st.container():
    c1, c2 = st.columns([2, 1])
    with c1:
        # Reset page if search changes
        search_query = st.text_input("🔍 Search Keyword", placeholder="e.g. Coup, Gold, Cotton...")
    with c2:
        selected_countries = st.multiselect("🏳️ Filter by Country", options=AFRICAN_COUNTRIES)

# --- FEED LOGIC ---
if not selected_feeds:
    st.info("👈 Select sources in the sidebar.")
else:
    all_stories = []
    unique_feeds = list(set(selected_feeds))
    
    with st.spinner(f'Scanning {len(unique_feeds)} sources...'):
        # Using the modularized fetch function
        all_stories = fetch_all_feeds(unique_feeds)

    # Deduplicate
    seen_urls = set()
    unique_stories = []
    for story in all_stories:
        if story['link'] not in seen_urls:
            unique_stories.append(story)
            seen_urls.add(story['link'])
    all_stories = unique_stories

    # Filter
    filtered_stories = []
    if not search_query and not selected_countries:
        filtered_stories = all_stories
    else:
        for story in all_stories:
            match_keyword = True
            match_country = True
            if search_query:
                query = search_query.lower()
                if query not in story['title'].lower() and query not in story['summary'].lower(): match_keyword = False
            if selected_countries:
                found_country = False
                for country in selected_countries:
                    c_lower = country.lower()
                    if (c_lower in story['title'].lower() or c_lower in story['summary'].lower() or c_lower in story['source'].lower()):
                        found_country = True
                        break
                match_country = found_country
            if match_keyword and match_country: filtered_stories.append(story)

    filtered_stories = sorted(filtered_stories, key=lambda x: x['timestamp'], reverse=True)

    # --- PAGINATION LOGIC ---
    if not filtered_stories:
        st.warning("No stories found.")
    else:
        # 1. Calculate Pages
        total_stories = len(filtered_stories)
        total_pages = math.ceil(total_stories / ITEMS_PER_PAGE)
        
        # 2. Safety Check
        if st.session_state.current_page >= total_pages:
            st.session_state.current_page = 0
            
        start_idx = st.session_state.current_page * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        
        # 3. Slice the data
        page_stories = filtered_stories[start_idx:end_idx]
        
        # 4. Display Info
        st.caption(f"Showing {start_idx+1}-{min(end_idx, total_stories)} of {total_stories} stories")
        
        # 5. Render Stories
        for story in page_stories:
            with st.container():
                c1, c2 = st.columns([1, 3])
                with c1:
                    if story['image']: st.image(story['image'], width="stretch")
                    else: st.markdown("""<div class="img-placeholder">📷 No Image</div>""", unsafe_allow_html=True)
                
                with c2:
                    st.markdown(
                        f"<span class='{story['sentiment_class']}'>{story['sentiment_label']}</span> "
                        f"**{story['source']}** • "
                        f"<span style='color:#AAA; font-size:0.9em'>{story['relative_time']}</span>", 
                        unsafe_allow_html=True
                    )
                    st.subheader(f"[{story['title']}]({story['link']})")
                    if len(story['summary']) > 5: st.markdown(f"<span style='color:#B0B0B0'>{story['summary'][:200]}...</span>", unsafe_allow_html=True)
                    
                    st.write("") 
                    col_a, col_b, col_c = st.columns([1, 1, 1.5])
                    with col_a: st.link_button("🔗 Read", story['link'])
                    with col_b:
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
                            if not gemini_key: st.error("Add API Key!")
                            else:
                                with st.spinner("Writing..."):
                                    st.session_state.generated_copy[story['link']] = generate_single_post(gemini_key, story)
                        if story['link'] in st.session_state.generated_copy:
                            st.code(st.session_state.generated_copy[story['link']], language="markdown")
                st.divider()

        # 6. PAGINATION CONTROLS
        col_prev, col_info, col_next = st.columns([1, 2, 1])
        
        with col_prev:
            if st.session_state.current_page > 0:
                if st.button("⬅️ Previous"):
                    st.session_state.current_page -= 1
                    st.rerun()
        
        with col_info:
            st.markdown(f"<div style='text-align: center; color: #888; padding-top: 5px;'>Page {st.session_state.current_page + 1} of {total_pages}</div>", unsafe_allow_html=True)
            
        with col_next:
            if st.session_state.current_page < total_pages - 1:
                if st.button("Next ➡️"):
                    st.session_state.current_page += 1
                    st.rerun()