import feedparser
import requests

url = "https://www.theafricareport.com/feed/"

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
}

print(f"\n--- Attempt 3: Fetching {url} via REQUESTS ---")
try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Response Status: {response.status_code}")
    if response.status_code == 200:
        d = feedparser.parse(response.content)
        print(f"Entries found: {len(d.entries)}")
        if len(d.entries) > 0:
            print(f"First title: {d.entries[0].title}")
    else:
        print("Failed to fetch via requests.")
except Exception as e:
    print(f"Request Error: {e}")

