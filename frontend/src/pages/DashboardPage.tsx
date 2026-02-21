import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  DocumentTextIcon,
  ChatBubbleLeftRightIcon,
  CubeIcon,
  ArrowTrendingUpIcon,
  SparklesIcon,
  CloudArrowUpIcon,
  BoltIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import { tenantApi } from '../api/tenants';
import { TenantStats } from '../types';
import { LoadingSpinner } from '../components/common';

const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<TenantStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [greeting, setGreeting] = useState('');

  useEffect(() => {
    const hour = new Date().getHours();
    if (hour < 12) setGreeting('Good morning');
    else if (hour < 17) setGreeting('Good afternoon');
    else setGreeting('Good evening');

    const loadStats = async () => {
      try {
        const data = await tenantApi.getCurrentStats();
        setStats(data);
      } catch (err) {
        console.error('Failed to load stats:', err);
      } finally {
        setIsLoading(false);
      }
    };
    loadStats();
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full bg-gradient-to-br from-slate-50 to-blue-50 dark:from-gray-900 dark:to-gray-800">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <p className="mt-4 text-gray-500 dark:text-gray-400 animate-pulse">Loading your workspace...</p>
        </div>
      </div>
    );
  }

  const statCards = [
    {
      name: 'Documents',
      value: stats?.document_count ?? 0,
      icon: DocumentTextIcon,
      gradient: 'from-blue-500 to-cyan-400',
      bgGradient: 'from-blue-50 to-cyan-50',
      link: '/documents',
      description: 'Total uploaded files',
    },
    {
      name: 'Knowledge Chunks',
      value: stats?.total_chunks ?? 0,
      icon: CubeIcon,
      gradient: 'from-purple-500 to-pink-400',
      bgGradient: 'from-purple-50 to-pink-50',
      description: 'Indexed segments',
    },
    {
      name: 'Queries Today',
      value: stats?.query_count_today ?? 0,
      icon: ChatBubbleLeftRightIcon,
      gradient: 'from-emerald-500 to-teal-400',
      bgGradient: 'from-emerald-50 to-teal-50',
      link: '/chat',
      description: 'Questions asked today',
    },
    {
      name: 'Total Queries',
      value: stats?.query_count_total ?? 0,
      icon: ArrowTrendingUpIcon,
      gradient: 'from-orange-500 to-amber-400',
      bgGradient: 'from-orange-50 to-amber-50',
      description: 'All-time conversations',
    },
  ];

  const storagePercentage = stats ? Math.min((stats.storage_used_mb / 500) * 100, 100) : 0;

  return (
    <div className="min-h-full bg-gradient-to-br from-slate-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6 sm:mb-8 animate-fade-in">
          <div className="flex items-center gap-2 sm:gap-3 mb-1 sm:mb-2">
            <div className="p-1.5 sm:p-2 bg-gradient-to-br from-primary-500 to-primary-600 rounded-lg sm:rounded-xl shadow-lg shadow-primary-500/20">
              <ChartBarIcon className="h-5 w-5 sm:h-6 sm:w-6 text-white" />
            </div>
            <div>
              <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">{greeting} 👋</p>
              <h1 className="text-xl sm:text-3xl font-bold bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 dark:from-white dark:via-gray-200 dark:to-white bg-clip-text text-transparent">
                Dashboard
              </h1>
            </div>
          </div>
          <p className="text-xs sm:text-base text-gray-500 dark:text-gray-400 mt-1 sm:mt-2 ml-9 sm:ml-14">Your RAG application at a glance</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6 mb-6 sm:mb-8">
          {statCards.map((card, index) => (
            <div
              key={card.name}
              className="group relative bg-white dark:bg-gray-800 rounded-xl sm:rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-3 sm:p-6 
                hover:shadow-xl hover:shadow-gray-200/50 dark:hover:shadow-gray-900/50 hover:-translate-y-1 
                transition-all duration-300 overflow-hidden animate-fade-in-up"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className={`absolute -right-4 sm:-right-8 -top-4 sm:-top-8 w-20 h-20 sm:w-32 sm:h-32 bg-gradient-to-br ${card.bgGradient} rounded-full opacity-50 dark:opacity-20 blur-2xl group-hover:opacity-70 dark:group-hover:opacity-30 transition-opacity`} />
              
              <div className="relative">
                <div className="flex items-start justify-between mb-2 sm:mb-4">
                  <div className={`p-2 sm:p-3 bg-gradient-to-br ${card.gradient} rounded-lg sm:rounded-xl shadow-lg`}>
                    <card.icon className="h-4 w-4 sm:h-6 sm:w-6 text-white" />
                  </div>
                  {card.link && (
                    <Link to={card.link} className="text-[10px] sm:text-xs text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors hidden sm:block">
                      View →
                    </Link>
                  )}
                </div>
                <p className="text-[10px] sm:text-sm font-medium text-gray-500 dark:text-gray-400 mb-0.5 sm:mb-1">{card.name}</p>
                <p className="text-xl sm:text-4xl font-bold text-gray-900 dark:text-white mb-0.5 sm:mb-1">{card.value.toLocaleString()}</p>
                <p className="text-[10px] sm:text-xs text-gray-400 dark:text-gray-500 hidden sm:block">{card.description}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
          {/* Quick Actions */}
          <div className="lg:col-span-2 animate-fade-in-up" style={{ animationDelay: '400ms' }}>
            <div className="bg-white dark:bg-gray-800 rounded-xl sm:rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-4 sm:p-6">
              <div className="flex items-center gap-2 mb-4 sm:mb-6">
                <BoltIcon className="h-4 w-4 sm:h-5 sm:w-5 text-amber-500" />
                <h2 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">Quick Actions</h2>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                <Link
                  to="/documents"
                  className="group relative overflow-hidden rounded-lg sm:rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 
                    p-4 sm:p-6 text-white shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-0.5"
                >
                  <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                  <div className="absolute -right-4 -bottom-4 w-16 h-16 sm:w-24 sm:h-24 bg-white/10 rounded-full blur-2xl" />
                  <div className="relative">
                    <div className="bg-white/20 backdrop-blur-sm w-10 h-10 sm:w-12 sm:h-12 rounded-lg flex items-center justify-center mb-3 sm:mb-4 group-hover:scale-110 transition-transform">
                      <CloudArrowUpIcon className="h-5 w-5 sm:h-6 sm:w-6" />
                    </div>
                    <h3 className="font-semibold text-base sm:text-lg mb-0.5 sm:mb-1">Upload Documents</h3>
                    <p className="text-xs sm:text-sm text-white/80">Add PDFs, DOCX, or TXT files</p>
                  </div>
                </Link>
                <Link
                  to="/chat"
                  className="group relative overflow-hidden rounded-lg sm:rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 
                    p-4 sm:p-6 text-white shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-0.5"
                >
                  <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                  <div className="absolute -right-4 -bottom-4 w-16 h-16 sm:w-24 sm:h-24 bg-white/10 rounded-full blur-2xl" />
                  <div className="relative">
                    <div className="bg-white/20 backdrop-blur-sm w-10 h-10 sm:w-12 sm:h-12 rounded-lg flex items-center justify-center mb-3 sm:mb-4 group-hover:scale-110 transition-transform">
                      <SparklesIcon className="h-5 w-5 sm:h-6 sm:w-6" />
                    </div>
                    <h3 className="font-semibold text-base sm:text-lg mb-0.5 sm:mb-1">Start Chatting</h3>
                    <p className="text-xs sm:text-sm text-white/80">Ask AI-powered questions</p>
                  </div>
                </Link>
              </div>
            </div>
          </div>

          {/* Storage */}
          <div className="animate-fade-in-up" style={{ animationDelay: '500ms' }}>
            <div className="bg-white dark:bg-gray-800 rounded-xl sm:rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-4 sm:p-6 h-full">
              <div className="flex items-center gap-2 mb-4 sm:mb-6">
                <div className="p-1 sm:p-1.5 bg-gradient-to-br from-violet-500 to-purple-600 rounded-lg">
                  <CubeIcon className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-white" />
                </div>
                <h2 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">Storage</h2>
              </div>

              <div className="flex flex-col items-center mb-4 sm:mb-6">
                <div className="relative w-24 h-24 sm:w-32 sm:h-32">
                  <svg className="w-full h-full transform -rotate-90">
                    <circle cx="64" cy="64" r="56" fill="none" stroke="#f1f5f9" strokeWidth="12" />
                    <circle
                      cx="64" cy="64" r="56" fill="none" stroke="url(#gradient)" strokeWidth="12" strokeLinecap="round"
                      strokeDasharray={`${storagePercentage * 3.52} 352`}
                      className="transition-all duration-1000 ease-out"
                    />
                    <defs>
                      <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="#8b5cf6" />
                        <stop offset="100%" stopColor="#d946ef" />
                      </linearGradient>
                    </defs>
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-lg sm:text-2xl font-bold text-gray-900 dark:text-white">{stats?.storage_used_mb.toFixed(1) ?? 0}</span>
                    <span className="text-[10px] sm:text-xs text-gray-500 dark:text-gray-400">MB used</span>
                  </div>
                </div>
              </div>

              <div className="space-y-2 sm:space-y-3">
                <div className="flex justify-between text-xs sm:text-sm">
                  <span className="text-gray-500 dark:text-gray-400">Used</span>
                  <span className="font-medium text-gray-900 dark:text-white">{stats?.storage_used_mb.toFixed(2) ?? 0} MB</span>
                </div>
                <div className="flex justify-between text-xs sm:text-sm">
                  <span className="text-gray-500 dark:text-gray-400">Available</span>
                  <span className="font-medium text-gray-900 dark:text-white">500 MB</span>
                </div>
                <div className="pt-2 sm:pt-3 border-t border-gray-200 dark:border-gray-700">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] sm:text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">Plan</span>
                    <span className="px-2 py-0.5 sm:px-2.5 sm:py-1 bg-gradient-to-r from-violet-100 to-purple-100 dark:from-violet-900/50 dark:to-purple-900/50 text-violet-700 dark:text-violet-300 text-[10px] sm:text-xs font-semibold rounded-full">
                      Free Tier
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* CTA Banner */}
        <div className="mt-4 sm:mt-6 animate-fade-in-up" style={{ animationDelay: '600ms' }}>
          <div className="bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 rounded-xl sm:rounded-2xl p-4 sm:p-6 text-white overflow-hidden relative">
            <div className="absolute inset-0 opacity-30" style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%230ea5e9' fill-opacity='0.1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")` }} />
            <div className="relative flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-4">
              <div>
                <h3 className="text-base sm:text-lg font-semibold mb-0.5 sm:mb-1">Ready to explore?</h3>
                <p className="text-gray-400 text-xs sm:text-sm">Upload documents and start asking questions with AI-powered search</p>
              </div>
              <Link
                to="/chat"
                className="flex items-center gap-2 bg-white text-gray-900 px-4 sm:px-5 py-2 sm:py-2.5 rounded-lg sm:rounded-xl text-sm sm:text-base font-medium hover:bg-gray-100 transition-colors shadow-lg"
              >
                <SparklesIcon className="h-4 w-4 sm:h-5 sm:w-5 text-primary-600" />
                Start Chat
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
