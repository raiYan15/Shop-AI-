import { create } from 'zustand';
import { Product } from '../data/mockData';
import { AuthUser, clearAuth, getStoredUser } from '../services/api';

const THEME_KEY = 'shopmind_theme';

function getInitialDarkMode(): boolean {
  if (typeof window === 'undefined') return false;
  const saved = localStorage.getItem(THEME_KEY);
  if (saved === 'dark') return true;
  if (saved === 'light') return false;
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false;
}

interface AppState {
  darkMode: boolean;
  toggleDarkMode: () => void;
  cart: Product[];
  addToCart: (product: Product) => void;
  removeFromCart: (id: string) => void;
  wishlist: Product[];
  toggleWishlist: (product: Product) => void;
  isInWishlist: (id: string) => boolean;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  searchHistory: string[];
  addToSearchHistory: (query: string) => void;
  activeCategory: string;
  setActiveCategory: (category: string) => void;
  // Auth
  currentUser: AuthUser | null;
  setCurrentUser: (user: AuthUser | null) => void;
  logout: () => void;
  isAuthenticated: () => boolean;
}

export const useStore = create<AppState>((set, get) => ({
  darkMode: getInitialDarkMode(),
  toggleDarkMode: () => {
    const newMode = !get().darkMode;
    set({ darkMode: newMode });
    localStorage.setItem(THEME_KEY, newMode ? 'dark' : 'light');
    if (newMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  },

  cart: [],
  addToCart: (product) =>
    set((state) => ({
      cart: state.cart.find((p) => p.id === product.id)
        ? state.cart
        : [...state.cart, product],
    })),
  removeFromCart: (id) =>
    set((state) => ({ cart: state.cart.filter((p) => p.id !== id) })),

  wishlist: [],
  toggleWishlist: (product) =>
    set((state) => {
      const exists = state.wishlist.find((p) => p.id === product.id);
      return {
        wishlist: exists
          ? state.wishlist.filter((p) => p.id !== product.id)
          : [...state.wishlist, product],
      };
    }),
  isInWishlist: (id) => get().wishlist.some((p) => p.id === id),

  searchQuery: '',
  setSearchQuery: (query) => set({ searchQuery: query }),

  searchHistory: [
    'MacBook Pro M3',
    'Gaming headset',
    'Running shoes',
    '4K TV under 1 lakh',
  ],
  addToSearchHistory: (query) =>
    set((state) => ({
      searchHistory: [query, ...state.searchHistory.filter((q) => q !== query)].slice(0, 10),
    })),

  activeCategory: 'All',
  setActiveCategory: (category) => set({ activeCategory: category }),

  // Auth
  currentUser: getStoredUser(),
  setCurrentUser: (user) => set({ currentUser: user }),
  logout: () => {
    clearAuth();
    set({ currentUser: null });
  },
  isAuthenticated: () => get().currentUser !== null,
}));
