import React from 'react';
import { useAuth } from '../context/AuthContext';
import PageTransition from '../components/PageTransition';
import styles from './AccountPage.module.css';
import { User, Shield, Mail, Calendar, Settings } from 'lucide-react';

const AccountPage: React.FC = () => {
  const { user } = useAuth();

  return (
    <PageTransition>
      <div className={`${styles.page} container`}>
        <header className={styles.header}>
          <h1>Account Settings</h1>
          <p>Manage your personal information and security.</p>
        </header>

        <div className={styles.content}>
          <div className={styles.accountCard}>
            <div className={styles.cardHeader}>
              <div className={styles.avatarSection}>
                <div className={styles.avatar}>
                  {(user?.name ?? "U").charAt(0).toUpperCase()}
                </div>
                <div className={styles.headerInfo}>
                  <h2>{user?.name}</h2>
                  <p>{user?.email}</p>
                </div>
              </div>
              <button className={styles.editBtn}>Edit Profile</button>
            </div>

            <div className={styles.detailsGrid}>
              <div className={styles.detailItem}>
                <div className={styles.itemIcon}><User size={20} /></div>
                <div className={styles.itemContent}>
                  <label>Full Name</label>
                  <p>{user?.name}</p>
                </div>
              </div>

              <div className={styles.detailItem}>
                <div className={styles.itemIcon}><Mail size={20} /></div>
                <div className={styles.itemContent}>
                  <label>Email Address</label>
                  <p>{user?.email}</p>
                </div>
              </div>

              <div className={styles.detailItem}>
                <div className={styles.itemIcon}><Shield size={20} /></div>
                <div className={styles.itemContent}>
                  <label>Account Status</label>
                  <p className={styles.statusActive}>● Active</p>
                </div>
              </div>

              <div className={styles.detailItem}>
                <div className={styles.itemIcon}><Calendar size={20} /></div>
                <div className={styles.itemContent}>
                  <label>Membership</label>
                  <p>Free Tier</p>
                </div>
              </div>
            </div>
          </div>

          <div className={styles.secondaryActions}>
            <div className={styles.actionCard}>
              <Settings size={24} />
              <h3>Privacy & Security</h3>
              <p>Manage your password and data sharing preferences.</p>
              <button className={styles.secondaryBtn}>Manage</button>
            </div>
          </div>
        </div>
      </div>
    </PageTransition>
  );
};

export default AccountPage;
