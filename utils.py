import time
import re
from datetime import datetime
from textblob import TextBlob

# --- HELPER FUNCTIONS ---
def get_sentiment(text):
    try:
        blob = TextBlob(text)
        score = blob.sentiment.polarity
        if score > 0.1: return "Positive", "badge-pos", "🟢 Good News"
        elif score < -0.1: return "Negative", "badge-neg", "🔴 Crisis/Issue"
        else: return "Neutral", "badge-neu", "⚪ Neutral"
    except: return "Neutral", "badge-neu", "⚪ Neutral"

def extract_image_url(entry):
    if hasattr(entry, 'media_content'):
        for media in entry.media_content:
            if media.get('medium') == 'image' or media.get('type', '').startswith('image'):
                return media['url']
    if hasattr(entry, 'media_thumbnail'):
         if entry.media_thumbnail: return entry.media_thumbnail[0]['url']
    if hasattr(entry, 'enclosures'):
        for enclosure in entry.enclosures:
            if enclosure.get('type', '').startswith('image'): return enclosure['href']
    if hasattr(entry, 'summary'):
        img_match = re.search(r'<img[^>]+src="([^">]+)"', entry.summary)
        if img_match: return img_match.group(1)
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
