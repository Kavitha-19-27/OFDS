import { useEffect, useState } from 'react';
import { usersApi, UserData, CreateUserData } from '../api/users';
import { chatApi, FeedbackListItem, FeedbackStats } from '../api/chat';
import { useAuthStore } from '../stores/authStore';
import { Modal, Button, Input, LoadingSpinner } from '../components/common';
import toast from 'react-hot-toast';
import {
  UsersIcon,
  UserPlusIcon,
  TrashIcon,
  ShieldCheckIcon,
  UserCircleIcon,
  MagnifyingGlassIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ChatBubbleLeftRightIcon,
  HandThumbUpIcon,
  HandThumbDownIcon,
} from '@heroicons/react/24/outline';

type TabType = 'users' | 'feedback';

const AdminPage: React.FC = () => {
  const { user: currentUser } = useAuthStore();
  const isAdmin = currentUser?.role === 'ADMIN';
  const [activeTab, setActiveTab] = useState<TabType>('users');
  
  // Users state
  const [users, setUsers] = useState<UserData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [totalUsers, setTotalUsers] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Feedback state
  const [feedbackList, setFeedbackList] = useState<FeedbackListItem[]>([]);
  const [feedbackStats, setFeedbackStats] = useState<FeedbackStats | null>(null);
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [feedbackPage, setFeedbackPage] = useState(1);
  const [feedbackTotalPages, setFeedbackTotalPages] = useState(1);
  const [feedbackFilter, setFeedbackFilter] = useState<number | undefined>(undefined);
  
  // Modals
  const [showAddModal, setShowAddModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // New user form
  const [newUser, setNewUser] = useState<CreateUserData>({
    email: '',
    password: '',
    full_name: '',
    role: 'USER',
  });

  const loadUsers = async (page = 1) => {
    setIsLoading(true);
    try {
      const response = await usersApi.getUsers(page, 20);
      setUsers(response.users);
      setTotalUsers(response.total);
      setTotalPages(response.total_pages);
      setCurrentPage(page);
    } catch (error) {
      console.error('Failed to load users:', error);
      toast.error('Failed to load users');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  // Load feedback when tab changes or filter changes
  const loadFeedback = async (page = 1) => {
    if (!isAdmin) return;
    setFeedbackLoading(true);
    try {
      const [listResponse, statsResponse] = await Promise.all([
        chatApi.getFeedbackList(page, 20, feedbackFilter),
        chatApi.getFeedbackStats(30),
      ]);
      setFeedbackList(listResponse.feedback);
      setFeedbackPage(page);
      setFeedbackTotalPages(listResponse.total_pages);
      setFeedbackStats(statsResponse);
    } catch (error) {
      console.error('Failed to load feedback:', error);
    } finally {
      setFeedbackLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'feedback' && isAdmin) {
      loadFeedback();
    }
  }, [activeTab, feedbackFilter, isAdmin]);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await usersApi.createUser(newUser);
      toast.success('User created successfully!');
      setShowAddModal(false);
      setNewUser({ email: '', password: '', full_name: '', role: 'USER' });
      loadUsers(currentPage);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create user');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteUser = async () => {
    if (!showDeleteModal) return;
    setIsSubmitting(true);
    try {
      await usersApi.deleteUser(showDeleteModal);
      toast.success('User deleted');
      setShowDeleteModal(null);
      loadUsers(currentPage);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to delete user');
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredUsers = users.filter(user => 
    user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    user.full_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-full bg-gradient-to-br from-slate-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 sm:mb-8">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-xl shadow-lg shadow-purple-500/20">
              {activeTab === 'users' ? (
                <UsersIcon className="h-6 w-6 text-white" />
              ) : (
                <ChatBubbleLeftRightIcon className="h-6 w-6 text-white" />
              )}
            </div>
            <div>
              <h1 className="text-xl sm:text-3xl font-bold bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 dark:from-white dark:via-gray-100 dark:to-white bg-clip-text text-transparent">
                {activeTab === 'users' ? 'Team Members' : 'AI Feedback'}
              </h1>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {activeTab === 'users' 
                  ? `${totalUsers} total users in your organization`
                  : 'View and manage user feedback on AI responses'}
              </p>
            </div>
          </div>
          {isAdmin && activeTab === 'users' && (
            <Button 
              onClick={() => setShowAddModal(true)}
              className="flex items-center gap-2 bg-gradient-to-r from-primary-600 to-purple-600"
            >
              <UserPlusIcon className="h-5 w-5" />
              <span className="hidden sm:inline">Add User</span>
              <span className="sm:hidden">Add</span>
            </Button>
          )}
        </div>

        {/* Tabs - Admin only for feedback */}
        {isAdmin && (
          <div className="flex gap-2 mb-6">
            <button
              onClick={() => setActiveTab('users')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'users'
                  ? 'bg-primary-600 text-white'
                  : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <UsersIcon className="h-4 w-4" />
              Users
            </button>
            <button
              onClick={() => setActiveTab('feedback')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'feedback'
                  ? 'bg-primary-600 text-white'
                  : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <ChatBubbleLeftRightIcon className="h-4 w-4" />
              Feedback
            </button>
          </div>
        )}

        {/* Users Tab Content */}
        {activeTab === 'users' && (
          <>
            {/* Stats Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mb-6">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-100 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <UsersIcon className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{totalUsers}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">Total Users</p>
              </div>
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-100 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                <ShieldCheckIcon className="h-5 w-5 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {users.filter(u => u.is_active).length}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">Active</p>
              </div>
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-100 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                <ShieldCheckIcon className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {users.filter(u => u.role === 'ADMIN').length}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">Admins</p>
              </div>
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-100 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-100 dark:bg-amber-900/30 rounded-lg">
                <UserCircleIcon className="h-5 w-5 text-amber-600 dark:text-amber-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {users.filter(u => u.role === 'USER').length}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">Users</p>
              </div>
            </div>
          </div>
        </div>

        {/* Search */}
        <div className="mb-4">
          <div className="relative max-w-md">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search users..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
            />
          </div>
        </div>

        {/* Users Table */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 overflow-hidden">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <LoadingSpinner size="lg" />
            </div>
          ) : filteredUsers.length === 0 ? (
            <div className="text-center py-12">
              <UsersIcon className="h-12 w-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
              <p className="text-gray-500 dark:text-gray-400">No users found</p>
            </div>
          ) : (
            <>
              {/* Desktop Table */}
              <div className="hidden sm:block overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 dark:bg-gray-700/50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">User</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Role</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Joined</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                    {filteredUsers.map((user) => (
                      <tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center text-white font-medium">
                              {user.full_name?.charAt(0) || user.email.charAt(0).toUpperCase()}
                            </div>
                            <div>
                              <p className="font-medium text-gray-900 dark:text-white">{user.full_name || 'No name'}</p>
                              <p className="text-sm text-gray-500 dark:text-gray-400">{user.email}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${
                            user.role === 'ADMIN' 
                              ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
                              : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                          }`}>
                            <ShieldCheckIcon className="h-3.5 w-3.5" />
                            {user.role}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
                            user.is_active
                              ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                              : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
                          }`}>
                            <span className={`w-1.5 h-1.5 rounded-full ${user.is_active ? 'bg-green-500' : 'bg-red-500'}`} />
                            {user.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                          {new Date(user.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right">
                          {isAdmin && user.id !== currentUser?.id && (
                            <button
                              onClick={() => setShowDeleteModal(user.id)}
                              className="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                              title="Delete user"
                            >
                              <TrashIcon className="h-4 w-4" />
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Mobile Cards */}
              <div className="sm:hidden divide-y divide-gray-100 dark:divide-gray-700">
                {filteredUsers.map((user) => (
                  <div key={user.id} className="p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center text-white font-medium flex-shrink-0">
                          {user.full_name?.charAt(0) || user.email.charAt(0).toUpperCase()}
                        </div>
                        <div className="min-w-0">
                          <p className="font-medium text-gray-900 dark:text-white truncate">{user.full_name || 'No name'}</p>
                          <p className="text-sm text-gray-500 dark:text-gray-400 truncate">{user.email}</p>
                        </div>
                      </div>
                      {isAdmin && user.id !== currentUser?.id && (
                        <button
                          onClick={() => setShowDeleteModal(user.id)}
                          className="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                    <div className="flex items-center gap-2 mt-3">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
                        user.role === 'ADMIN' 
                          ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                      }`}>
                        {user.role}
                      </span>
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
                        user.is_active
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                          : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
                      }`}>
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 sm:px-6 py-4 border-t border-gray-100 dark:border-gray-700">
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Page {currentPage} of {totalPages}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => loadUsers(currentPage - 1)}
                  disabled={currentPage === 1}
                >
                  <ChevronLeftIcon className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => loadUsers(currentPage + 1)}
                  disabled={currentPage === totalPages}
                >
                  <ChevronRightIcon className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </div>
          </>
        )}

        {/* Feedback Tab Content */}
        {activeTab === 'feedback' && isAdmin && (
          <>
            {/* Feedback Stats */}
            {feedbackStats && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mb-6">
                <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-100 dark:border-gray-700">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                      <ChatBubbleLeftRightIcon className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">{feedbackStats.total_feedback}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">Total Feedback</p>
                    </div>
                  </div>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-100 dark:border-gray-700">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                      <HandThumbUpIcon className="h-5 w-5 text-green-600 dark:text-green-400" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">{feedbackStats.positive}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">Positive</p>
                    </div>
                  </div>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-100 dark:border-gray-700">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-red-100 dark:bg-red-900/30 rounded-lg">
                      <HandThumbDownIcon className="h-5 w-5 text-red-600 dark:text-red-400" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">{feedbackStats.negative}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">Negative</p>
                    </div>
                  </div>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-100 dark:border-gray-700">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                      <ShieldCheckIcon className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">{feedbackStats.satisfaction_rate}%</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">Satisfaction</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Filter */}
            <div className="flex gap-2 mb-4">
              <button
                onClick={() => setFeedbackFilter(undefined)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  feedbackFilter === undefined
                    ? 'bg-gray-800 dark:bg-white text-white dark:text-gray-900'
                    : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setFeedbackFilter(1)}
                className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  feedbackFilter === 1
                    ? 'bg-green-600 text-white'
                    : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300'
                }`}
              >
                <HandThumbUpIcon className="h-4 w-4" /> Positive
              </button>
              <button
                onClick={() => setFeedbackFilter(-1)}
                className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  feedbackFilter === -1
                    ? 'bg-red-600 text-white'
                    : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300'
                }`}
              >
                <HandThumbDownIcon className="h-4 w-4" /> Negative
              </button>
            </div>

            {/* Feedback List */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 overflow-hidden">
              {feedbackLoading ? (
                <div className="flex items-center justify-center py-12">
                  <LoadingSpinner size="lg" />
                </div>
              ) : feedbackList.length === 0 ? (
                <div className="text-center py-12">
                  <ChatBubbleLeftRightIcon className="h-12 w-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                  <p className="text-gray-500 dark:text-gray-400">No feedback yet</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-100 dark:divide-gray-700">
                  {feedbackList.map((fb) => (
                    <div key={fb.id} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <div className={`p-2 rounded-full ${
                            fb.rating === 1
                              ? 'bg-green-100 dark:bg-green-900/30'
                              : 'bg-red-100 dark:bg-red-900/30'
                          }`}>
                            {fb.rating === 1 ? (
                              <HandThumbUpIcon className="h-5 w-5 text-green-600 dark:text-green-400" />
                            ) : (
                              <HandThumbDownIcon className="h-5 w-5 text-red-600 dark:text-red-400" />
                            )}
                          </div>
                          <div>
                            <p className="font-medium text-gray-900 dark:text-white">
                              {fb.user_name || fb.user_email}
                            </p>
                            <p className="text-sm text-gray-500 dark:text-gray-400">
                              {new Date(fb.created_at).toLocaleDateString()} at {new Date(fb.created_at).toLocaleTimeString()}
                            </p>
                          </div>
                        </div>
                        {fb.issue_type && (
                          <span className="px-2 py-1 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 text-xs font-medium rounded-full">
                            {fb.issue_type}
                          </span>
                        )}
                      </div>
                      {fb.feedback_text && (
                        <p className="mt-2 ml-12 text-gray-600 dark:text-gray-300 text-sm">
                          "{fb.feedback_text}"
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Feedback Pagination */}
              {feedbackTotalPages > 1 && (
                <div className="flex items-center justify-between px-4 sm:px-6 py-4 border-t border-gray-100 dark:border-gray-700">
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Page {feedbackPage} of {feedbackTotalPages}
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => loadFeedback(feedbackPage - 1)}
                      disabled={feedbackPage === 1}
                    >
                      <ChevronLeftIcon className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => loadFeedback(feedbackPage + 1)}
                      disabled={feedbackPage === feedbackTotalPages}
                    >
                      <ChevronRightIcon className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Add User Modal */}
      <Modal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        title="Add New User"
        size="md"
      >
        <form onSubmit={handleCreateUser} className="space-y-4">
          <Input
            label="Email"
            type="email"
            value={newUser.email}
            onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
            required
            placeholder="user@example.com"
          />
          <Input
            label="Full Name"
            type="text"
            value={newUser.full_name || ''}
            onChange={(e) => setNewUser({ ...newUser, full_name: e.target.value })}
            placeholder="John Doe"
          />
          <Input
            label="Password"
            type="password"
            value={newUser.password}
            onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
            required
            placeholder="••••••••"
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Role
            </label>
            <select
              value={newUser.role}
              onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
            >
              <option value="USER">User</option>
              <option value="ADMIN">Admin</option>
            </select>
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="ghost" onClick={() => setShowAddModal(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={isSubmitting}>
              <UserPlusIcon className="h-4 w-4 mr-2" />
              Create User
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!showDeleteModal}
        onClose={() => setShowDeleteModal(null)}
        title="Delete User"
        size="sm"
      >
        <div className="text-center py-4">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full mb-4">
            <TrashIcon className="h-8 w-8 text-red-600 dark:text-red-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Delete this user?</h3>
          <p className="text-gray-500 dark:text-gray-400 mb-6">
            This action cannot be undone. The user will lose access immediately.
          </p>
          <div className="flex justify-center gap-3">
            <Button variant="ghost" onClick={() => setShowDeleteModal(null)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleDeleteUser} isLoading={isSubmitting}>
              Delete User
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default AdminPage;
