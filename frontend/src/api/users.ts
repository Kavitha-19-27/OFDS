import api from './client';

export interface UserData {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface UserListResponse {
  users: UserData[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface CreateUserData {
  email: string;
  password: string;
  full_name?: string;
  role?: string;
}

export const usersApi = {
  // Get all users (admin only)
  getUsers: async (page = 1, pageSize = 20): Promise<UserListResponse> => {
    const response = await api.get<UserListResponse>('/users', {
      params: { page, page_size: pageSize }
    });
    return response.data;
  },

  // Get single user
  getUser: async (userId: string): Promise<UserData> => {
    const response = await api.get<UserData>(`/users/${userId}`);
    return response.data;
  },

  // Create new user (admin only)
  createUser: async (data: CreateUserData): Promise<UserData> => {
    const response = await api.post<UserData>('/users', data);
    return response.data;
  },

  // Update user
  updateUser: async (userId: string, data: Partial<CreateUserData>): Promise<UserData> => {
    const response = await api.patch<UserData>(`/users/${userId}`, data);
    return response.data;
  },

  // Delete user (admin only)
  deleteUser: async (userId: string): Promise<void> => {
    await api.delete(`/users/${userId}`);
  },

  // Toggle user active status
  toggleUserStatus: async (userId: string, isActive: boolean): Promise<UserData> => {
    const response = await api.patch<UserData>(`/users/${userId}/status`, { is_active: isActive });
    return response.data;
  },
};
