import { useState, useEffect } from 'react';
import { useAuthStore } from '../stores/authStore';
import { Input, Button } from '../components/common';
import { authApi } from '../api/auth';
import { getErrorMessage } from '../api';
import toast from 'react-hot-toast';
import {
  Cog6ToothIcon,
  UserCircleIcon,
  KeyIcon,
  ShieldCheckIcon,
  EnvelopeIcon,
  UserIcon,
  CheckBadgeIcon,
  LockClosedIcon,
  BuildingOfficeIcon,
  CalendarIcon,
} from '@heroicons/react/24/outline';

const SettingsPage: React.FC = () => {
  const { user, isLoading, fetchUser } = useAuthStore();
  const [activeTab, setActiveTab] = useState<'profile' | 'security'>('profile');
  
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  // Fetch user data on mount if not available
  useEffect(() => {
    if (!user) {
      fetchUser();
    }
  }, [user, fetchUser]);

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();

    if (passwordData.newPassword !== passwordData.confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }

    if (passwordData.newPassword.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }

    setIsChangingPassword(true);
    try {
      await authApi.changePassword(
        passwordData.currentPassword,
        passwordData.newPassword
      );
      toast.success('Password changed successfully');
      setPasswordData({
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
      });
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setIsChangingPassword(false);
    }
  };

  const tabs = [
    { id: 'profile' as const, label: 'Profile', icon: UserCircleIcon },
    { id: 'security' as const, label: 'Security', icon: ShieldCheckIcon },
  ];

  if (isLoading) {
    return (
      <div className="min-h-full bg-gray-50 dark:bg-gray-900 p-6 lg:p-8">
        <div className="max-w-3xl mx-auto">
          <div className="animate-pulse space-y-6">
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-32"></div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 space-y-4">
              <div className="h-20 bg-gray-100 dark:bg-gray-700 rounded-lg"></div>
              <div className="h-16 bg-gray-100 dark:bg-gray-700 rounded-lg"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const getInitials = (name?: string | null) => {
    if (!name) return 'U';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  const getRoleBadge = (role?: string | null) => {
    const roleConfig: Record<string, { bg: string; text: string; label: string }> = {
      ADMIN: { bg: 'bg-blue-100', text: 'text-blue-700', label: 'Admin' },
      USER: { bg: 'bg-gray-100', text: 'text-gray-700', label: 'User' },
    };
    const config = roleConfig[role || 'USER'] || roleConfig.USER;
    return config;
  };

  const roleBadge = getRoleBadge(user?.role);

  return (
    <div className="min-h-full bg-gray-50 dark:bg-gray-900 p-4 sm:p-6 lg:p-8">
      <div className="max-w-3xl mx-auto">
        {/* Page Header */}
        <div className="mb-6 sm:mb-8">
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>
          <p className="text-sm sm:text-base text-gray-500 dark:text-gray-400 mt-1">Manage your account and preferences</p>
        </div>

        {/* Tab Navigation */}
        <div className="bg-white dark:bg-gray-800 rounded-lg sm:rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 mb-4 sm:mb-6">
          <div className="flex border-b border-gray-200 dark:border-gray-700">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 sm:gap-2 px-3 sm:px-6 py-3 sm:py-4 text-xs sm:text-sm font-medium border-b-2 -mb-px transition-colors ${
                  activeTab === tab.id
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:border-gray-300'
                }`}
              >
                <tab.icon className="h-4 w-4 sm:h-5 sm:w-5" />
                {tab.label}
              </button>
            ))}
          </div>

          {/* Profile Tab Content */}
          {activeTab === 'profile' && (
            <div className="p-4 sm:p-6">
              {/* User Info Section */}
              <div className="flex flex-col sm:flex-row items-center sm:items-start gap-4 sm:gap-5 pb-6 border-b border-gray-100 dark:border-gray-700">
                <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-full bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center text-white text-lg sm:text-xl font-bold flex-shrink-0">
                  {getInitials(user?.full_name)}
                </div>
                <div className="flex-1 min-w-0 text-center sm:text-left">
                  <div className="flex flex-col sm:flex-row items-center gap-2 sm:gap-3 mb-1">
                    <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white truncate">
                      {user?.full_name || 'User'}
                    </h2>
                    <span className={`inline-flex items-center gap-1 px-2 sm:px-2.5 py-0.5 rounded-full text-xs font-medium ${roleBadge.bg} ${roleBadge.text}`}>
                      <CheckBadgeIcon className="h-3 w-3 sm:h-3.5 sm:w-3.5" />
                      {roleBadge.label}
                    </span>
                  </div>
                  <p className="text-sm sm:text-base text-gray-500 dark:text-gray-400">{user?.email}</p>
                </div>
              </div>

              {/* Profile Details Grid */}
              <div className="pt-4 sm:pt-6 space-y-4">
                <h3 className="text-xs sm:text-sm font-medium text-gray-900 dark:text-gray-100 uppercase tracking-wider">Account Information</h3>
                
                <div className="grid gap-3 sm:gap-4">
                  {/* Email */}
                  <div className="flex items-center gap-3 sm:gap-4 p-3 sm:p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <div className="p-2 sm:p-2.5 bg-white dark:bg-gray-600 rounded-lg shadow-sm">
                      <EnvelopeIcon className="h-4 w-4 sm:h-5 sm:w-5 text-gray-600 dark:text-gray-300" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[10px] sm:text-xs text-gray-500 dark:text-gray-400 mb-0.5">Email Address</p>
                      <p className="text-xs sm:text-sm font-medium text-gray-900 dark:text-white truncate">{user?.email ?? 'Not available'}</p>
                    </div>
                  </div>

                  {/* Full Name */}
                  <div className="flex items-center gap-3 sm:gap-4 p-3 sm:p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <div className="p-2 sm:p-2.5 bg-white dark:bg-gray-600 rounded-lg shadow-sm">
                      <UserIcon className="h-4 w-4 sm:h-5 sm:w-5 text-gray-600 dark:text-gray-300" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[10px] sm:text-xs text-gray-500 dark:text-gray-400 mb-0.5">Full Name</p>
                      <p className="text-xs sm:text-sm font-medium text-gray-900 dark:text-white truncate">{user?.full_name ?? 'Not set'}</p>
                    </div>
                  </div>

                  {/* Role */}
                  <div className="flex items-center gap-3 sm:gap-4 p-3 sm:p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <div className="p-2 sm:p-2.5 bg-white dark:bg-gray-600 rounded-lg shadow-sm">
                      <BuildingOfficeIcon className="h-4 w-4 sm:h-5 sm:w-5 text-gray-600 dark:text-gray-300" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[10px] sm:text-xs text-gray-500 dark:text-gray-400 mb-0.5">Account Role</p>
                      <p className="text-xs sm:text-sm font-medium text-gray-900 dark:text-white capitalize">{user?.role?.replace('_', ' ') ?? 'User'}</p>
                    </div>
                  </div>

                  {/* Account Status */}
                  <div className="flex items-center gap-3 sm:gap-4 p-3 sm:p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <div className="p-2 sm:p-2.5 bg-white dark:bg-gray-600 rounded-lg shadow-sm">
                      <CalendarIcon className="h-4 w-4 sm:h-5 sm:w-5 text-gray-600 dark:text-gray-300" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[10px] sm:text-xs text-gray-500 dark:text-gray-400 mb-0.5">Account Status</p>
                      <p className="text-xs sm:text-sm font-medium text-green-600 flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-green-500 rounded-full"></span>
                        Active
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Security Tab Content */}
          {activeTab === 'security' && (
            <div className="p-4 sm:p-6">
              <div className="max-w-md">
                <div className="flex items-center gap-2 sm:gap-3 mb-4 sm:mb-6">
                  <div className="p-2 sm:p-2.5 bg-amber-100 dark:bg-amber-900/50 rounded-lg">
                    <KeyIcon className="h-4 w-4 sm:h-5 sm:w-5 text-amber-600 dark:text-amber-400" />
                  </div>
                  <div>
                    <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">Change Password</h3>
                    <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">Update your password regularly</p>
                  </div>
                </div>

                <form onSubmit={handlePasswordChange} className="space-y-4">
                  <Input
                    label="Current Password"
                    type="password"
                    value={passwordData.currentPassword}
                    onChange={(e) =>
                      setPasswordData((prev) => ({ ...prev, currentPassword: e.target.value }))
                    }
                    required
                  />
                  <Input
                    label="New Password"
                    type="password"
                    value={passwordData.newPassword}
                    onChange={(e) =>
                      setPasswordData((prev) => ({ ...prev, newPassword: e.target.value }))
                    }
                    required
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400 -mt-2">Must be at least 8 characters</p>
                  <Input
                    label="Confirm New Password"
                    type="password"
                    value={passwordData.confirmPassword}
                    onChange={(e) =>
                      setPasswordData((prev) => ({ ...prev, confirmPassword: e.target.value }))
                    }
                    required
                  />
                  <Button 
                    type="submit" 
                    isLoading={isChangingPassword}
                    className="w-full sm:w-auto"
                  >
                    <LockClosedIcon className="h-4 w-4 mr-2" />
                    Update Password
                  </Button>
                </form>
              </div>

              {/* Security Tips */}
              <div className="mt-6 sm:mt-8 p-3 sm:p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                <h4 className="text-xs sm:text-sm font-medium text-green-800 dark:text-green-200 mb-2 flex items-center gap-2">
                  <ShieldCheckIcon className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                  Password Tips
                </h4>
                <ul className="text-xs sm:text-sm text-green-700 dark:text-green-300 space-y-1 list-disc list-inside">
                  <li>Mix of letters, numbers, special chars</li>
                  <li>Avoid common words or personal info</li>
                  <li>Don't reuse passwords</li>
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
