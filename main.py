def main(path: str) -> None:
    import json
    from clustering import cluster_articles

    with open(path, 'r', encoding='utf-8') as f:
        articles = json.load(f)
    clusters = cluster_articles(articles)
    print(json.dumps(clusters, indent=2))


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print('Usage: python main.py path_to_articles.json')
        sys.exit(1)
    main(sys.argv[1])
