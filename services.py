import concurrent.futures
import feedparser
import streamlit as st
import re
from google import genai
from utils import get_sentiment, extract_image_url, format_display_date, get_relative_time, parse_date

# --- GEMINI AI ---
def generate_single_post(api_key, story):
    try:
        client = genai.Client(api_key=api_key)
        prompt = f"Write a punchy LinkedIn caption (under 100 words) for: {story['title']} from {story['source']}. Summary: {story['summary']}"
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return response.text
    except Exception as e: return f"Error: {str(e)}"

def generate_newsletter(api_key, stories):
    try:
        client = genai.Client(api_key=api_key)
        stories_text = ""
        for i, s in enumerate(stories):
            stories_text += f"{i+1}. {s['title']} ({s['source']}): {s['summary'][:150]}...\n"
        prompt = f"Write a Morning Briefing newsletter based on these stories:\n{stories_text}\nFormat: Intro, Bullet points, Closing thought."
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return response.text
    except Exception as e: return f"Error: {str(e)}"

# --- DATA FETCHING ---
@st.cache_data(ttl=300, show_spinner=False)
def fetch_feed_data(url, source_name):
    try:
        feed = feedparser.parse(url)
        articles = []
        if hasattr(feed, 'bozo_exception') and feed.bozo_exception:
             # Log warning but attempt to parse anyway
             print(f"Warning parsing {url}: {feed.bozo_exception}")

        articles = []
        for entry in feed.entries[:6]: 
            summary = entry.get('summary', 'No summary.')
            summary = re.sub('<[^<]+?>', '', summary) 
            if "Guardian" in source_name and "<" in summary: summary = summary.split("<")[0]
            
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
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

def fetch_all_feeds(unique_feeds):
    all_stories = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_url = {executor.submit(fetch_feed_data, url, name): name for name, url in unique_feeds}
        
        for future in concurrent.futures.as_completed(future_to_url):
            try:
                stories = future.result()
                all_stories.extend(stories)
            except Exception as e:
                st.error(f"Error fetching feed: {e}")
    return all_stories
