import { create } from 'zustand';
import { postQuery } from '../lib/api';

const useChatStore = create((set, get) => ({
  messages: [],
  isLoading: false,
  selectedRegion: 'all',

  setRegion: (region) => set({ selectedRegion: region }),

  sendMessage: async (text) => {
    const { messages } = get();
    const useAccountStore = (await import('./accountStore')).default;
    const { selectedAccount } = useAccountStore.getState();
    const regionToQuery = get().selectedRegion || 'all';

    // Add user message immediately
    const userMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };
    
    if (!selectedAccount) {
      set({
        messages: [
          ...messages,
          userMessage,
          {
            id: `error-${Date.now()}`,
            role: 'assistant',
            content: `⚠️ **Error:** Please select an AWS account first.`,
            timestamp: new Date().toISOString(),
            rawEvents: [],
            eventsCount: 0,
          }
        ],
        isLoading: false
      });
      return;
    }

    set({ messages: [...messages, userMessage], isLoading: true });

    // Build conversation history from existing messages
    const conversationHistory = [...messages, userMessage].map((msg) => ({
      role: msg.role,
      content: msg.content,
    }));

    try {
      const response = await postQuery(text, conversationHistory, regionToQuery, selectedAccount.id);

      const assistantMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        timestamp: new Date().toISOString(),
        severity: response.severity || null,
        evidence: response.evidence || [],
        recommended_actions: response.recommended_actions || [],
        steps_taken: response.steps_taken || [],
        iterations: response.iterations || 0,
        rawEvents: response.raw_events || [],
        eventsCount: response.events_count || 0,
      };

      set((state) => ({
        messages: [...state.messages, assistantMessage],
        isLoading: false,
      }));
    } catch (error) {
      const errorMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `⚠️ **Error:** ${error.response?.data?.detail || error.message || 'Failed to process your query. Please try again.'}`,
        timestamp: new Date().toISOString(),
        rawEvents: [],
        eventsCount: 0,
      };

      set((state) => ({
        messages: [...state.messages, errorMessage],
        isLoading: false,
      }));
    }
  },

  clearMessages: () => set({ messages: [], isLoading: false }),
}));

export default useChatStore;
