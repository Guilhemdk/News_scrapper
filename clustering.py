from typing import List, Dict

from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import numpy as np
import json


def cluster_articles(articles: List[Dict], min_k: int = 2, max_k: int = 10) -> List[Dict]:
    if not articles:
        return []

    summaries = [article["summary"] for article in articles]

    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(summaries)

    max_k = max(min(max_k, len(articles)), min_k)
    possible_ks = range(min_k, max_k + 1)
    best_k = min_k
    best_score = -1

    for k in possible_ks:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init="auto")
        labels = kmeans.fit_predict(embeddings)
        if len(set(labels)) == 1:
            continue
        score = silhouette_score(embeddings, labels)
        if score > best_score:
            best_score = score
            best_k = k

    kmeans = KMeans(n_clusters=best_k, random_state=42, n_init="auto")
    labels = kmeans.fit_predict(embeddings)

    clusters = []
    for cluster_id in range(best_k):
        indices = np.where(labels == cluster_id)[0]
        cluster_embeds = embeddings[indices]
        centroid = kmeans.cluster_centers_[cluster_id]
        distances = np.linalg.norm(cluster_embeds - centroid, axis=1)
        rep_idx = indices[int(np.argmin(distances))]
        rep_article = articles[rep_idx]
        clusters.append({
            "cluster_id": int(cluster_id),
            "representative_headline": rep_article.get("headline", ""),
            "representative_summary": rep_article.get("summary", ""),
            "articles": [articles[i]["id"] for i in indices]
        })

    return clusters


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python clustering.py path_to_articles.json")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        data = json.load(f)

    result = cluster_articles(data)
    print(json.dumps(result, indent=2))
