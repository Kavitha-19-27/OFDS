import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type Theme = 'light' | 'dark' | 'system';

export interface Favorite {
  id: string;
  question: string;
  answer: string;
  createdAt: string;
}

export interface CustomTemplate {
  id: string;
  name: string;
  prompt: string;
  icon: string;
  createdAt: string;
}

interface SettingsState {
  // Theme
  theme: Theme;
  setTheme: (theme: Theme) => void;
  
  // Favorites
  favorites: Favorite[];
  addFavorite: (question: string, answer: string) => void;
  removeFavorite: (id: string) => void;
  isFavorite: (question: string) => boolean;
  
  // Custom Templates
  customTemplates: CustomTemplate[];
  addTemplate: (name: string, prompt: string, icon?: string) => void;
  removeTemplate: (id: string) => void;
  updateTemplate: (id: string, updates: Partial<Pick<CustomTemplate, 'name' | 'prompt' | 'icon'>>) => void;
  
  // Voice Settings
  voiceEnabled: boolean;
  setVoiceEnabled: (enabled: boolean) => void;
  voiceLanguage: 'en-US' | 'ta-IN';
  setVoiceLanguage: (lang: 'en-US' | 'ta-IN') => void;
}

// Apply theme to document
const applyTheme = (theme: Theme) => {
  const root = document.documentElement;
  const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  
  if (theme === 'dark' || (theme === 'system' && systemDark)) {
    root.classList.add('dark');
  } else {
    root.classList.remove('dark');
  }
};

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set, get) => ({
      // Theme
      theme: 'light',
      setTheme: (theme: Theme) => {
        applyTheme(theme);
        set({ theme });
      },
      
      // Favorites
      favorites: [],
      addFavorite: (question: string, answer: string) => {
        const newFavorite: Favorite = {
          id: crypto.randomUUID(),
          question,
          answer,
          createdAt: new Date().toISOString(),
        };
        set((state) => ({ favorites: [...state.favorites, newFavorite] }));
      },
      removeFavorite: (id: string) => {
        set((state) => ({
          favorites: state.favorites.filter((f) => f.id !== id),
        }));
      },
      isFavorite: (question: string) => {
        return get().favorites.some((f) => f.question === question);
      },
      
      // Custom Templates
      customTemplates: [],
      addTemplate: (name: string, prompt: string, icon: string = '📝') => {
        const newTemplate: CustomTemplate = {
          id: crypto.randomUUID(),
          name,
          prompt,
          icon,
          createdAt: new Date().toISOString(),
        };
        set((state) => ({ customTemplates: [...state.customTemplates, newTemplate] }));
      },
      removeTemplate: (id: string) => {
        set((state) => ({
          customTemplates: state.customTemplates.filter((t) => t.id !== id),
        }));
      },
      updateTemplate: (id: string, updates: Partial<Pick<CustomTemplate, 'name' | 'prompt' | 'icon'>>) => {
        set((state) => ({
          customTemplates: state.customTemplates.map((t) =>
            t.id === id ? { ...t, ...updates } : t
          ),
        }));
      },
      
      // Voice Settings
      voiceEnabled: false,
      setVoiceEnabled: (enabled: boolean) => set({ voiceEnabled: enabled }),
      voiceLanguage: 'en-US',
      setVoiceLanguage: (lang: 'en-US' | 'ta-IN') => set({ voiceLanguage: lang }),
    }),
    {
      name: 'app-settings',
      onRehydrateStorage: () => (state) => {
        // Apply theme on page load
        if (state) {
          applyTheme(state.theme);
        }
      },
    }
  )
);

// Listen for system theme changes
if (typeof window !== 'undefined') {
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    const { theme } = useSettingsStore.getState();
    if (theme === 'system') {
      applyTheme('system');
    }
  });
}
