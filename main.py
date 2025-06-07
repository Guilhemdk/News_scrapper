import datetime
from filter_module import filter_articles


def main():
    # Example articles
    articles = [
        {
            "title": "New AI chip launched",
            "content": "This technology could change the future.",
            "region": "US",
            "published_at": datetime.datetime.utcnow().isoformat(),
        },
        {
            "title": "Health benefits of meditation",
            "content": "Experts share the positives of daily meditation.",
            "region": "EU",
            "published_at": datetime.datetime.utcnow().isoformat(),
        },
    ]

    result = filter_articles(
        articles,
        categories=["tech", "health"],
        sentiments=["positive", "neutral"],
        regions=["US", "EU"],
        since_hours=24,
    )

    for art in result:
        print({
            "title": art["title"],
            "category": art["category"],
            "sentiment": art["sentiment"],
            "region": art["region"],
        })


if __name__ == "__main__":
    main()
