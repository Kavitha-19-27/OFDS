/**
 * Quota usage display component.
 * Shows usage limits and remaining capacity.
 */
import React from 'react';

interface QuotaData {
  used: number;
  limit: number;
  remaining: number;
  percentage: number;
}

interface QuotaStatus {
  documents: QuotaData;
  storage_mb: QuotaData;
  queries_today: QuotaData;
  tokens_today: QuotaData;
  resets_at: string;
}

interface QuotaUsageProps {
  quota: QuotaStatus;
}

const QuotaUsage: React.FC<QuotaUsageProps> = ({ quota }) => {
  const getProgressColor = (percentage: number) => {
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 70) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const formatResetTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const quotaItems = [
    { key: 'documents', label: 'Documents', unit: '' },
    { key: 'storage_mb', label: 'Storage', unit: 'MB' },
    { key: 'queries_today', label: 'Queries Today', unit: '' },
    { key: 'tokens_today', label: 'Tokens Today', unit: '' }
  ];

  return (
    <div className="p-4 bg-white rounded-lg border shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-700">Usage Quota</h3>
        <span className="text-xs text-gray-500">
          Resets at {formatResetTime(quota.resets_at)}
        </span>
      </div>

      <div className="space-y-4">
        {quotaItems.map((item) => {
          const data = quota[item.key as keyof QuotaStatus] as QuotaData;
          return (
            <div key={item.key}>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-gray-600">{item.label}</span>
                <span className="text-gray-500">
                  {data.used.toLocaleString()}{item.unit} / {data.limit.toLocaleString()}{item.unit}
                </span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-300 ${getProgressColor(data.percentage)}`}
                  style={{ width: `${Math.min(100, data.percentage)}%` }}
                />
              </div>
              {data.percentage >= 80 && (
                <p className="text-xs text-yellow-600 mt-1">
                  {data.remaining.toLocaleString()}{item.unit} remaining
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default QuotaUsage;
