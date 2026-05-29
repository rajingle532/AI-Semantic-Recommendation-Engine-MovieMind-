import React from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { Toaster } from 'react-hot-toast';

// Components
import Navbar from './components/Navbar';
import ProtectedRoute from './components/ProtectedRoute';
import ChatWidget from './components/ChatWidget';

// Pages
import HomePage from './pages/HomePage';
import TVPage from './pages/TVPage';
import SearchPage from './pages/SearchPage';
import MovieDetailPage from './pages/MovieDetailPage';
import TVDetailPage from './pages/TVDetailPage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import ProfilePage from './pages/ProfilePage';
import MusicPage from './pages/MusicPage';
import PersonDetailPage from './pages/PersonDetailPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
import AccountPage from './pages/AccountPage';
import HelpPage from './pages/HelpPage';
import CineMatchPage from './pages/CineMatchPage';
import CineSharePage from './pages/CineSharePage';
import TicketsPage from './pages/TicketsPage';

const App: React.FC = () => {
  const location = useLocation();

  return (
    <>
      <Toaster
        position="top-center"
        toastOptions={{
          style: {
            background: '#333',
            color: '#fff',
            borderRadius: '8px',
          },
        }}
      />

      <Navbar />

      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          {/* Public Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="/help" element={<HelpPage />} />

          {/* Protected Routes */}
          <Route element={<ProtectedRoute />}>
            <Route path="/" element={<HomePage />} />
            <Route path="/tv" element={<TVPage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/movie/:id" element={<MovieDetailPage />} />
            <Route path="/tv/:id" element={<TVDetailPage />} />
            <Route path="/person/:id" element={<PersonDetailPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/music" element={<MusicPage />} />
            <Route path="/account" element={<AccountPage />} />
            <Route path="/cinematch" element={<CineMatchPage />} />
            <Route path="/cineshare" element={<CineSharePage />} />
            <Route path="/tickets" element={<TicketsPage />} />
          </Route>
        </Routes>
      </AnimatePresence>

      <ChatWidget />
    </>
  );
};

export default App;