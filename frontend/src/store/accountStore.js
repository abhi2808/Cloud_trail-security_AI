import { create } from 'zustand';
import api from '../lib/api';

const useAccountStore = create((set, get) => ({
  accounts: [],
  selectedAccount: null,
  isLoading: false,

  fetchAccounts: async () => {
    set({ isLoading: true });
    try {
      const response = await api.get('/api/accounts');
      set({ accounts: response.data, isLoading: false });
    } catch (error) {
      set({ isLoading: false });
      console.error('Failed to fetch accounts', error);
    }
  },

  addAccount: async (accountData) => {
    set({ isLoading: true });
    try {
      const response = await api.post('/api/accounts', accountData);
      set(state => ({ 
        accounts: [...state.accounts, response.data],
        isLoading: false 
      }));
      return true;
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  testConnection: async (accountData) => {
    try {
      const response = await api.post('/api/accounts/test', accountData);
      return response.data;
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.message || error.response?.data?.detail || "Connection failed to verify."
      };
    }
  },

  deleteAccount: async (accountId) => {
    try {
      await api.delete(`/api/accounts/${accountId}`);
      set(state => {
        const newAccounts = state.accounts.filter(a => a.id !== accountId);
        const newSelected = state.selectedAccount?.id === accountId ? null : state.selectedAccount;
        return { 
          accounts: newAccounts,
          selectedAccount: newSelected
        };
      });
    } catch (error) {
      console.error('Failed to delete account', error);
      throw error;
    }
  },

  selectAccount: (account) => {
    set({ selectedAccount: account });
  }
}));

export default useAccountStore;
