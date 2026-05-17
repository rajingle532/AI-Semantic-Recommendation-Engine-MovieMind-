"""
Recommendation routes — content-based, collaborative, and hybrid recommendations.
"""
from fastapi import APIRouter, Depends, HTTPException
from app.utils.security import get_current_user
from app.services.recommender import (
    get_content_recommendations,
    get_hybrid_recommendations,
)
from app.database import get_collection
from app.services.tmdb import get_movie_details
from concurrent.futures import ThreadPoolExecutor

router = APIRouter(prefix="/api/recommend", tags=["Recommendations"])


@router.get("/{movie_id}")
def recommend_similar(movie_id: int, count: int = 10):
    """
    Get similar movies based on content (genres, keywords, cast, overview).
    No authentication required.
    """
    recommendations = get_content_recommendations(movie_id, n=count)
    return {"movie_id": movie_id, "recommendations": recommendations, "count": len(recommendations)}


@router.get("/personal/me")
def recommend_personal(current_user: dict = Depends(get_current_user)):
    """
    Get personalized recommendations using hybrid model (content + collaborative).
    Requires authentication — uses the user's rating history.
    """
    user_id = current_user["user_id"]
    recommendations = get_hybrid_recommendations(user_id)
    return {"recommendations": recommendations, "count": len(recommendations)}


@router.get("/smart/me")
def recommend_smart(n: int = 20, current_user: dict = Depends(get_current_user)):
    """
    Smart personalized recommendations using BOTH watchlist + ratings.
    Builds a genre/keyword taste profile and returns ranked picks.
    """
    user_id = current_user["user_id"]

    ratings_col = get_collection("ratings")
    watchlist_col = get_collection("watchlist")

    user_ratings = list(ratings_col.find({"user_id": user_id}))
    user_watchlist = list(watchlist_col.find({"user_id": user_id}))

    # ── 1. Build taste profile ────────────────────────────────────────
    # Fetch TMDB details for all rated + watchlisted movies in parallel
    all_movie_ids: dict[int, float] = {}  # movie_id -> weight

    for r in user_ratings:
        mid = r.get("movie_id")
        rating = r.get("rating", 5)
        if mid:
            all_movie_ids[mid] = (rating / 5.0) * 1.5  # Ratings weighted 1.5x

    for w in user_watchlist:
        mid = w.get("movie_id")
        if mid and mid not in all_movie_ids:
            all_movie_ids[mid] = 0.8  # Watchlist as implicit 0.8 weight

    if not all_movie_ids:
        # Complete newcomer — return content recs from a popular seed
        return {"recommendations": get_content_recommendations(27205, n=n),
                "profile": None, "source": "cold_start"}

    # Fetch TMDB details in parallel for genre extraction
    genre_weights: dict[str, float] = {}
    keyword_weights: dict[str, float] = {}
    language_weights: dict[str, float] = {}
    seen_ids = set(all_movie_ids.keys())

    def enrich(mid_weight_pair):
        mid, weight = mid_weight_pair
        try:
            details = get_movie_details(mid)
            if not details:
                return None
            genres = [g["name"] for g in (details.get("genres") or [])]
            keywords = [k["name"] for k in (details.get("keywords", {}).get("keywords") or [])]
            lang = details.get("original_language", "")
            return genres, keywords, lang, weight
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=10) as ex:
        enriched = list(ex.map(enrich, all_movie_ids.items()))

    for item in enriched:
        if not item:
            continue
        genres, keywords, lang, weight = item
        for g in genres:
            genre_weights[g] = genre_weights.get(g, 0) + weight
        for k in keywords[:5]:  # Top 5 keywords per movie
            keyword_weights[k] = keyword_weights.get(k, 0) + weight * 0.5
        if lang:
            language_weights[lang] = language_weights.get(lang, 0) + weight

    # Top 3 genres / top language for insight text
    top_genres = sorted(genre_weights, key=genre_weights.get, reverse=True)[:5]  # type: ignore
    top_language = max(language_weights, key=language_weights.get) if language_weights else "en"

    # ── 2. Get content-based recs from top-rated seeds ─────────────────
    sorted_seeds = sorted(all_movie_ids.items(), key=lambda x: x[1], reverse=True)
    seed_ids = [mid for mid, _ in sorted_seeds[:6]]  # Top 6 seeds

    score_map: dict[int, dict] = {}

    def fetch_recs_for_seed(seed_mid_weight):
        seed_mid, seed_weight = seed_mid_weight
        try:
            recs = get_content_recommendations(seed_mid, n=25)
            return recs, seed_weight
        except Exception:
            return [], seed_weight

    seed_pairs = [(mid, all_movie_ids[mid]) for mid in seed_ids]
    with ThreadPoolExecutor(max_workers=6) as ex:
        rec_results = list(ex.map(fetch_recs_for_seed, seed_pairs))

    for recs, seed_weight in rec_results:
        for rec in recs:
            rec_id = rec.get("movie_id") or rec.get("id")
            if not rec_id or rec_id in seen_ids:
                continue
            sim = rec.get("similarity_score", 0.5)
            weighted_score = sim * seed_weight

            if rec_id in score_map:
                score_map[rec_id]["score"] += weighted_score
                score_map[rec_id]["count"] += 1
            else:
                score_map[rec_id] = {
                    "id": rec_id,
                    "movie_id": rec_id,
                    "title": rec.get("title", ""),
                    "poster_path": rec.get("poster_path"),
                    "score": weighted_score,
                    "count": 1,
                }

    # ── 3. Re-rank: boost movies matching taste profile genres ──────────
    # Fetch genres for each candidate
    candidate_ids = list(score_map.keys())

    def boost_rec(mid):
        try:
            details = get_movie_details(mid)
            if not details:
                return mid, 1.0
            rec_genres = [g["name"] for g in (details.get("genres") or [])]
            rec_lang = details.get("original_language", "en")

            genre_boost = sum(genre_weights.get(g, 0) for g in rec_genres)
            lang_boost = 1.15 if rec_lang == top_language else 1.0
            total_boost = 1.0 + (genre_boost * 0.1)
            return mid, total_boost * lang_boost
        except Exception:
            return mid, 1.0

    with ThreadPoolExecutor(max_workers=12) as ex:
        boost_results = dict(ex.map(boost_rec, candidate_ids[:40]))

    for mid, boost in boost_results.items():
        if mid in score_map:
            score_map[mid]["score"] = round(
                (score_map[mid]["score"] / score_map[mid]["count"]) * boost, 4
            )

    # ── 4. Final sort + format ──────────────────────────────────────────
    results = sorted(score_map.values(), key=lambda x: x["score"], reverse=True)

    return {
        "recommendations": [
            {
                "id": r["id"],
                "movie_id": r["movie_id"],
                "title": r["title"],
                "poster_path": r["poster_path"],
                "relevance_score": r["score"],
            }
            for r in results[:n]
        ],
        "profile": {
            "top_genres": top_genres,
            "top_language": top_language,
            "total_inputs": len(all_movie_ids),
            "rated_count": len(user_ratings),
            "watchlist_count": len(user_watchlist),
        },
        "source": "smart_hybrid"
    }

