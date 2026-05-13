import '@testing-library/jest-dom';
import React from 'react';
import { vi } from 'vitest';

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
      return ({ children, ...props }: any) => React.createElement(prop as string, props, children);
    }
  }),
  AnimatePresence: ({ children }: any) => children,
}));

vi.mock('lucide-react', () => {
  const icons = [
    'Film', 'Star', 'Info', 'Play', 'X', 'Search', 'User', 'LogOut', 
    'Settings', 'Heart', 'ChevronLeft', 'ChevronRight', 'Sun', 'Moon',
    'Shield', 'HelpCircle', 'ArrowRight', 'Eye', 'Calendar', 'Clock'
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
