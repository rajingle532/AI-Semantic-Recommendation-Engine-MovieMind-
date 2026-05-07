import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../services/api';
import styles from './Auth.module.css';

const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      // Logic: Backend will check if email exists and "send" reset link
      await api.post('/auth/forgot-password', { email });
      setSubmitted(true);
      toast.success('Reset link sent to your email!');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Something went wrong');
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
        <div style={{ marginBottom: '1.5rem' }}>
          <Link to="/login" className={styles.backBtn} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', textDecoration: 'none', fontSize: '0.9rem' }}>
            <ArrowLeft size={16} /> Back to Login
          </Link>
        </div>

        <h1 className={styles.title}>Reset Password</h1>
        
        {!submitted ? (
          <>
            <p style={{ color: 'var(--text-muted)', marginBottom: '2rem', fontSize: '0.95rem', lineHeight: '1.5' }}>
              Enter your email address and we'll send you a link to reset your password.
            </p>
            <form onSubmit={handleSubmit} className={styles.form}>
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
              <button type="submit" className={styles.btn} disabled={loading}>
                {loading ? 'Sending link...' : 'Send Reset Link'}
              </button>
            </form>
          </>
        ) : (
          <div style={{ textAlign: 'center', padding: '2rem 0' }}>
            <div style={{ fontSize: '1.1rem', color: '#fff', marginBottom: '1rem' }}>Check your inbox!</div>
            <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
              We've sent a password reset link to <strong>{email}</strong>.
            </p>
            <button onClick={() => setSubmitted(false)} className={styles.btn} style={{ background: 'rgba(255,255,255,0.05)', color: '#fff' }}>
              Try another email
            </button>
          </div>
        )}
      </motion.div>
    </div>
  );
};

export default ForgotPasswordPage;
