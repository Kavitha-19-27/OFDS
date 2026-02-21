/**
 * Confidence indicator component for showing answer reliability.
 */
import React from 'react';
import { 
  CheckCircleIcon, 
  ExclamationCircleIcon, 
  QuestionMarkCircleIcon,
  XCircleIcon 
} from '@heroicons/react/24/outline';

interface ConfidenceIndicatorProps {
  level: 'high' | 'medium' | 'low' | 'none';
  score?: number;
  explanation?: string;
}

const ConfidenceIndicator: React.FC<ConfidenceIndicatorProps> = ({
  level,
  score,
  explanation
}) => {
  const config = {
    high: {
      icon: CheckCircleIcon,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      label: 'High confidence',
      description: 'Answer is well-supported by sources'
    },
    medium: {
      icon: ExclamationCircleIcon,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
      label: 'Medium confidence',
      description: 'Answer has partial source support'
    },
    low: {
      icon: QuestionMarkCircleIcon,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
      label: 'Low confidence',
      description: 'Limited source support for this answer'
    },
    none: {
      icon: XCircleIcon,
      color: 'text-red-600',
      bgColor: 'bg-red-50',
      label: 'No confidence',
      description: 'Unable to verify from sources'
    }
  };

  const { icon: Icon, color, bgColor, label, description } = config[level];

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full ${bgColor}`}>
      <Icon className={`h-4 w-4 ${color}`} />
      <span className={`text-xs font-medium ${color}`}>{label}</span>
      {score !== undefined && (
        <span className={`text-xs ${color} opacity-75`}>
          ({Math.round(score * 100)}%)
        </span>
      )}
      {explanation && (
        <span className="text-xs text-gray-500 ml-1" title={explanation}>
          ⓘ
        </span>
      )}
    </div>
  );
};

export default ConfidenceIndicator;
