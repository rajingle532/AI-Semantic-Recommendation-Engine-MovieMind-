import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, X, Send, Sparkles, Movie as MovieIcon } from 'lucide-react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { Movie } from '../types';
import styles from './ChatWidget.module.css';

interface ChatMessage {
  id: string;
  text: string;
  isAi: boolean;
  movies?: Movie[];
}

const ChatWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      text: "Hi! I'm your MovieMind AI. What kind of movie are you looking for today?",
      isAi: true
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      text: input,
      isAi: false
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const { data } = await api.get('/chat', { params: { message: input } });
      
      const aiMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        text: data.response,
        isAi: true,
        movies: data.movies
      };

      setMessages(prev => [...prev, aiMsg]);
    } catch (err) {
      console.error("Chat error:", err);
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        text: "Sorry, I'm having trouble connecting right now. Please try again later!",
        isAi: true
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.chatContainer}>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className={styles.chatWindow}
            initial={{ opacity: 0, y: 50, scale: 0.9, transformOrigin: 'bottom right' }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 50, scale: 0.9 }}
          >
            <div className={styles.chatHeader}>
              <h3><Sparkles size={18} color="#e50914" /> MovieMind AI</h3>
              <button className={styles.closeBtn} onClick={() => setIsOpen(false)}>
                <X size={20} />
              </button>
            </div>

            <div className={styles.messageArea} ref={scrollRef}>
              {messages.map((msg) => (
                <div key={msg.id} className={`${styles.message} ${msg.isAi ? styles.aiMessage : styles.userMessage}`}>
                  {msg.text}
                  
                  {msg.isAi && msg.movies && msg.movies.length > 0 && (
                    <div className={styles.movieResults}>
                      {msg.movies.slice(0, 3).map((movie) => (
                        <Link key={movie.id} to={`/movie/${movie.id}`} className={styles.movieItem}>
                          <img 
                            src={movie.poster_path || 'https://via.placeholder.com/40x60'} 
                            alt={movie.title} 
                            className={styles.miniPoster}
                          />
                          <span className={styles.movieTitle}>{movie.title}</span>
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {isLoading && <div className={styles.typing}>AI is thinking...</div>}
            </div>

            <div className={styles.inputArea}>
              <input
                type="text"
                placeholder="Ask about a movie plot, mood..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              />
              <button className={styles.sendBtn} onClick={handleSend} disabled={isLoading}>
                <Send size={18} />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.button
        className={styles.chatButton}
        onClick={() => setIsOpen(!isOpen)}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
      >
        {isOpen ? <X size={28} /> : <MessageSquare size={28} />}
      </motion.button>
    </div>
  );
};

export default ChatWidget;
