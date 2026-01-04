import requests
import subprocess
import concurrent.futures
import feedparser
import streamlit as st
import re
import cloudscraper
from google import genai
from utils import get_sentiment, extract_image_url, format_display_date, get_relative_time, parse_date

# --- HELPERS ---
def fetch_content_robust(url):
    """
    Attempts to fetch content/RSS XML from a URL using multiple methods 
    to bypass bot protection (Cloudflare, etc.).
    """
    # Method 1: Cloudscraper (Best for Cloudflare)
    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get(url, timeout=15)
        if response.status_code == 200:
            return response.content
    except Exception as e:
        print(f"[Cloudscraper] Failed for {url}: {e}")

    # Method 2: Requests (Standard)
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.content
    except Exception as e:
        print(f"[Requests] Failed for {url}: {e}")

    # Method 3: Curl (Last Resort)
    try:
        result = subprocess.run(
            ["curl", "-L", "-A", "Mozilla/5.0", url],
            capture_output=True,
            timeout=15
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout
    except Exception as e:
        print(f"[Curl] Failed for {url}: {e}")
        
    return None

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
        # Robust fetch
        content = fetch_content_robust(url)
        
        if content:
             feed = feedparser.parse(content)
        else:
             # Last resort: let feedparser try (though it likely failed already)
             feed = feedparser.parse(url)

        if hasattr(feed, 'bozo_exception') and feed.bozo_exception:
             # Log warning but attempt to parse anyway
             print(f"Warning parsing {url}: {feed.bozo_exception}")

        articles = []
        for entry in feed.entries[:10]: 
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
