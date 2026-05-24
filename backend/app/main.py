"""
FastAPI Main Entry Point — Movie Recommender System API.
Registers all route modules and configures CORS middleware.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from app.config import settings

# Import route modules
from app.routes import auth, movies, recommend, ratings, watchlist, admin, chat, music, music_ai, tv

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown."""
    from app.services.tmdb import get_genres, get_trending_movies
    import asyncio
    try:
        # Pre-fetch genres and first page of trending movies
        print("Warm-up: Fetching genres and trending movies...")
        await asyncio.gather(
            asyncio.to_thread(get_genres),
            asyncio.to_thread(get_trending_movies, 1)
        )
        print("Warm-up complete.")
    except Exception as e:
        print(f"Warm-up failed: {e}")
    yield

# ═══════════════════════════════════════════
# Create FastAPI App
# ═══════════════════════════════════════════
app = FastAPI(
    title="🎬 Movie Recommender System API",
    description="Full-stack ML-powered movie recommendation engine with hybrid filtering, NLP search, JWT auth, and user interactions.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# ═══════════════════════════════════════════
# CORS Middleware (allow React frontend)
# ═══════════════════════════════════════════
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "https://movies-recommender-system-ten.vercel.app",
        "https://movies-recommender-system-git-main-omkar-ingle-s-projects.vercel.app",
        "https://movies-recommender-system-mrjqv00ji-omkar-ingle-s-projects.vercel.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enable GZip compression for responses > 1KB
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ═══════════════════════════════════════════
# Register Route Modules
# ═══════════════════════════════════════════
app.include_router(auth.router)
app.include_router(movies.router)
app.include_router(recommend.router)
app.include_router(ratings.router)
app.include_router(watchlist.router)
app.include_router(admin.router)
app.include_router(chat.router)
app.include_router(music.router)
app.include_router(music_ai.router)
app.include_router(tv.router)


# ═══════════════════════════════════════════
# Health Check
# ═══════════════════════════════════════════
@app.get("/", tags=["Health"])
def health_check():
    """API health check endpoint."""
    return {
        "status": "healthy",
        "app": "Movie Recommender System API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/api/health", tags=["Health"])
def api_health():
    """Detailed health check with feature status."""
    return {
        "status": "healthy",
        "version": "2.5.0",
        "filters_status": "unified_and_robust",
        "features": {
            "auth": "JWT + bcrypt",
            "recommendations": "Content-based + Hybrid",
            "search": "TMDB title search + NLP semantic search",
            "ratings": "1-5 star system",
            "watchlist": "Personal movie list",
        }
    }
