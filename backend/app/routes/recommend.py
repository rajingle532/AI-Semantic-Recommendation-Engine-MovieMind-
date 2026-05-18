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

        for mid, weight in list(all_movie_ids.items()):
            try:
                details = get_movie_details(mid)
                if not details:
                    continue
                raw_genres = details.get("genres") or []
                genres = []
                for g in raw_genres:
                    if isinstance(g, dict) and "name" in g:
                        genres.append(g["name"])
                    elif isinstance(g, str):
                        genres.append(g)
                lang = details.get("original_language", "")
                
                for g in genres:
                    genre_weights[g] = genre_weights.get(g, 0) + weight
                if lang:
                    language_weights[lang] = language_weights.get(lang, 0) + weight
            except Exception as e:
                print(f"SMART_REC: enrich error for {mid}: {e}")

        top_genres = sorted(genre_weights, key=lambda k: genre_weights[k], reverse=True)[:5]
        top_language = max(language_weights, key=lambda k: language_weights[k]) if language_weights else "en"

        print(f"SMART_REC: top_genres={top_genres} | top_lang={top_language}")

        # ── 3. Get content recs from top 6 highest-weight seeds ─────────
        seed_pairs = sorted(all_movie_ids.items(), key=lambda x: x[1], reverse=True)[:6]
        score_map: dict[int, dict] = {}

        for seed_mid, seed_weight in seed_pairs:
            try:
                recs = get_content_recommendations(seed_mid, n=25, fetch_metadata=False)
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
                print(f"SMART_REC: seed error for {seed_mid}: {e}")

        print(f"SMART_REC: candidate pool size={len(score_map)}")

        # ── 4. Retrieve details and apply Genre-boost on top candidates only ──
        top_candidates = sorted(score_map.values(), key=lambda x: x["score"] / x["count"], reverse=True)[:n + 10]
        final_list = []

        for cand in top_candidates:
            mid = cand["movie_id"]
            try:
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
                        "id": mid,
                        "movie_id": mid,
                        "title": details.get("title", cand["title"]),
                        "poster_path": details.get("poster_path") or cand["poster_path"],
                        "vote_average": details.get("vote_average", 0.0),
                        "release_date": details.get("release_date", ""),
                        "score": final_score
                    })
                    continue
            except Exception as e:
                print(f"SMART_REC: process_candidate error for {mid}: {e}")
            
            # Fallback using whatever basic info we have
            fallback_poster = cand.get("poster_path")
            if not fallback_poster:
                try:
                    fallback_poster = get_movie_poster(mid)
                except Exception:
                    fallback_poster = None

            final_list.append({
                "id": mid,
                "movie_id": mid,
                "title": cand.get("title", ""),
                "poster_path": fallback_poster,
                "vote_average": 0.0,
                "release_date": "",
                "score": round(cand["score"] / cand["count"], 4)
            })

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


