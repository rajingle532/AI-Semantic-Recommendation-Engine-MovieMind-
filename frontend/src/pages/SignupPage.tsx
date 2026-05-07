import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { GoogleLogin } from '@react-oauth/google';
import styles from './Auth.module.css';

const SignupPage: React.FC = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const { data } = await api.post('/auth/signup', { name, email, password });
      // Instruction: Save token+user to localStorage and redirect to home
      login(data.access_token, data.user);
      toast.success('Account created! Welcome to MovieMind.');
      navigate('/');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Signup failed');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSuccess = async (credentialResponse: any) => {
    setLoading(true);
    try {
      const { data } = await api.post('/auth/google', { token: credentialResponse.credential });
      login(data.access_token, data.user);
      toast.success('Signed in with Google!');
      navigate('/');
    } catch (err: any) {
      toast.error('Google sign-in failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.page}>
      <div className={styles.glow}></div>
      <motion.div 
        className={styles.card}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className={styles.title}>Create Account</h1>
        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.group}>
            <label>Full Name</label>
            <input 
              type="text" 
              placeholder="John Doe"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>
          <div className={styles.group}>
            <label>Email Address</label>
            <input 
              type="email" 
              placeholder="name@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className={styles.group}>
            <label>Password</label>
            <input 
              type="password" 
              placeholder="Min. 8 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit" className={styles.btn} disabled={loading}>
            {loading ? 'Creating account...' : 'Sign Up'}
          </button>
        </form>

        <div style={{ display: 'flex', alignItems: 'center', margin: '1.5rem 0', gap: '1rem' }}>
          <div style={{ flex: 1, height: '1px', background: 'rgba(255,255,255,0.1)' }}></div>
          <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>OR</span>
          <div style={{ flex: 1, height: '1px', background: 'rgba(255,255,255,0.1)' }}></div>
        </div>

        <div style={{ width: '100%', display: 'flex', justifyContent: 'center' }}>
          <GoogleLogin
            onSuccess={handleGoogleSuccess}
            onError={() => toast.error('Google login failed')}
            useOneTap
            theme="filled_blue"
            shape="pill"
            width="340px"
          />
        </div>
        <p className={styles.footer}>
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </motion.div>
    </div>
  );
};

export default SignupPage;
