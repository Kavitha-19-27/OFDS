import { LanguageIcon } from '@heroicons/react/24/outline';

export type LanguageMode = 'english' | 'tanglish';

interface LanguageToggleProps {
  value: LanguageMode;
  onChange: (mode: LanguageMode) => void;
}

const LanguageToggle: React.FC<LanguageToggleProps> = ({ value, onChange }) => {
  const handleToggle = () => {
    const newMode = value === 'english' ? 'tanglish' : 'english';
    onChange(newMode);
  };

  return (
    <div className="relative flex items-center gap-2">
      {/* Simple Toggle Button */}
      <button
        onClick={handleToggle}
        className={`
          relative flex items-center gap-2 px-4 py-2 rounded-xl font-medium text-sm
          transition-all duration-300 ease-in-out
          ${value === 'tanglish' 
            ? 'bg-gradient-to-r from-orange-500 to-red-500 text-white shadow-lg shadow-orange-500/30' 
            : 'bg-gradient-to-r from-blue-500 to-indigo-500 text-white shadow-lg shadow-blue-500/30'
          }
          hover:scale-105 active:scale-95
        `}
      >
        <LanguageIcon className="h-4 w-4" />
        <span>{value === 'english' ? '🇬🇧 English' : '🇮🇳 Tanglish'}</span>
      </button>
      
      {/* Mode Indicator */}
      <div className="text-xs text-gray-500 hidden sm:block">
        {value === 'tanglish' ? 'Tamil + English Mix 🔥' : 'Professional English ✨'}
      </div>
    </div>
  );
};

// Alternative: Slider Toggle Style
export const LanguageSlider: React.FC<LanguageToggleProps> = ({ value, onChange }) => {
  const handleToggle = () => {
    const newMode = value === 'english' ? 'tanglish' : 'english';
    onChange(newMode);
  };

  return (
    <div className="flex items-center gap-3">
      <span className={`text-sm font-medium transition-colors ${value === 'english' ? 'text-blue-600' : 'text-gray-400'}`}>
        🇬🇧 English
      </span>
      
      <button
        onClick={handleToggle}
        className={`
          relative w-14 h-7 rounded-full transition-colors duration-300 ease-in-out
          ${value === 'tanglish' 
            ? 'bg-gradient-to-r from-orange-500 to-red-500' 
            : 'bg-gradient-to-r from-blue-500 to-indigo-500'
          }
        `}
      >
        <span
          className={`
            absolute top-1 w-5 h-5 bg-white rounded-full shadow-md
            transition-all duration-300 ease-in-out
            ${value === 'tanglish' ? 'left-8' : 'left-1'}
          `}
        />
      </button>
      
      <span className={`text-sm font-medium transition-colors ${value === 'tanglish' ? 'text-orange-600' : 'text-gray-400'}`}>
        🇮🇳 Tanglish
      </span>
    </div>
  );
};

export default LanguageToggle;
