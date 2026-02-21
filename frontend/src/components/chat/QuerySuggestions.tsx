/**
 * Query suggestions component.
 * Shows contextual follow-up questions.
 */
import React from 'react';
import { LightBulbIcon } from '@heroicons/react/24/outline';

interface QuerySuggestionsProps {
  suggestions: string[];
  onSelect: (query: string) => void;
}

const QuerySuggestions: React.FC<QuerySuggestionsProps> = ({
  suggestions,
  onSelect
}) => {
  if (!suggestions || suggestions.length === 0) {
    return null;
  }

  return (
    <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-100">
      <div className="flex items-center gap-2 mb-2">
        <LightBulbIcon className="h-4 w-4 text-blue-600" />
        <span className="text-xs font-medium text-blue-700">
          Follow-up questions
        </span>
      </div>
      <div className="flex flex-wrap gap-2">
        {suggestions.map((suggestion, index) => (
          <button
            key={index}
            onClick={() => onSelect(suggestion)}
            className="text-xs px-3 py-1.5 bg-white border border-blue-200 rounded-full 
                     text-blue-700 hover:bg-blue-100 hover:border-blue-300 
                     transition-colors cursor-pointer"
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
};

export default QuerySuggestions;
