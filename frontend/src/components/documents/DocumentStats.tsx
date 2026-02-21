import { DocumentStats as Stats } from '../../types';
import {
  DocumentTextIcon,
  CubeIcon,
  CircleStackIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
} from '@heroicons/react/24/outline';

interface DocumentStatsProps {
  stats: Stats | null;
  isLoading?: boolean;
}

const DocumentStats: React.FC<DocumentStatsProps> = ({ stats, isLoading }) => {
  if (isLoading || !stats) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="animate-pulse rounded-2xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 p-5">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gray-100 dark:bg-gray-700 rounded-xl" />
              <div className="flex-1">
                <div className="h-3 w-16 bg-gray-100 dark:bg-gray-700 rounded mb-2" />
                <div className="h-6 w-12 bg-gray-200 dark:bg-gray-600 rounded" />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  const statItems = [
    {
      name: 'Total Documents',
      value: stats.total_documents,
      icon: DocumentTextIcon,
      iconColor: 'text-blue-600',
      bgColor: 'bg-gradient-to-br from-blue-50 to-blue-100',
      borderColor: 'border-blue-100',
    },
    {
      name: 'Completed',
      value: stats.completed_count,
      icon: CheckCircleIcon,
      iconColor: 'text-green-600',
      bgColor: 'bg-gradient-to-br from-green-50 to-green-100',
      borderColor: 'border-green-100',
    },
    {
      name: 'Failed',
      value: stats.failed_count,
      icon: ExclamationCircleIcon,
      iconColor: 'text-red-600',
      bgColor: 'bg-gradient-to-br from-red-50 to-red-100',
      borderColor: 'border-red-100',
    },
    {
      name: 'Total Chunks',
      value: stats.total_chunks,
      icon: CubeIcon,
      iconColor: 'text-purple-600',
      bgColor: 'bg-gradient-to-br from-purple-50 to-purple-100',
      borderColor: 'border-purple-100',
    },
    {
      name: 'Storage Used',
      value: `${stats.total_storage_mb.toFixed(1)} MB`,
      icon: CircleStackIcon,
      iconColor: 'text-amber-600',
      bgColor: 'bg-gradient-to-br from-amber-50 to-amber-100',
      borderColor: 'border-amber-100',
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
      {statItems.map((item, idx) => (
        <div 
          key={item.name} 
          className="group rounded-2xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 p-5 hover:shadow-lg hover:shadow-gray-100 dark:hover:shadow-gray-900 hover:border-gray-200 dark:hover:border-gray-600 transition-all duration-300"
          style={{ animationDelay: `${idx * 50}ms` }}
        >
          <div className="flex items-center gap-3">
            <div className={`p-3 rounded-xl ${item.bgColor} ${item.borderColor} border group-hover:scale-110 transition-transform duration-300`}>
              <item.icon className={`h-5 w-5 ${item.iconColor}`} />
            </div>
            <div>
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">{item.name}</p>
              <p className="text-xl font-bold text-gray-900 dark:text-white">{item.value}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default DocumentStats;
