import React, { Suspense } from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { Toaster } from 'react-hot-toast';

// Components (keep non-page components eager — they're needed immediately)
import Navbar from './components/Navbar';
import ProtectedRoute from './components/ProtectedRoute';
import ChatWidget from './components/ChatWidget';

// Lazy-load all pages for code splitting (dramatically reduces initial bundle size)
const HomePage         = React.lazy(() => import('./pages/HomePage'));
const TVPage           = React.lazy(() => import('./pages/TVPage'));
const SearchPage       = React.lazy(() => import('./pages/SearchPage'));
const MovieDetailPage  = React.lazy(() => import('./pages/MovieDetailPage'));
const TVDetailPage     = React.lazy(() => import('./pages/TVDetailPage'));
const LoginPage        = React.lazy(() => import('./pages/LoginPage'));
const SignupPage       = React.lazy(() => import('./pages/SignupPage'));
const ProfilePage      = React.lazy(() => import('./pages/ProfilePage'));
const MusicPage        = React.lazy(() => import('./pages/MusicPage'));
const PersonDetailPage = React.lazy(() => import('./pages/PersonDetailPage'));
const ForgotPasswordPage = React.lazy(() => import('./pages/ForgotPasswordPage'));
const ResetPasswordPage  = React.lazy(() => import('./pages/ResetPasswordPage'));
const AccountPage      = React.lazy(() => import('./pages/AccountPage'));
const HelpPage         = React.lazy(() => import('./pages/HelpPage'));
const CineMatchPage    = React.lazy(() => import('./pages/CineMatchPage'));
const CineSharePage    = React.lazy(() => import('./pages/CineSharePage'));
const TicketsPage      = React.lazy(() => import('./pages/TicketsPage'));

// Minimal full-screen spinner shown while a lazy chunk is downloading
const PageLoader = () => (
  <div style={{
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100vh',
    background: 'var(--bg-primary, #0d0d0d)',
  }}>
    <div style={{
      width: 48,
      height: 48,
      borderRadius: '50%',
      border: '3px solid rgba(255,255,255,0.1)',
      borderTopColor: 'var(--accent-primary, #e50914)',
      animation: 'spin 0.7s linear infinite',
    }} />
    <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
  </div>
);

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

      <Suspense fallback={<PageLoader />}>
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
      </Suspense>

      <ChatWidget />
    </>
  );
};

export default App;