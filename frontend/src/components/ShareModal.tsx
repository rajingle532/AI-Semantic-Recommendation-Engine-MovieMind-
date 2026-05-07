import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Send, Twitter, Link as LinkIcon, Share2 } from 'lucide-react';
import toast from 'react-hot-toast';
import styles from './ShareModal.module.css';

interface ShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  url: string;
}

const ShareModal: React.FC<ShareModalProps> = ({ isOpen, onClose, title, url }) => {
  const shareText = `Check out this movie on MovieMind: ${title}`;
  const fullUrl = window.location.origin + url;

  const copyToClipboard = () => {
    navigator.clipboard.writeText(fullUrl);
    toast.success("Link copied to clipboard!");
  };

  const shareOnWhatsApp = () => {
    const whatsappUrl = `https://api.whatsapp.com/send?text=${encodeURIComponent(shareText + ' ' + fullUrl)}`;
    window.open(whatsappUrl, '_blank');
  };

  const shareOnTwitter = () => {
    const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(fullUrl)}`;
    window.open(twitterUrl, '_blank');
  };

  const handleNativeShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'MovieMind',
          text: shareText,
          url: fullUrl,
        });
      } catch (err) {
        console.error("Native share failed", err);
      }
    } else {
      toast.error("Sharing not supported on this browser");
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className={styles.overlay} onClick={onClose}>
          <motion.div 
            className={styles.modal}
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className={styles.header}>
              <h3>Share Movie</h3>
              <button onClick={onClose} className={styles.closeBtn}>
                <X size={20} />
              </button>
            </div>

            <div className={styles.options}>
              <button className={styles.option} onClick={shareOnWhatsApp}>
                <div className={`${styles.icon} ${styles.whatsapp}`}>
                  <Send size={24} />
                </div>
                <span>WhatsApp</span>
              </button>

              <button className={styles.option} onClick={shareOnTwitter}>
                <div className={`${styles.icon} ${styles.twitter}`}>
                  <Twitter size={24} />
                </div>
                <span>Twitter</span>
              </button>

              <button className={styles.option} onClick={handleNativeShare}>
                <div className={`${styles.icon} ${styles.native}`}>
                  <Share2 size={24} />
                </div>
                <span>Other</span>
              </button>
            </div>

            <div className={styles.copySection}>
              <div className={styles.urlInput}>
                <input type="text" value={fullUrl} readOnly />
              </div>
              <button onClick={copyToClipboard} className={styles.copyBtn}>
                <LinkIcon size={18} /> Copy
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default ShareModal;
