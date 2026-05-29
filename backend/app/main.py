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
from app.routes import auth, movies, recommend, ratings, watchlist, admin, chat, music, music_ai, tv, tickets

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown."""
    from app.services.tmdb import get_genres, get_trending_movies
    import asyncio
    import httpx
    
    # Keep-alive background task
    async def keep_alive_task():
        # Only run on production/cloud environments if configured, or just run silently
        import os
        if os.getenv("ENVIRONMENT", "").lower() not in {"production", "prod"}:
            return
            
        async with httpx.AsyncClient() as client:
            while True:
                await asyncio.sleep(600)  # 10 minutes
                try:
                    port = os.getenv("PORT", "8000")
                    await client.get(f"http://127.0.0.1:{port}/api/health")
                except Exception:
                    pass

    task = None
    try:
        # Pre-fetch genres and first page of trending movies
        print("Warm-up: Fetching genres and trending movies...")
        await asyncio.gather(
            asyncio.to_thread(get_genres),
            asyncio.to_thread(get_trending_movies, 1)
        )
        print("Warm-up complete.")
        
        task = asyncio.create_task(keep_alive_task())
    except Exception as e:
        print(f"Warm-up failed: {e}")
    yield
    if task is not None:
        try:
            task.cancel()
        except Exception:
            pass

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
app.include_router(tickets.router)


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
