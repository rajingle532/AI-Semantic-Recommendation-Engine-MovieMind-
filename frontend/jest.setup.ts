import '@testing-library/jest-dom';
import React from 'react';

// Mock localStorage
const localStorageMock = (function() {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => { store[key] = value.toString(); },
    clear: () => { store = {}; },
    removeItem: (key: string) => { delete store[key]; }
  };
})();

Object.defineProperty(window, 'localStorage', { value: localStorageMock });

// Mock IntersectionObserver
class IntersectionObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}
Object.defineProperty(window, 'IntersectionObserver', { value: IntersectionObserver });

// Global mocks
jest.mock('framer-motion', () => ({
  motion: {
    div: 'div',
    h1: 'h1',
    h2: 'h2',
    h3: 'h3',
    p: 'p',
    button: 'button',
    section: 'section',
    span: 'span',
    img: 'img',
  },
  AnimatePresence: ({ children }: any) => children,
}));

jest.mock('lucide-react', () => ({
  Star: () => React.createElement('div', { 'data-testid': 'star-icon' }),
  Info: () => React.createElement('div', { 'data-testid': 'info-icon' }),
  Play: () => React.createElement('div', { 'data-testid': 'play-icon' }),
  X: () => React.createElement('div', { 'data-testid': 'x-icon' }),
  Search: () => React.createElement('div', { 'data-testid': 'search-icon' }),
  User: () => React.createElement('div', { 'data-testid': 'user-icon' }),
  LogOut: () => React.createElement('div', { 'data-testid': 'logout-icon' }),
  Settings: () => React.createElement('div', { 'data-testid': 'settings-icon' }),
  Heart: () => React.createElement('div', { 'data-testid': 'heart-icon' }),
  ChevronLeft: () => React.createElement('div', { 'data-testid': 'chevron-left-icon' }),
  ChevronRight: () => React.createElement('div', { 'data-testid': 'chevron-right-icon' }),
}));
