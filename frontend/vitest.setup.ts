import * as matchers from '@testing-library/jest-dom/matchers';
import { expect, vi } from 'vitest';
import React from 'react';

expect.extend(matchers);

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
vi.mock('framer-motion', () => ({
  motion: new Proxy({}, {
    get: (target, prop) => {
      return ({ children, whileHover, whileTap, whileFocus, whileDrag, whileInView, initial, animate, exit, transition, variants, style, layout, layoutId, ...props }: any) => {
        // Also sanitize style if it's an object with custom properties that might cause warnings, but let's just pass valid props
        return React.createElement(prop as string, { ...props, style }, children);
      };
    }
  }),
  AnimatePresence: ({ children }: any) => children,
}));

vi.mock('lucide-react', () => {
  const icons = [
    // Navigation & UI
    'Film', 'Star', 'Info', 'Play', 'X', 'Search', 'User', 'LogOut',
    'Settings', 'Heart', 'ChevronLeft', 'ChevronRight', 'Sun', 'Moon',
    'Shield', 'HelpCircle', 'ArrowRight', 'Eye', 'Calendar', 'Clock',
    'Tv', 'ChevronDown', 'ChevronUp', 'Share2', 'Headphones',
    // Mood icons
    'Smile', 'Flame', 'CloudRain',
    // Profile / Account page icons
    'Bookmark', 'Brain', 'TrendingUp', 'Zap', 'RefreshCw',
    'Mail', 'Phone', 'Lock', 'Bell', 'Camera', 'Edit3',
    'CheckCircle2', 'Crown', 'Sparkles', 'Users',
  ];
  const mockIcons: any = {};
  icons.forEach(icon => {
    mockIcons[icon] = (props: any) => React.createElement('div', { ...props, 'data-testid': `${icon}-icon` });
  });
  return mockIcons;
});

// Mock api service globally
vi.mock('./src/services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
}));
