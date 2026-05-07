import React, { useState } from 'react';
import PageTransition from '../components/PageTransition';
import styles from './HelpPage.module.css';
import { ChevronDown, ChevronUp, HelpCircle, MessageCircle, Mail } from 'lucide-react';

const HelpPage: React.FC = () => {
  const [activeFaq, setActiveFaq] = useState<number | null>(null);

  const faqs = [
    {
      question: "How does the AI recommendation work?",
      answer: "MovieMind uses a sophisticated Content-Based Filtering algorithm. It analyzes the genres, keywords, and themes of movies you've rated highly to suggest similar titles that match your unique taste."
    },
    {
      question: "How do I add movies to my watchlist?",
      answer: "Simply click the '+' or 'Bookmark' icon on any movie card or detail page. You can access your full watchlist from your profile or the main menu."
    },
    {
      question: "Can I change my account details?",
      answer: "Yes, you can update your name and account settings from the 'Account Details' section in your profile menu."
    },
    {
      question: "Is MovieMind free to use?",
      answer: "Yes! MovieMind is currently free for all movie lovers. We want to help everyone find their next favorite film without any barriers."
    }
  ];

  const toggleFaq = (index: number) => {
    setActiveFaq(activeFaq === index ? null : index);
  };

  return (
    <PageTransition>
      <div className={`${styles.page} container`}>
        <header className={styles.header}>
          <HelpCircle size={48} className={styles.icon} />
          <h1>How can we help?</h1>
          <p>Find answers to common questions or reach out to our team.</p>
        </header>

        <section className={styles.faqSection}>
          <h2>Frequently Asked Questions</h2>
          <div className={styles.faqList}>
            {faqs.map((faq, index) => (
              <div 
                key={index} 
                className={`${styles.faqItem} ${activeFaq === index ? styles.active : ''}`}
                onClick={() => toggleFaq(index)}
              >
                <div className={styles.faqQuestion}>
                  <span>{faq.question}</span>
                  {activeFaq === index ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                </div>
                {activeFaq === index && (
                  <div className={styles.faqAnswer}>
                    {faq.answer}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>

        <section className={styles.contactSection}>
          <h2>Still need help?</h2>
          <div className={styles.contactCards}>
            <div className={styles.contactCard}>
              <Mail size={32} />
              <h3>Email Support</h3>
              <p>Response within 24 hours</p>
              <a href="mailto:support@moviemind.ai">support@moviemind.ai</a>
            </div>
            <div className={styles.contactCard}>
              <MessageCircle size={32} />
              <h3>Community</h3>
              <p>Join our Discord server</p>
              <button className={styles.btn}>Join Now</button>
            </div>
          </div>
        </section>
      </div>
    </PageTransition>
  );
};

export default HelpPage;
