import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import { GoogleOAuthProvider } from '@react-oauth/google'
import App from './App'
import './index.css'
import { startKeepAlive } from './utils/keepAlive'

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";

// Start keep-alive pings to prevent Render free tier from sleeping
startKeepAlive();

const container = document.getElementById('root');
const root = createRoot(container!);

root.render(
  <React.StrictMode>
    <BrowserRouter>
      <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
        <ThemeProvider>
          <AuthProvider>
            <App />
          </AuthProvider>
        </ThemeProvider>
      </GoogleOAuthProvider>
    </BrowserRouter>
  </React.StrictMode>,
)
