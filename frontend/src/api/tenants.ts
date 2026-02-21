import api from './client';
import { Tenant, TenantStats } from '../types';

export const tenantApi = {
  getCurrent: async (): Promise<Tenant> => {
    const response = await api.get<Tenant>('/tenants/current');
    return response.data;
  },

  getCurrentStats: async (): Promise<TenantStats> => {
    const response = await api.get<TenantStats>('/tenants/current/stats');
    return response.data;
  },

  update: async (data: { name?: string }): Promise<Tenant> => {
    const response = await api.patch<Tenant>('/tenants/current', data);
    return response.data;
  },
};
