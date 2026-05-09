import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, X, Send, Sparkles, Film as MovieIcon, ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { Movie } from '../types';
import styles from './ChatWidget.module.css';

interface ChatMessage {
  id: string;
  text: string;
  isAi: boolean;
  movies?: (Movie & { reason?: string })[];
  suggestions?: string[];
}

const ChatWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      text: "Hi! I'm MovieMind AI, your personal cinema expert. What's on your mind today?",
      isAi: true,
      suggestions: [
        "Suggest a mind-bending thriller",
        "Top rated Sci-Fi movies",
        "Action movies with great stunts"
      ]
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [messages, isLoading]);

  const handleSend = async (text: string = input) => {
    const messageText = text.trim();
    if (!messageText || isLoading) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      text: messageText,
      isAi: false
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      // Send history for context (last 5 messages)
      const history = messages.slice(-5).map(m => ({
        role: m.isAi ? 'assistant' : 'user',
        content: m.text
      }));

      const { data } = await api.post('/chat', { 
        message: messageText,
        history: history
      });
      
      const aiMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        text: data.response,
        isAi: true,
        movies: data.movies,
        suggestions: data.suggestions
      };

      setMessages(prev => [...prev, aiMsg]);
    } catch (err) {
      console.error("Chat error:", err);
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        text: "Sorry, I'm having trouble connecting right now. Let me check my database and get back to you!",
        isAi: true
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const TypingIndicator = () => (
    <div className={styles.typingIndicator}>
      <div className={styles.dot}></div>
      <div className={styles.dot}></div>
      <div className={styles.dot}></div>
    </div>
  );

  return (
    <div className={styles.chatContainer}>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className={styles.chatWindow}
            initial={{ opacity: 0, y: 40, scale: 0.9, filter: 'blur(10px)' }}
            animate={{ opacity: 1, y: 0, scale: 1, filter: 'blur(0px)' }}
            exit={{ opacity: 0, y: 40, scale: 0.9, filter: 'blur(10px)' }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
          >
            <div className={styles.chatHeader}>
              <h3><Sparkles size={20} color="#e50914" fill="#e50914" /> MovieMind AI</h3>
              <button className={styles.closeBtn} onClick={() => setIsOpen(false)}>
                <X size={18} />
              </button>
            </div>

            <div className={styles.messageArea} ref={scrollRef}>
              {messages.map((msg, idx) => (
                <motion.div 
                  key={msg.id} 
                  initial={{ opacity: 0, x: msg.isAi ? -20 : 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 }}
                  className={`${styles.message} ${msg.isAi ? styles.aiMessage : styles.userMessage}`}
                >
                  <div className={styles.messageText}>{msg.text}</div>
                  
                  {msg.isAi && msg.movies && msg.movies.length > 0 && (
                    <div className={styles.movieResults}>
                      {msg.movies.slice(0, 3).map((movie) => (
                        <Link key={movie.id} to={`/movie/${movie.id}`} className={styles.movieItem}>
                          <img 
                            src={movie.poster_path 
                              ? (movie.poster_path.startsWith('http') ? movie.poster_path : `https://image.tmdb.org/t/p/w92${movie.poster_path}`)
                              : 'https://via.placeholder.com/92x138'} 
                            alt={movie.title} 
                            className={styles.miniPoster}
                          />
                          <div className={styles.movieInfo}>
                            <span className={styles.movieTitle}>{movie.title}</span>
                            {movie.reason && <span className={styles.movieReason}>{movie.reason}</span>}
                          </div>
                          <ChevronRight size={16} style={{ marginLeft: 'auto', opacity: 0.5 }} />
                        </Link>
                      ))}
                    </div>
                  )}

                  {msg.isAi && msg.suggestions && msg.suggestions.length > 0 && (
                    <div className={styles.suggestions}>
                      {msg.suggestions.map((s, i) => (
                        <motion.button
                          key={i}
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          className={styles.chip}
                          onClick={() => handleSend(s)}
                        >
                          {s}
                        </motion.button>
                      ))}
                    </div>
                  )}
                </motion.div>
              ))}
              {isLoading && <TypingIndicator />}
            </div>

            <div className={styles.inputArea}>
              <input
                type="text"
                placeholder="Find a movie, explore vibes..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              />
              <button 
                className={styles.sendBtn} 
                onClick={() => handleSend()} 
                disabled={isLoading || !input.trim()}
              >
                <Send size={18} />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.button
        className={styles.chatButton}
        onClick={() => setIsOpen(!isOpen)}
        whileHover={{ scale: 1.05, rotate: isOpen ? 0 : 5 }}
        whileTap={{ scale: 0.95 }}
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: "spring", stiffness: 400, damping: 10 }}
      >
        <AnimatePresence mode="wait">
          {isOpen ? (
            <motion.div
              key="close"
              initial={{ rotate: -90, opacity: 0 }}
              animate={{ rotate: 0, opacity: 1 }}
              exit={{ rotate: 90, opacity: 0 }}
            >
              <X size={28} />
            </motion.div>
          ) : (
            <motion.div
              key="chat"
              initial={{ rotate: 90, opacity: 0 }}
              animate={{ rotate: 0, opacity: 1 }}
              exit={{ rotate: -90, opacity: 0 }}
            >
              <MessageSquare size={28} />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.button>
    </div>
  );
};

export default ChatWidget;
