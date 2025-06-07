import datetime
from typing import List, Dict, Optional

from transformers import pipeline

# Instantiate pipelines lazily so they load only when needed
_zero_shot = None
_sentiment = None


def _get_zero_shot():
    global _zero_shot
    if _zero_shot is None:
        _zero_shot = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    return _zero_shot


def _get_sentiment():
    global _sentiment
    if _sentiment is None:
        _sentiment = pipeline("sentiment-analysis")
    return _sentiment


def classify_category(text: str, candidate_labels: List[str]) -> str:
    """Classify text into one of the candidate labels using zero-shot classification."""
    clf = _get_zero_shot()
    result = clf(text, candidate_labels)
    return result["labels"][0]


def classify_sentiment(text: str) -> str:
    """Return sentiment label for text."""
    clf = _get_sentiment()
    result = clf(text)[0]
    return result["label"].lower()


def filter_articles(
    articles: List[Dict],
    categories: Optional[List[str]] = None,
    sentiments: Optional[List[str]] = None,
    regions: Optional[List[str]] = None,
    since_hours: int = 24,
) -> List[Dict]:
    """Filter articles by categories, sentiments, regions and publication time."""

    filtered = []
    now = datetime.datetime.utcnow()
    since_delta = datetime.timedelta(hours=since_hours)

    for art in articles:
        # time filter
        published = art.get("published_at")
        if published is None:
            continue
        if isinstance(published, str):
            try:
                published_dt = datetime.datetime.fromisoformat(published)
            except ValueError:
                continue
        else:
            published_dt = published

        if now - published_dt > since_delta:
            continue

        # region filter
        if regions is not None and art.get("region") not in regions:
            continue

        # sentiment filter
        if sentiments is not None:
            sent = classify_sentiment(art.get("content", ""))
            if sent not in sentiments:
                continue
            art["sentiment"] = sent
        else:
            art["sentiment"] = classify_sentiment(art.get("content", ""))

        # category filter
        if categories is not None:
            category = classify_category(art.get("title", ""), categories)
            if category not in categories:
                continue
            art["category"] = category
        else:
            art["category"] = classify_category(art.get("title", ""), ["tech", "health", "other"])

        filtered.append(art)

    return filtered
