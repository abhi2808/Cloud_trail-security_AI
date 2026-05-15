import { create } from 'zustand';
import { postQuery } from '../lib/api';
import api from '../lib/api';

// ── API helpers ────────────────────────────────────────────────────
const chatApi = {
  list: () => api.get('/api/chats').then(r => r.data),
  create: (body) => api.post('/api/chats', body).then(r => r.data),
  get: (id) => api.get(`/api/chats/${id}`).then(r => r.data),
  appendMessage: (id, message) =>
    api.post(`/api/chats/${id}/messages`, { message }).then(r => r.data),
  updateTitle: (id, title) =>
    api.patch(`/api/chats/${id}`, { title }).then(r => r.data),
  delete: (id) => api.delete(`/api/chats/${id}`),
  clearMessages: (id) => api.delete(`/api/chats/${id}/messages`).then(r => r.data),
};

// ── Generate a short auto-title from first user message ────────────
function autoTitle(text) {
  const trimmed = text.trim().replace(/\n/g, ' ');
  return trimmed.length > 60 ? trimmed.slice(0, 57) + '…' : trimmed;
}

const useChatStore = create((set, get) => ({
  // ── Session list (sidebar) ─────────────────────────────────────
  sessions: [],           // ChatSessionSummary[]
  sessionsLoading: false,

  // ── Active session ─────────────────────────────────────────────
  activeSessionId: null,
  messages: [],
  isLoading: false,
  selectedRegion: 'all',

  // ── Region ────────────────────────────────────────────────────
  setRegion: (region) => set({ selectedRegion: region }),

  // ── Load sidebar list ──────────────────────────────────────────
  fetchSessions: async () => {
    set({ sessionsLoading: true });
    try {
      const sessions = await chatApi.list();
      set({ sessions, sessionsLoading: false });
    } catch {
      set({ sessionsLoading: false });
    }
  },

  // ── Switch to an existing session ─────────────────────────────
  loadSession: async (sessionId) => {
    if (get().isLoading) return;          // ← locked while query running
    if (get().activeSessionId === sessionId) return;
    try {
      const session = await chatApi.get(sessionId);
      set({
        activeSessionId: sessionId,
        messages: session.messages || [],
        isLoading: false,
      });

      // ── Auto-sync account to match the session ─────────────────
      // If this session belongs to a different account than currently
      // selected, switch the account so queries always use the right keys.
      if (session.account_id) {
        const useAccountStore = (await import('./accountStore')).default;
        const { accounts, selectedAccount } = useAccountStore.getState();
        if (selectedAccount?.id !== session.account_id) {
          const matchingAccount = accounts.find(a => a.id === session.account_id);
          if (matchingAccount) {
            // Bypass the guard in selectAccount (no query running at this point)
            useAccountStore.setState({ selectedAccount: matchingAccount });
          }
        }
      }
    } catch {
      set({ activeSessionId: null, messages: [] });
    }
  },

  // ── Start a brand-new chat ─────────────────────────────────────
  // Does NOT pre-create a session in the DB — the session is created with
  // the correct auto-title when the user sends their first message.
  // Avoids empty placeholder sessions and the rename race condition.
  newSession: () => {
    if (get().isLoading) return;    // ← locked while query running
    set({ activeSessionId: null, messages: [], isLoading: false });
  },

  // ── Delete a session ───────────────────────────────────────────
  deleteSession: async (sessionId) => {
    if (get().isLoading && get().activeSessionId === sessionId) return; // ← can't delete active session while querying
    try {
      await chatApi.delete(sessionId);
      const { activeSessionId, sessions } = get();
      const remaining = sessions.filter(s => s.id !== sessionId);
      const newActive = activeSessionId === sessionId
        ? (remaining[0]?.id || null)
        : activeSessionId;

      set({ sessions: remaining });

      if (activeSessionId === sessionId) {
        if (newActive) {
          await get().loadSession(newActive);
        } else {
          set({ activeSessionId: null, messages: [] });
        }
      }
    } catch { /* noop */ }
  },

  // ── Clear messages (keep session) ─────────────────────────────
  clearMessages: async () => {
    const { activeSessionId } = get();
    if (!activeSessionId) {
      set({ messages: [] });
      return;
    }
    try {
      await chatApi.clearMessages(activeSessionId);
      set({ messages: [] });
      set(state => ({
        sessions: state.sessions.map(s =>
          s.id === activeSessionId ? { ...s, message_count: 0 } : s
        ),
      }));
    } catch {
      set({ messages: [] });
    }
  },

  // ── Send message ───────────────────────────────────────────────
  sendMessage: async (text) => {
    const { messages, activeSessionId } = get();
    const useAccountStore = (await import('./accountStore')).default;
    const { selectedAccount } = useAccountStore.getState();
    const regionToQuery = get().selectedRegion || 'all';

    const userMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };

    // Guard: no account selected
    if (!selectedAccount) {
      set({
        messages: [
          ...messages,
          userMessage,
          {
            id: `error-${Date.now()}`,
            role: 'assistant',
            content: '⚠️ **Error:** Please select an AWS account first.',
            timestamp: new Date().toISOString(),
            rawEvents: [],
            eventsCount: 0,
          },
        ],
        isLoading: false,
      });
      return;
    }

    // ── If no active session, create one with the auto-title ───────
    // This handles both: typing on a blank page AND clicking "New Chat" then typing.
    // The title is set correctly here — no rename step needed.
    let sessionId = activeSessionId;
    if (!sessionId) {
      try {
        const title = autoTitle(text);
        const session = await chatApi.create({
          title,
          account_id: selectedAccount.id,
          region: regionToQuery,
        });
        sessionId = session.id;
        set(state => ({
          sessions: [{ ...session, title, message_count: 0 }, ...state.sessions],
          activeSessionId: sessionId,
        }));
      } catch {
        // continue without persisting — UX not blocked
      }
    }

    set({ messages: [...messages, userMessage], isLoading: true });

    // ── Persist user message ───────────────────────────────────────
    if (sessionId) {
      try {
        await chatApi.appendMessage(sessionId, {
          role: 'user',
          content: text,
          timestamp: userMessage.timestamp,
        });
        set(state => ({
          sessions: state.sessions.map(s =>
            s.id === sessionId
              ? { ...s, message_count: (s.message_count || 0) + 1, updated_at: new Date().toISOString() }
              : s
          ),
        }));
      } catch { /* noop — don't break UX */ }
    }

    // Build conversation history for AI
    const conversationHistory = [...messages, userMessage].map(msg => ({
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

      set(state => ({
        messages: [...state.messages, assistantMessage],
        isLoading: false,
      }));

      // Persist AI response
      if (sessionId) {
        try {
          await chatApi.appendMessage(sessionId, {
            role: 'assistant',
            content: response.answer,
            timestamp: assistantMessage.timestamp,
            severity: response.severity || null,
            evidence: response.evidence || [],
            recommended_actions: response.recommended_actions || [],
            steps_taken: response.steps_taken || [],
            iterations: response.iterations || 0,
            events_count: response.events_count || 0,
          });
          set(state => ({
            sessions: state.sessions.map(s =>
              s.id === sessionId
                ? { ...s, message_count: (s.message_count || 0) + 1, updated_at: new Date().toISOString() }
                : s
            ),
          }));
        } catch { /* noop */ }
      }
    } catch (error) {
      const errorMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `⚠️ **Error:** ${error.response?.data?.detail || error.message || 'Failed to process your query. Please try again.'}`,
        timestamp: new Date().toISOString(),
        rawEvents: [],
        eventsCount: 0,
      };
      set(state => ({
        messages: [...state.messages, errorMessage],
        isLoading: false,
      }));
    }
  },
}));

export default useChatStore;
