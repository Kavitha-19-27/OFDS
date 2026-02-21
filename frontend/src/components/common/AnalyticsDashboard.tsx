/**
 * Analytics dashboard component.
 * Displays usage statistics and quality metrics.
 */
import React from 'react';
import {
  ChatBubbleLeftRightIcon,
  UsersIcon,
  ClockIcon,
  BoltIcon,
  HandThumbUpIcon,
  ArrowTrendingUpIcon
} from '@heroicons/react/24/outline';

interface AnalyticsData {
  period_days: number;
  total_queries: number;
  unique_users: number;
  avg_latency_ms: number;
  cache_hit_rate: number;
  satisfaction_rate: number;
  daily_activity: Record<string, { positive: number; negative: number }>;
}

interface AnalyticsDashboardProps {
  data: AnalyticsData;
}

const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({ data }) => {
  const stats = [
    {
      label: 'Total Queries',
      value: data.total_queries.toLocaleString(),
      icon: ChatBubbleLeftRightIcon,
      color: 'bg-blue-50 text-blue-600'
    },
    {
      label: 'Active Users',
      value: data.unique_users.toLocaleString(),
      icon: UsersIcon,
      color: 'bg-green-50 text-green-600'
    },
    {
      label: 'Avg Latency',
      value: `${data.avg_latency_ms}ms`,
      icon: ClockIcon,
      color: 'bg-purple-50 text-purple-600'
    },
    {
      label: 'Cache Hit Rate',
      value: `${Math.round(data.cache_hit_rate * 100)}%`,
      icon: BoltIcon,
      color: 'bg-yellow-50 text-yellow-600'
    },
    {
      label: 'Satisfaction',
      value: `${Math.round(data.satisfaction_rate)}%`,
      icon: HandThumbUpIcon,
      color: 'bg-pink-50 text-pink-600'
    }
  ];

  // Prepare chart data
  const dates = Object.keys(data.daily_activity).sort();
  const positiveData = dates.map(d => data.daily_activity[d].positive);
  const negativeData = dates.map(d => data.daily_activity[d].negative);
  const maxValue = Math.max(...positiveData, ...negativeData, 1);

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div
              key={stat.label}
              className="p-4 bg-white rounded-lg border shadow-sm"
            >
              <div className={`inline-flex p-2 rounded-lg ${stat.color} mb-2`}>
                <Icon className="h-5 w-5" />
              </div>
              <p className="text-2xl font-bold text-gray-800">{stat.value}</p>
              <p className="text-xs text-gray-500">{stat.label}</p>
            </div>
          );
        })}
      </div>

      {/* Activity Chart */}
      <div className="p-4 bg-white rounded-lg border shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-700">
            Feedback Trend ({data.period_days} days)
          </h3>
          <div className="flex items-center gap-4 text-xs">
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 rounded bg-green-500"></span>
              Positive
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 rounded bg-red-500"></span>
              Negative
            </span>
          </div>
        </div>

        {/* Simple bar chart */}
        <div className="flex items-end gap-1 h-32">
          {dates.map((date, idx) => {
            const positive = data.daily_activity[date].positive;
            const negative = data.daily_activity[date].negative;
            const posHeight = (positive / maxValue) * 100;
            const negHeight = (negative / maxValue) * 100;

            return (
              <div
                key={date}
                className="flex-1 flex flex-col items-center gap-1 group"
                title={`${date}: +${positive} / -${negative}`}
              >
                <div className="w-full flex flex-col-reverse h-full">
                  <div
                    className="w-full bg-green-400 rounded-t transition-all group-hover:bg-green-500"
                    style={{ height: `${posHeight}%` }}
                  />
                </div>
                <div className="w-full flex flex-col h-full">
                  <div
                    className="w-full bg-red-400 rounded-b transition-all group-hover:bg-red-500"
                    style={{ height: `${negHeight}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>

        {/* X-axis labels */}
        <div className="flex justify-between mt-2 text-xs text-gray-400">
          <span>{dates[0]}</span>
          <span>{dates[dates.length - 1]}</span>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
