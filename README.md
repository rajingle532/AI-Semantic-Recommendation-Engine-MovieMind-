# 🎬 CineMatch AI — The Future of Movie Discovery

![CineMatch AI Banner](docs/assets/banner.png)

CineMatch AI is a premium, full-stack movie recommendation platform that leverages **Hybrid Machine Learning algorithms** to deliver hyper-personalized film suggestions. Built with a sleek, Netflix-inspired dark aesthetic, it features real-time search, semantic NLP discovery, and a robust user interaction system.

## ✨ Key Features

- **🧠 Hybrid Recommendation Engine**: Combines Content-Based Filtering (Cosine Similarity) with Collaborative Filtering (SVD Matrix Factorization) for unparalleled accuracy.
- **🔍 NLP Semantic Search**: Describe a vibe, mood, or plot theme (e.g., *"A lonely robot in space"*) and let our AI find the perfect match.
- **🌗 Stunning UI/UX**: A high-performance React frontend with glassmorphism effects, Framer Motion animations, and responsive design.
- **🔐 Secure Authentication**: JWT-based security with support for traditional Email/Password and **Google OAuth** integration.
- **⭐ User Interactions**: Rate movies, maintain a personal Watchlist, and see your recommendations evolve in real-time.
- **📱 TMDB Integration**: Live synchronization with the TMDB API for the latest posters, trailers, and movie metadata.

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | React 18, Vite, Framer Motion, Lucide Icons, Vanilla CSS |
| **Backend** | FastAPI (Python 3.10+), Uvicorn |
| **Database** | MongoDB Atlas (NoSQL) |
| **Machine Learning** | Scikit-learn, Pandas, NumPy, NLTK |
| **Authentication** | JWT (JSON Web Tokens), Google OAuth 2.0 |

## 🚀 Quick Start

### 1. Clone & Configure
```bash
git clone https://github.com/rajingle532/movies-recommender-system.git
cd movies-recommender-system
cp .env.example .env
```
*Fill in your `TMDB_API_KEY`, `MONGODB_URI`, and `GOOGLE_CLIENT_ID` in the `.env` file.*

### 2. Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```
*API Documentation available at `http://localhost:8000/docs`*

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
*Access the app at `http://localhost:5173`*

## 📊 ML Architecture

CineMatch AI uses a sophisticated pipeline:
1. **Content Filtering**: Analyzes genres, keywords, cast, and overviews using **TF-IDF Vectorization**.
2. **Collaborative Filtering**: Learns user preferences from global rating patterns using **SVD**.
3. **Hybrid Scoring**: Dynamically weights both models to provide "Picked for You" suggestions.

## 🤝 Contributing

Contributions make the open-source community an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---
*Built with ❤️ by [Raj Ingle](https://github.com/rajingle532)*
