import { SunIcon, MoonIcon, ComputerDesktopIcon } from '@heroicons/react/24/outline';
import { useSettingsStore, Theme } from '../stores/settingsStore';

const ThemeToggle: React.FC = () => {
  const { theme, setTheme } = useSettingsStore();

  const themes: { value: Theme; icon: React.ReactNode; label: string }[] = [
    { value: 'light', icon: <SunIcon className="h-4 w-4" />, label: 'Light' },
    { value: 'dark', icon: <MoonIcon className="h-4 w-4" />, label: 'Dark' },
    { value: 'system', icon: <ComputerDesktopIcon className="h-4 w-4" />, label: 'System' },
  ];

  return (
    <div className="flex items-center gap-1 p-1 bg-gray-100 dark:bg-gray-800 rounded-xl">
      {themes.map((t) => (
        <button
          key={t.value}
          onClick={() => setTheme(t.value)}
          className={`
            flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium
            transition-all duration-200
            ${theme === t.value
              ? 'bg-white dark:bg-gray-700 text-primary-600 dark:text-primary-400 shadow-sm'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
            }
          `}
          title={t.label}
        >
          {t.icon}
          <span className="hidden sm:inline">{t.label}</span>
        </button>
      ))}
    </div>
  );
};

export default ThemeToggle;
