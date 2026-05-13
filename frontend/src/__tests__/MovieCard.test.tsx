import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import MovieCard from '../components/MovieCard';

const mockMovie = {
  id: 1,
  title: 'Test Movie',
  poster_path: '/test.jpg',
  vote_average: 8.5,
  release_date: '2024-01-01',
};

describe('MovieCard Component', () => {
  test('renders movie title and poster', () => {
    render(
      <BrowserRouter>
        <MovieCard movie={mockMovie} />
      </BrowserRouter>
    );
    screen.debug();
    expect(screen.getByText('Test Movie')).toBeInTheDocument();
    const img = screen.getByRole('img');
    expect(img).toHaveAttribute('src', expect.stringContaining('test.jpg'));
  });

  test('shows rating stars', () => {
    render(
      <BrowserRouter>
        <MovieCard movie={mockMovie} />
      </BrowserRouter>
    );
    // Rating stars might be rendered as text or SVG, let's check for the value
    expect(screen.getByText('8.5')).toBeInTheDocument();
  });
});
