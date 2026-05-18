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
from app.services.tmdb import get_movie_details, get_movie_poster
from concurrent.futures import ThreadPoolExecutor

router = APIRouter(prefix="/api/recommend", tags=["Recommendations"])


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
    Builds a genre/keyword taste profile and returns genre-boosted ranked picks.
    """
    user_id = current_user["user_id"]

    try:
        ratings_col = get_collection("ratings")
        watchlist_col = get_collection("watchlist")

        user_ratings = list(ratings_col.find({"user_id": user_id}))
        user_watchlist = list(watchlist_col.find({"user_id": user_id}))

        print(f"SMART_REC: user={user_id} | ratings={len(user_ratings)} | watchlist={len(user_watchlist)}")

        # ── 1. Build weighted movie input map ────────────────────────────
        all_movie_ids: dict[int, float] = {}

        for r in user_ratings:
            mid = r.get("movie_id")
            rating = r.get("rating", 5)
            if mid:
                all_movie_ids[int(mid)] = (float(rating) / 5.0) * 1.5

        for w in user_watchlist:
            mid = w.get("movie_id")
            if mid and int(mid) not in all_movie_ids:
                all_movie_ids[int(mid)] = 0.8

        print(f"SMART_REC: unique input movies={len(all_movie_ids)}")

        if not all_movie_ids:
            fallback = get_content_recommendations(27205, n=n)
            return {"recommendations": fallback, "profile": None, "source": "cold_start"}

        # ── 2. Build taste profile via TMDB genre enrichment ────────────
        genre_weights: dict[str, float] = {}
        language_weights: dict[str, float] = {}
        seen_ids = set(all_movie_ids.keys())

        def enrich(pair):
            mid, weight = pair
            try:
                details = get_movie_details(mid)
                if not details:
                    return None
                raw_genres = details.get("genres") or []
                genres = []
                for g in raw_genres:
                    if isinstance(g, dict) and "name" in g:
                        genres.append(g["name"])
                    elif isinstance(g, str):
                        genres.append(g)
                lang = details.get("original_language", "")
                return genres, lang, weight
            except Exception as e:
                print(f"SMART_REC: enrich error for {mid}: {e}")
                return None

        with ThreadPoolExecutor(max_workers=8) as ex:
            enriched = list(ex.map(enrich, all_movie_ids.items()))

        for item in enriched:
            if not item:
                continue
            genres, lang, weight = item
            for g in genres:
                genre_weights[g] = genre_weights.get(g, 0) + weight
            if lang:
                language_weights[lang] = language_weights.get(lang, 0) + weight

        top_genres = sorted(genre_weights, key=lambda k: genre_weights[k], reverse=True)[:5]
        top_language = max(language_weights, key=lambda k: language_weights[k]) if language_weights else "en"

        print(f"SMART_REC: top_genres={top_genres} | top_lang={top_language}")

        # ── 3. Get content recs from top 6 highest-weight seeds ─────────
        seed_pairs = sorted(all_movie_ids.items(), key=lambda x: x[1], reverse=True)[:6]
        score_map: dict[int, dict] = {}

        def fetch_seed(pair):
            seed_mid, seed_weight = pair
            try:
                # fetch_metadata=False for super-fast candidate similarity retrieval
                recs = get_content_recommendations(seed_mid, n=25, fetch_metadata=False)
                return recs, seed_weight
            except Exception:
                return [], seed_weight

        with ThreadPoolExecutor(max_workers=6) as ex:
            rec_results = list(ex.map(fetch_seed, seed_pairs))

        for recs, seed_weight in rec_results:
            for rec in recs:
                rec_id = rec.get("movie_id") or rec.get("id")
                if not rec_id or rec_id in seen_ids:
                    continue
                sim = rec.get("similarity_score", 0.5)
                ws = sim * seed_weight
                if rec_id in score_map:
                    score_map[rec_id]["score"] += ws
                    score_map[rec_id]["count"] += 1
                else:
                    score_map[rec_id] = {
                        "id": rec_id, "movie_id": rec_id,
                        "title": rec.get("title", ""),
                        "poster_path": rec.get("poster_path"),
                        "score": ws, "count": 1,
                    }

        print(f"SMART_REC: candidate pool size={len(score_map)}")

        # ── 4. Retrieve details and apply Genre-boost on top candidates only ──
        top_candidates = sorted(score_map.values(), key=lambda x: x["score"] / x["count"], reverse=True)[:n + 10]
        final_list = []

        def process_candidate(cand):
            mid = cand["movie_id"]
            try:
                # Fetch details (cached or single parallel fast TMDB request)
                details = get_movie_details(mid)
                if details:
                    raw_genres = details.get("genres") or []
                    rec_genres = []
                    for g in raw_genres:
                        if isinstance(g, dict) and "name" in g:
                            rec_genres.append(g["name"])
                        elif isinstance(g, str):
                            rec_genres.append(g)
                    rec_lang = details.get("original_language", "en")
                    genre_boost = sum(genre_weights.get(g, 0) for g in rec_genres)
                    lang_boost = 1.15 if rec_lang == top_language else 1.0
                    
                    boost_multiplier = (1.0 + genre_boost * 0.15) * lang_boost
                    final_score = round((cand["score"] / cand["count"]) * boost_multiplier, 4)
                    
                    return {
                        "id": mid,
                        "movie_id": mid,
                        "title": details.get("title", cand["title"]),
                        "poster_path": details.get("poster_path") or cand["poster_path"],
                        "vote_average": details.get("vote_average", 0.0),
                        "release_date": details.get("release_date", ""),
                        "score": final_score
                    }
            except Exception as e:
                print(f"SMART_REC: process_candidate error for {mid}: {e}")
            
            # Fallback using whatever basic info we have
            fallback_poster = cand.get("poster_path")
            if not fallback_poster:
                try:
                    fallback_poster = get_movie_poster(mid)
                except Exception:
                    fallback_poster = None

            return {
                "id": mid,
                "movie_id": mid,
                "title": cand.get("title", ""),
                "poster_path": fallback_poster,
                "vote_average": 0.0,
                "release_date": "",
                "score": round(cand["score"] / cand["count"], 4)
            }

        with ThreadPoolExecutor(max_workers=10) as ex:
            final_list = [res for res in ex.map(process_candidate, top_candidates) if res is not None]

        # ── 5. Sort and return ───────────────────────────────────────
        final = sorted(final_list, key=lambda x: x["score"], reverse=True)
        print(f"SMART_REC: returning {min(len(final), n)} recommendations")

        return {
            "recommendations": [
                {"id": r["id"], "movie_id": r["movie_id"], "title": r["title"],
                 "poster_path": r["poster_path"], "relevance_score": r["score"]}
                for r in final[:n]
            ],
            "profile": {
                "top_genres": top_genres,
                "top_language": top_language,
                "total_inputs": len(all_movie_ids),
                "rated_count": len(user_ratings),
                "watchlist_count": len(user_watchlist),
            },
            "source": "smart_hybrid",
        }

    except Exception as e:
        print(f"SMART_REC ERROR: {e}")
        import traceback; traceback.print_exc()
        fallback = get_content_recommendations(27205, n=n)
        return {"recommendations": fallback, "profile": None, "source": "error_fallback"}


@router.get("/debug/me", tags=["Health"])
def recommend_debug(email: str = "ingleraj79@gmail.com"):
    logs = []
    def log(msg):
        logs.append(msg)
        print(f"DEBUG_ROUTE: {msg}")

    log("Starting debug recommendations")
    try:
        users_col = get_collection("users")
        user = users_col.find_one({"email": email})
        if not user:
            log(f"User not found for email: {email}")
            return {"logs": logs, "status": "failed"}

        user_id = str(user["_id"])
        log(f"Found User ID: {user_id}")

        ratings_col = get_collection("ratings")
        watchlist_col = get_collection("watchlist")

        user_ratings = list(ratings_col.find({"user_id": user_id}))
        user_watchlist = list(watchlist_col.find({"user_id": user_id}))

        log(f"Ratings: {len(user_ratings)} | Watchlist: {len(user_watchlist)}")

        all_movie_ids = {}
        for r in user_ratings:
            mid = r.get("movie_id")
            if mid:
                all_movie_ids[int(mid)] = float(r.get("rating", 3.0))

        for w in user_watchlist:
            mid = w.get("movie_id")
            if mid:
                mid = int(mid)
                all_movie_ids[mid] = all_movie_ids.get(mid, 3.0) + 1.0

        log(f"Unique movie IDs: {len(all_movie_ids)}")

        if not all_movie_ids:
            log("No movies found, using cold start fallback")
            fallback = get_content_recommendations(27205, n=20)
            return {"logs": logs, "status": "cold_start", "count": len(fallback)}

        log("Step 1: Enriching taste profile")
        genre_weights = {}
        language_weights = {}
        seen_ids = set(all_movie_ids.keys())

        for mid, weight in list(all_movie_ids.items()):
            try:
                details = get_movie_details(mid)
                if not details:
                    log(f"No details found for {mid}")
                    continue
                raw_genres = details.get("genres") or []
                genres = []
                for g in raw_genres:
                    if isinstance(g, dict) and "name" in g:
                        genres.append(g["name"])
                    elif isinstance(g, str):
                        genres.append(g)
                lang = details.get("original_language", "")
                log(f"Movie {mid}: genres={genres} | lang={lang}")
                
                for g in genres:
                    genre_weights[g] = genre_weights.get(g, 0) + weight
                if lang:
                    language_weights[lang] = language_weights.get(lang, 0) + weight
            except Exception as e:
                log(f"Error enriching {mid}: {e}")

        top_genres = sorted(genre_weights, key=lambda k: genre_weights[k], reverse=True)[:5]
        top_language = max(language_weights, key=lambda k: language_weights[k]) if language_weights else "en"
        log(f"Top Genres: {top_genres} | Top Language: {top_language}")

        log("Step 2: Candidate Generation from top seeds")
        seed_pairs = sorted(all_movie_ids.items(), key=lambda x: x[1], reverse=True)[:6]
        score_map = {}

        for seed_mid, seed_weight in seed_pairs:
            try:
                log(f"Fetching similarity recommendations for seed {seed_mid} (weight={seed_weight})")
                recs = get_content_recommendations(seed_mid, n=25, fetch_metadata=False)
                log(f"Seed {seed_mid} returned {len(recs)} candidates")
                for rec in recs:
                    rec_id = rec.get("movie_id") or rec.get("id")
                    if not rec_id or rec_id in seen_ids:
                        continue
                    sim = rec.get("similarity_score", 0.5)
                    ws = sim * seed_weight
                    if rec_id in score_map:
                        score_map[rec_id]["score"] += ws
                        score_map[rec_id]["count"] += 1
                    else:
                        score_map[rec_id] = {
                            "id": rec_id, "movie_id": rec_id,
                            "title": rec.get("title", ""),
                            "poster_path": rec.get("poster_path"),
                            "score": ws, "count": 1,
                        }
            except Exception as e:
                log(f"Error in seed {seed_mid}: {e}")

        log(f"Candidate pool size: {len(score_map)}")
        top_candidates = sorted(score_map.values(), key=lambda x: x["score"] / x["count"], reverse=True)[:30]
        log(f"Top candidates subset size: {len(top_candidates)}")

        log("Step 3: Process top candidates")
        final_list = []
        for cand in top_candidates:
            mid = cand["movie_id"]
            try:
                log(f"Processing candidate {mid} ({cand['title']})")
                details = get_movie_details(mid)
                if details:
                    raw_genres = details.get("genres") or []
                    rec_genres = []
                    for g in raw_genres:
                        if isinstance(g, dict) and "name" in g:
                            rec_genres.append(g["name"])
                        elif isinstance(g, str):
                            rec_genres.append(g)
                    rec_lang = details.get("original_language", "en")
                    genre_boost = sum(genre_weights.get(g, 0) for g in rec_genres)
                    lang_boost = 1.15 if rec_lang == top_language else 1.0
                    boost_multiplier = (1.0 + genre_boost * 0.15) * lang_boost
                    final_score = round((cand["score"] / cand["count"]) * boost_multiplier, 4)
                    
                    final_list.append({
                        "id": mid, "movie_id": mid,
                        "title": details.get("title", cand["title"]),
                        "poster_path": details.get("poster_path") or cand["poster_path"],
                        "score": final_score
                    })
                    log(f"Candidate {mid} processed: boost={boost_multiplier:.2f} | score={final_score}")
                else:
                    log(f"No details found for candidate {mid}, using fallback")
                    final_list.append({
                        "id": mid, "movie_id": mid,
                        "title": cand["title"],
                        "poster_path": cand.get("poster_path"),
                        "score": round(cand["score"] / cand["count"], 4)
                    })
            except Exception as e:
                log(f"Error processing candidate {mid}: {e}")

        final = sorted(final_list, key=lambda x: x["score"], reverse=True)
        log(f"Successfully generated {len(final)} recommendations")

        return {
            "status": "success",
            "logs": logs,
            "profile": {
                "top_genres": top_genres,
                "top_language": top_language
            },
            "recommendations": final[:20]
        }

    except Exception as e:
        log(f"CRITICAL ERROR: {e}")
        import traceback
        log(traceback.format_exc())
        return {"status": "failed", "logs": logs}


# ── IMPORTANT: Keep this LAST — wildcard catches anything not matched above ──
@router.get("/{movie_id}")
def recommend_similar(movie_id: int, count: int = 10):
    """
    Get similar movies based on content (genres, keywords, cast, overview).
    No authentication required. Must be declared AFTER all named routes.
    """
    recommendations = get_content_recommendations(movie_id, n=count)
    return {"movie_id": movie_id, "recommendations": recommendations, "count": len(recommendations)}
