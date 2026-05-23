# MovieMind AI

![MovieMind AI Banner](https://raw.githubusercontent.com/rajingle532/AI-Semantic-Recommendation-Engine-MovieMind-/main/docs/assets/banner.png)

MovieMind AI is a full-stack movie discovery platform with a React/Vite frontend, FastAPI backend, MongoDB persistence, TMDB metadata, and AI-assisted recommendations.

## Features

- Personalized movie recommendations based on user ratings and watchlist activity.
- TMDB-powered movie, TV, cast, trailer, and provider metadata.
- JWT authentication with optional Google OAuth.
- Watchlist, ratings, profile, account, and recommendation flows.
- Optional Gemini, search, YouTube, Spotify, and email integrations.
- Docker Compose setup for local MongoDB, backend, and frontend services.

## Stack

- Frontend: React 18, Vite, TypeScript, Framer Motion, Lucide React, CSS modules.
- Backend: FastAPI, Uvicorn, PyMongo, JWT, bcrypt.
- Data and ML: Pandas, NumPy, scikit-learn, NLTK, saved recommendation models.
- Testing: Vitest, Testing Library, Playwright, pytest.

## Local Setup

1. Copy `.env.example` to `.env` for local backend runs.
2. For Docker Compose, copy `.env.example` to `backend/.env`.
3. Copy `frontend/.env.example` to `frontend/.env`.
4. Fill in your API keys and secrets. Use a strong `JWT_SECRET`.
5. Install dependencies:

```bash
npm install
npm install --prefix frontend
pip install -r backend/requirements.txt
```

## Useful Commands

```bash
npm run build --prefix frontend
npm test --prefix frontend
npm run lint --prefix frontend
npm run test:backend
npm run test:e2e
docker compose up --build
```

## Environment Safety

- `TMDB_API_KEY` must come from the environment, not source code.
- Set `ENVIRONMENT=production` in production so missing critical secrets fail fast.
- Keep `MONGODB_TLS_ALLOW_INVALID_CERTIFICATES=false` except for temporary local troubleshooting.
- Keep `VITE_ENABLE_KEEP_ALIVE=false` unless you intentionally want the browser to ping the configured backend.

## License

All rights reserved. Unauthorized copying, distribution, or use of this project and its source code is strictly prohibited.

## Author

Developed by Omkar Ingle.

- GitHub: https://github.com/rajingle532
- LinkedIn: https://linkedin.com/in/omkar1535
