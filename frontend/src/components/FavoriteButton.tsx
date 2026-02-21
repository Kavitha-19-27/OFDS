import { HeartIcon } from '@heroicons/react/24/outline';
import { HeartIcon as HeartSolidIcon } from '@heroicons/react/24/solid';
import { useSettingsStore } from '../stores/settingsStore';
import toast from 'react-hot-toast';

interface FavoriteButtonProps {
  question: string;
  answer: string;
  size?: 'sm' | 'md';
}

const FavoriteButton: React.FC<FavoriteButtonProps> = ({ 
  question, 
  answer, 
  size = 'md' 
}) => {
  const { favorites, addFavorite, removeFavorite } = useSettingsStore();
  
  const favorite = favorites.find((f) => f.question === question);
  const isFavorited = !!favorite;
  
  const handleClick = () => {
    if (isFavorited && favorite) {
      removeFavorite(favorite.id);
      toast.success('Removed from favorites');
    } else {
      addFavorite(question, answer);
      toast.success('Added to favorites ⭐');
    }
  };

  const iconSize = size === 'sm' ? 'h-4 w-4' : 'h-5 w-5';
  const buttonSize = size === 'sm' ? 'p-1' : 'p-1.5';

  return (
    <button
      onClick={handleClick}
      className={`
        ${buttonSize} rounded-lg transition-all duration-200
        ${isFavorited
          ? 'text-red-500 hover:text-red-600 bg-red-50 dark:bg-red-900/20'
          : 'text-gray-400 hover:text-red-500 hover:bg-gray-100 dark:hover:bg-gray-700'
        }
      `}
      title={isFavorited ? 'Remove from favorites' : 'Add to favorites'}
    >
      {isFavorited ? (
        <HeartSolidIcon className={iconSize} />
      ) : (
        <HeartIcon className={iconSize} />
      )}
    </button>
  );
};

export default FavoriteButton;