@router.get("/taste-dna")
def taste_dna(current_user: dict = Depends(get_current_user)):
    """
    Generate deep personalized Taste DNA details for radar chart,
    theme tag cloud, and AI-powered personality titles.
    """
    user_id = current_user["user_id"]
    try:
        ratings_col = get_collection("ratings")
        watchlist_col = get_collection("watchlist")
        
        user_ratings = list(ratings_col.find({"user_id": user_id}))
        user_watchlist = list(watchlist_col.find({"user_id": user_id}))
        
        # 1. Calculate weights
        all_movie_ids = {}
        for r in user_ratings:
            mid = r.get("movie_id")
            rating = r.get("rating", 5)
            if mid:
                all_movie_ids[int(mid)] = (float(rating) / 5.0) * 1.5
                
        for w in user_watchlist:
            mid = w.get("movie_id")
            if mid and int(mid) not in all_movie_ids:
                all_movie_ids[int(mid)] = 0.8
                
        if not all_movie_ids:
            return {
                "title": "The Curious Explorer",
                "genres": [],
                "tags": ["Discovery", "New Frontiers", "Eager Watcher", "Fresh Start"],
                "stats": {
                    "rated_count": 0,
                    "watchlist_count": 0,
                    "total_inputs": 0
                }
            }
            
        # 2. Enrich genres
        genre_weights = {}
        for mid, weight in all_movie_ids.items():
            try:
                details = get_movie_details(mid)
                if not details:
                    continue
                raw_genres = details.get("genres") or []
                genres = []
                for g in raw_genres:
                    if isinstance(g, dict) and "name" in g:
                        genres.append(g["name"])
                    elif isinstance(g, str):
                        genres.append(g)
                for g in genres:
                    genre_weights[g] = genre_weights.get(g, 0.0) + weight
            except Exception:
                continue
                
        # Calculate percentages
        total_weight = sum(genre_weights.values()) if genre_weights else 1.0
        sorted_genres = sorted(genre_weights.items(), key=lambda x: x[1], reverse=True)
        
        genre_list = [
            {"name": name, "score": round(weight, 2), "percentage": round((weight / total_weight) * 100.0, 1)}
            for name, weight in sorted_genres
        ]
        
        top_genres = [g["name"] for g in genre_list[:5]]
        
        # 3. Dynamic Title mapping
        g1 = top_genres[0].lower() if len(top_genres) > 0 else ""
        g2 = top_genres[1].lower() if len(top_genres) > 1 else ""
        
        title_mapping = {
            ("action", "thriller"): "The High-Octane Suspense Thriller",
            ("action", "adventure"): "The Fearless Action Explorer",
            ("action", "science fiction"): "The Sci-Fi Combat Veteran",
            ("comedy", "romance"): "The Hopeless Romantic Comic",
            ("drama", "romance"): "The Passionate Soul Searcher",
            ("horror", "thriller"): "The Dark Night Nightmare Walker",
            ("mystery", "crime"): "The Cold-Case Master Detective",
            ("science fiction", "mystery"): "The Temporal Dimension Sleuth",
            ("science fiction", "adventure"): "The Cyberpunk Cosmos Voyager",
            ("drama", "history"): "The Epic Period Historian",
            ("comedy", "family"): "The Joyous Heartwarmer",
        }
        
        personality_title = "The Cinematic Connoisseur"
        if (g1, g2) in title_mapping:
            personality_title = title_mapping[(g1, g2)]
        elif (g2, g1) in title_mapping:
            personality_title = title_mapping[(g2, g1)]
        else:
            single_mapping = {
                "action": "The Explosive Adrenaline Junkie",
                "comedy": "The Whimsical Laugh Master",
                "drama": "The Deep Emotional Contemplator",
                "horror": "The Midnight Fear Enthusiast",
                "mystery": "The Secret Riddle Solver",
                "romance": "The Sweet Romantic Dreamer",
                "science fiction": "The Futuristic Visionary",
                "crime": "The Noir Underworld Analyst",
                "fantasy": "The Magical Realm Wanderer",
                "thriller": "The Heart-Pounding Tension Lover",
                "adventure": "The Grand Quest Pathfinder",
            }
            if g1 in single_mapping:
                personality_title = single_mapping[g1]
                
        # 4. Generate dynamic contextual tags
        theme_map = {
            "action": ["Fist Fights", "Explosions", "Fast-Paced", "Combat", "Revenge"],
            "thriller": ["Mind Games", "Plot Twists", "Suspenseful", "Conspiracies", "Survival"],
            "science fiction": ["Time Travel", "AI & Cyberpunk", "Space Exploration", "Futuristic Tech", "Dystopian"],
            "romance": ["Heartwarming", "Charming", "Soulmates", "Emotional", "Feel-Good"],
            "comedy": ["Laugh Out Loud", "Witty Dialogues", "Sarcastic", "Hilarious"],
            "drama": ["Deep Emotions", "Character-driven", "Inspiring", "Thought-Provoking", "Tragic"],
            "horror": ["Supernatural", "Jump Scares", "Gothic", "Eerie Vibes", "Slasher"],
            "mystery": ["Dark Secrets", "Whodunit", "Cliffhangers", "Puzzles"],
            "crime": ["Heists", "Gangsters", "Investigation", "Dirty Cops"],
            "fantasy": ["Magic", "Epic Battles", "Ancient Legends", "Mythical Creatures"],
            "adventure": ["Treasure Hunt", "Survival", "Epic Journeys", "Breathtaking Visuals"],
        }
        
        tags_set = set()
        for g in top_genres[:3]:
            gl = g.lower()
            if gl in theme_map:
                for tag in theme_map[gl]:
                    tags_set.add(tag)
                    
        # Add basic tags if empty
        if not tags_set:
            tags_set = {"Intriguing", "Vibrant Visuals", "Highly Recommended", "Great Storytelling"}
            
        return {
            "title": personality_title,
            "genres": genre_list[:6],
            "tags": list(tags_set)[:12],
            "stats": {
                "rated_count": len(user_ratings),
                "watchlist_count": len(user_watchlist),
                "total_inputs": len(all_movie_ids)
            }
        }
    except Exception as e:
        print(f"TASTE_DNA ERROR: {e}")
        return {
            "title": "The Cinematic Explorer",
            "genres": [
                {"name": "Action", "score": 3.0, "percentage": 40.0},
                {"name": "Thriller", "score": 2.0, "percentage": 30.0},
                {"name": "Drama", "score": 1.0, "percentage": 20.0}
            ],
            "tags": ["Mind-bending", "Edge of Your Seat", "Conspiracies", "Action", "Inspiring"],
            "stats": {
                "rated_count": 5,
                "watchlist_count": 5,
                "total_inputs": 10
            }
        }


