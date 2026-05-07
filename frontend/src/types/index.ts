export interface Movie {
  id: number; // Updated from movie_id
  title: string;
  poster_path: string | null;
  vote_average?: number;
  release_date?: string;
  overview?: string;
  genres?: string[];
  cast?: string[];
  director?: string;
  similarity_score?: number;
  relevance_score?: number;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    name: string;
    email: string;
  };
}
