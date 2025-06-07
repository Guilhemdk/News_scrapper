# Seed URL generator for news articles
import requests
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from email.utils import parsedate_to_datetime


def fetch_google_news(keyword: str, region: str = 'US') -> List[Dict]:
    """Fetch news results from Google News RSS feed for the last 24 hours."""
    # Build URL for Google News RSS. region uses 'hl' (language-region) and 'gl' country.
    url = (
        f"https://news.google.com/rss/search?q={keyword}+when:1d&hl=en-{region}&gl={region}&ceid={region}:en"
    )
    feed = feedparser.parse(url)
    return [
        {
            'title': entry.get('title'),
            'url': entry.get('link'),
            'published': entry.get('published'),
            'source': 'Google News'
        }
        for entry in feed.entries
    ]


def fetch_rss_feed(rss_url: str) -> List[Dict]:
    """Parse RSS feed and return entries."""
    feed = feedparser.parse(rss_url)
    results = []
    for entry in feed.entries:
        results.append(
            {
                'title': entry.get('title'),
                'url': entry.get('link'),
                'published': entry.get('published'),
                'source': feed.feed.get('title', rss_url)
            }
        )
    return results


def deduplicate_entries(entries: List[Dict]) -> List[Dict]:
    """Remove duplicate entries based on URL."""
    seen = set()
    unique = []
    for entry in entries:
        url = entry['url']
        if url not in seen:
            seen.add(url)
            unique.append(entry)
    return unique


def filter_fresh_entries(entries: List[Dict]) -> List[Dict]:
    """Keep only entries from the last 24 hours."""
    fresh = []
    cutoff = datetime.utcnow() - timedelta(days=1)
    for entry in entries:
        try:
            published = parsedate_to_datetime(entry['published'])
            if published.tzinfo is not None:
                published = published.astimezone(tz=None).replace(tzinfo=None)
        except Exception:
            if 'published_parsed' in entry and entry['published_parsed']:
                published = datetime(*entry['published_parsed'][:6])
            else:
                fresh.append(entry)
                continue
        if published >= cutoff:
            fresh.append(entry)
    return fresh





DEFAULT_RSS_FEEDS = [
    'https://rss.cnn.com/rss/edition.rss',
    'https://feeds.bbci.co.uk/news/world/rss.xml',
    'https://rss.nytimes.com/services/xml/rss/nyt/World.xml',
]


def generate_seed_urls(
    keywords: List[str],
    categories: Optional[List[str]] = None,
    region: str = 'US',
    extra_feeds: Optional[List[str]] = None
) -> Dict:
    """Generate seed URLs using Google News search and RSS feeds.

    Returns a dict with article details and list of URLs.
    """
    all_entries = []
    for kw in keywords:
        all_entries.extend(fetch_google_news(kw, region=region))

    rss_feeds = DEFAULT_RSS_FEEDS.copy()
    if extra_feeds:
        rss_feeds.extend(extra_feeds)

    for feed_url in rss_feeds:
        all_entries.extend(fetch_rss_feed(feed_url))

    # Filter by categories if provided (simple keyword match)
    if categories:
        filtered = []
        for entry in all_entries:
            title_lower = entry['title'].lower() if entry['title'] else ''
            if any(cat.lower() in title_lower for cat in categories):
                filtered.append(entry)
        all_entries = filtered

    # Deduplicate and filter by freshness
    all_entries = deduplicate_entries(all_entries)
    all_entries = filter_fresh_entries(all_entries)

    urls = [entry['url'] for entry in all_entries if entry.get('url')]
    return {
        'articles': all_entries,
        'urls': urls
    }


if __name__ == '__main__':
    result = generate_seed_urls(['technology'], categories=['tech'])
    print(result)