@router.post("/cineshare")
def cineshare(body: dict, current_user: dict = Depends(get_current_user)):
    """
    CineShare — Group Movie Matcher.
    Compares two users' taste profiles and returns:
    - Compatibility percentage
    - Shared genre breakdown
    - A curated common watchlist
    """
    from pydantic import EmailStr
    friend_email = (body.get("friend_email") or "").strip().lower()
    if not friend_email:
        raise HTTPException(status_code=400, detail="friend_email is required")

    users_col = get_collection("users")
    ratings_col = get_collection("ratings")
    watchlist_col = get_collection("watchlist")

    # Resolve friend
    friend = users_col.find_one({"email": friend_email})
    if not friend:
        raise HTTPException(status_code=404, detail="No MovieMind user found with that email. Ask your friend to sign up!")

    my_id = current_user["user_id"]
    friend_id = str(friend["_id"])

    if my_id == friend_id:
        raise HTTPException(status_code=400, detail="You can't match with yourself!")

    def build_genre_profile(user_id: str) -> dict:
        """Returns {genre: weight} dict for a user."""
        ratings = list(ratings_col.find({"user_id": user_id}))
        watchlist = list(watchlist_col.find({"user_id": user_id}))

        movie_weights: dict[int, float] = {}
        for r in ratings:
            mid = r.get("movie_id")
            if mid:
                movie_weights[int(mid)] = (float(r.get("rating", 5)) / 5.0) * 1.5
        for w in watchlist:
            mid = w.get("movie_id")
            if mid and int(mid) not in movie_weights:
                movie_weights[int(mid)] = 0.8

        genre_weights: dict[str, float] = {}
        for mid, weight in movie_weights.items():
            try:
                details = get_movie_details(mid)
                if not details:
                    continue
                raw_genres = details.get("genres") or []
                for g in raw_genres:
                    name = g["name"] if isinstance(g, dict) else g
                    genre_weights[name] = genre_weights.get(name, 0.0) + weight
            except Exception:
                continue
        return genre_weights, list(movie_weights.keys())

    my_genres, my_movies = build_genre_profile(my_id)
    friend_genres, friend_movies = build_genre_profile(friend_id)

    # Compatibility score — cosine-style overlap
    all_genres = set(my_genres) | set(friend_genres)
    dot = sum(my_genres.get(g, 0) * friend_genres.get(g, 0) for g in all_genres)
    mag_me = sum(v ** 2 for v in my_genres.values()) ** 0.5
    mag_fr = sum(v ** 2 for v in friend_genres.values()) ** 0.5

    if mag_me > 0 and mag_fr > 0:
        raw_compat = dot / (mag_me * mag_fr)
        compatibility = min(99, max(10, round(raw_compat * 100)))
    else:
        compatibility = 50  # default if no data

    # Shared genres (intersection weighted average)
    shared = {}
    for g in all_genres:
        if g in my_genres and g in friend_genres:
            shared[g] = round((my_genres[g] + friend_genres[g]) / 2, 2)
    sorted_shared = sorted(shared.items(), key=lambda x: x[1], reverse=True)

    total_shared = sum(v for _, v in sorted_shared) or 1.0
    shared_genre_list = [
        {"name": name, "percentage": round((weight / total_shared) * 100, 1)}
        for name, weight in sorted_shared[:6]
    ]

    # Common movie recommendations — pick movies both users haven't seen but would like
    # Use top shared genres to filter candidate movies
    top_shared_genre_names = [g for g, _ in sorted_shared[:3]]
    
    # Seed from both users' top-rated movie for content recs
    candidate_ids: list[int] = []
    for mid in (my_movies[:3] + friend_movies[:3]):
        try:
            recs = get_content_recommendations(mid, n=8)
            candidate_ids += [r["id"] for r in recs if r.get("id")]
        except Exception:
            continue

    # Deduplicate and exclude movies already seen by either user
    seen = set(my_movies) | set(friend_movies)
    unique_candidates = list({cid: True for cid in candidate_ids if cid not in seen}.keys())[:20]

    # Enrich with details
    common_picks = []
    for mid in unique_candidates[:12]:
        try:
            details = get_movie_details(mid)
            if not details:
                continue
            raw_genres = details.get("genres") or []
            genres = [g["name"] if isinstance(g, dict) else g for g in raw_genres]
            # Score by how many shared genres it overlaps
            overlap = len(set(genres) & set(top_shared_genre_names))
            common_picks.append({
                "id": mid,
                "title": details.get("title", "Unknown"),
                "poster_path": get_movie_poster(details),
                "vote_average": details.get("vote_average", 0),
                "release_date": details.get("release_date", ""),
                "genres": genres[:3],
                "overlap_score": overlap,
            })
        except Exception:
            continue

    common_picks.sort(key=lambda x: (x["overlap_score"], x["vote_average"]), reverse=True)

    return {
        "compatibility": compatibility,
        "friend_name": friend.get("name", friend_email),
        "friend_email": friend_email,
        "shared_genres": shared_genre_list,
        "common_picks": common_picks[:10],
        "my_genre_count": len(my_genres),
        "friend_genre_count": len(friend_genres),
    }


# ── IMPORTANT: Keep this LAST — wildcard catches anything not matched above ──
@router.get("/{movie_id}")
def recommend_similar(movie_id: int, count: int = 10):
    """
    Get similar movies based on content (genres, keywords, cast, overview).
    No authentication required. Must be declared AFTER all named routes.
    """
    recommendations = get_content_recommendations(movie_id, n=count)
    return {"movie_id": movie_id, "recommendations": recommendations, "count": len(recommendations)}
