import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import PageTransition from '../components/PageTransition';
import styles from './AccountPage.module.css';
import {
  User, Mail, Phone, Shield, Crown, CheckCircle2,
  Edit3, X, Camera, Bell, Lock, ChevronRight, Sparkles
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';
import api from '../services/api';

const AccountPage: React.FC = () => {
  const { user, token, login } = useAuth();
  const [showEditModal, setShowEditModal] = useState(false);
  const [editName, setEditName] = useState(user?.name || '');
  const [editPhone, setEditPhone] = useState(user?.phone || '');
  const [saving, setSaving] = useState(false);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editName.trim()) {
      toast.error('Name cannot be empty');
      return;
    }
    setSaving(true);
    try {
      const { data } = await api.patch('/auth/update-profile', {
        token,
        name: editName.trim(),
        phone: editPhone.trim(),
      });
      login(token!, data);
      toast.success('Profile updated successfully!');
      setShowEditModal(false);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const initials = (user?.name ?? 'U').charAt(0).toUpperCase();
  const joinDate = new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' });

  return (
    <PageTransition>
      <div className={styles.page}>
        {/* Hero Header */}
        <div className={styles.heroBanner}>
          <div className={styles.heroBannerBg} />
          <div className={styles.heroBannerContent}>
            <div className={styles.avatarWrapper}>
              <div className={styles.avatar}>{initials}</div>
              <button className={styles.cameraBtn} title="Change photo">
                <Camera size={14} />
              </button>
            </div>
            <div className={styles.heroInfo}>
              <h1>{user?.name}</h1>
              <p>{user?.email}</p>
              <span className={styles.memberBadge}>
                <Sparkles size={12} />
                MovieMind Member
              </span>
            </div>
            <button className={styles.editBtn} onClick={() => { setEditName(user?.name || ''); setEditPhone(user?.phone || ''); setShowEditModal(true); }}>
              <Edit3 size={16} />
              Edit Profile
            </button>
          </div>
        </div>

        <div className={styles.content}>
          {/* Personal Info Card */}
          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>Personal Information</h2>
            <div className={styles.infoCard}>
              <div className={styles.infoRow}>
                <div className={styles.infoIcon} style={{ background: 'rgba(229,9,20,0.1)' }}>
                  <User size={18} color="#e50914" />
                </div>
                <div className={styles.infoContent}>
                  <span className={styles.infoLabel}>Full Name</span>
                  <span className={styles.infoValue}>{user?.name || '—'}</span>
                </div>
                <button className={styles.rowEditBtn} onClick={() => { setEditName(user?.name || ''); setEditPhone(user?.phone || ''); setShowEditModal(true); }}>
                  <Edit3 size={14} />
                </button>
              </div>

              <div className={styles.divider} />

              <div className={styles.infoRow}>
                <div className={styles.infoIcon} style={{ background: 'rgba(99,102,241,0.1)' }}>
                  <Mail size={18} color="#6366f1" />
                </div>
                <div className={styles.infoContent}>
                  <span className={styles.infoLabel}>Email Address</span>
                  <span className={styles.infoValue}>{user?.email || '—'}</span>
                </div>
                <span className={styles.verifiedBadge}>
                  <CheckCircle2 size={14} />
                  Verified
                </span>
              </div>

              <div className={styles.divider} />

              <div className={styles.infoRow}>
                <div className={styles.infoIcon} style={{ background: 'rgba(16,185,129,0.1)' }}>
                  <Phone size={18} color="#10b981" />
                </div>
                <div className={styles.infoContent}>
                  <span className={styles.infoLabel}>Mobile Number</span>
                  <span className={styles.infoValue} style={{ color: user?.phone ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                    {user?.phone || 'Not added yet'}
                  </span>
                </div>
                <button className={styles.rowEditBtn} onClick={() => { setEditName(user?.name || ''); setEditPhone(user?.phone || ''); setShowEditModal(true); }}>
                  <Edit3 size={14} />
                </button>
              </div>
            </div>
          </div>

          {/* Account Details */}
          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>Account Details</h2>
            <div className={styles.statsGrid}>
              <div className={styles.statCard}>
                <div className={styles.statIcon} style={{ background: 'rgba(245,158,11,0.1)' }}>
                  <Crown size={20} color="#f59e0b" />
                </div>
                <div>
                  <span className={styles.statLabel}>Membership</span>
                  <span className={styles.statValue}>Free Tier</span>
                </div>
              </div>
              <div className={styles.statCard}>
                <div className={styles.statIcon} style={{ background: 'rgba(16,185,129,0.1)' }}>
                  <CheckCircle2 size={20} color="#10b981" />
                </div>
                <div>
                  <span className={styles.statLabel}>Account Status</span>
                  <span className={styles.statValue} style={{ color: '#10b981' }}>● Active</span>
                </div>
              </div>
              <div className={styles.statCard}>
                <div className={styles.statIcon} style={{ background: 'rgba(99,102,241,0.1)' }}>
                  <Sparkles size={20} color="#6366f1" />
                </div>
                <div>
                  <span className={styles.statLabel}>Member Since</span>
                  <span className={styles.statValue}>{joinDate}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Settings Links */}
          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>Settings</h2>
            <div className={styles.settingsCard}>
              <button className={styles.settingsRow}>
                <div className={styles.infoIcon} style={{ background: 'rgba(229,9,20,0.1)' }}>
                  <Lock size={18} color="#e50914" />
                </div>
                <div className={styles.infoContent}>
                  <span className={styles.infoLabel}>Password & Security</span>
                  <span className={styles.infoValueSmall}>Change password, 2FA settings</span>
                </div>
                <ChevronRight size={18} color="var(--text-muted)" />
              </button>

              <div className={styles.divider} />

              <button className={styles.settingsRow}>
                <div className={styles.infoIcon} style={{ background: 'rgba(99,102,241,0.1)' }}>
                  <Bell size={18} color="#6366f1" />
                </div>
                <div className={styles.infoContent}>
                  <span className={styles.infoLabel}>Notifications</span>
                  <span className={styles.infoValueSmall}>Email and push notifications</span>
                </div>
                <ChevronRight size={18} color="var(--text-muted)" />
              </button>

              <div className={styles.divider} />

              <button className={styles.settingsRow}>
                <div className={styles.infoIcon} style={{ background: 'rgba(16,185,129,0.1)' }}>
                  <Shield size={18} color="#10b981" />
                </div>
                <div className={styles.infoContent}>
                  <span className={styles.infoLabel}>Privacy</span>
                  <span className={styles.infoValueSmall}>Data and privacy preferences</span>
                </div>
                <ChevronRight size={18} color="var(--text-muted)" />
              </button>
            </div>
          </div>
        </div>

        {/* Edit Modal */}
        <AnimatePresence>
          {showEditModal && (
            <motion.div
              className={styles.modalBackdrop}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowEditModal(false)}
            >
              <motion.div
                className={styles.modal}
                initial={{ opacity: 0, scale: 0.9, y: 30 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9, y: 30 }}
                transition={{ type: 'spring', stiffness: 300, damping: 25 }}
                onClick={(e) => e.stopPropagation()}
              >
                <div className={styles.modalHeader}>
                  <div>
                    <h3>Edit Profile</h3>
                    <p>Update your personal information</p>
                  </div>
                  <button className={styles.closeBtn} onClick={() => setShowEditModal(false)}>
                    <X size={20} />
                  </button>
                </div>

                <form onSubmit={handleSave} className={styles.modalForm}>
                  <div className={styles.modalAvatar}>{initials}</div>

                  <div className={styles.formGroup}>
                    <label htmlFor="editName">
                      <User size={14} />
                      Full Name
                    </label>
                    <input
                      id="editName"
                      type="text"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      placeholder="Enter your full name"
                      required
                    />
                  </div>

                  <div className={styles.formGroup}>
                    <label htmlFor="editEmail">
                      <Mail size={14} />
                      Email Address
                    </label>
                    <input
                      id="editEmail"
                      type="email"
                      value={user?.email || ''}
                      disabled
                      className={styles.disabledInput}
                    />
                    <span className={styles.helperText}>Email cannot be changed</span>
                  </div>

                  <div className={styles.formGroup}>
                    <label htmlFor="editPhone">
                      <Phone size={14} />
                      Mobile Number
                    </label>
                    <input
                      id="editPhone"
                      type="tel"
                      value={editPhone}
                      onChange={(e) => setEditPhone(e.target.value)}
                      placeholder="+91 99999 99999"
                    />
                  </div>

                  <div className={styles.modalActions}>
                    <button type="button" className={styles.cancelBtn} onClick={() => setShowEditModal(false)}>
                      Cancel
                    </button>
                    <button type="submit" className={styles.saveBtn} disabled={saving}>
                      {saving ? 'Saving...' : 'Save Changes'}
                    </button>
                  </div>
                </form>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </PageTransition>
  );
};

export default AccountPage;
