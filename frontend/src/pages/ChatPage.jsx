import React, { useRef, useEffect, useLayoutEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogOut, ChevronDown, Trash2, Plus, MessageSquare, Clock, X, Edit2, Check } from 'lucide-react';
import useAuthStore from '../store/authStore';
import useAccountStore from '../store/accountStore';
import useChatStore from '../store/chatStore';
import ChatWindow from '../components/ChatWindow';
import InputBar from '../components/InputBar';
import SuggestedQueries from '../components/SuggestedQueries';
import GalaxyBackground from '../components/GalaxyBackground';
import PortalDropdown from '../components/PortalDropdown';

const REGIONS = [
  { value: 'all', label: 'All Regions' },
  { value: 'ap-south-1', label: 'ap-south-1' },
  { value: 'us-east-1', label: 'us-east-1' },
  { value: 'us-east-2', label: 'us-east-2' },
  { value: 'us-west-1', label: 'us-west-1' },
  { value: 'us-west-2', label: 'us-west-2' },
  { value: 'eu-west-1', label: 'eu-west-1' },
  { value: 'eu-west-2', label: 'eu-west-2' },
  { value: 'eu-central-1', label: 'eu-central-1' },
  { value: 'ap-southeast-1', label: 'ap-southeast-1' },
  { value: 'ap-southeast-2', label: 'ap-southeast-2' },
  { value: 'ap-northeast-1', label: 'ap-northeast-1' },
  { value: 'ca-central-1', label: 'ca-central-1' },
  { value: 'sa-east-1', label: 'sa-east-1' },
];

/** Relative timestamp helper */
function relativeTime(isoStr) {
  if (!isoStr) return '';
  const diff = Date.now() - new Date(isoStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(isoStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

// ── Inline-editable session title ────────────────────────────────
function SessionItem({ session, isActive, onSelect, onDelete, locked }) {
  const [hovering, setHovering] = useState(false);
  const [editing, setEditing] = useState(false);
  const [draftTitle, setDraftTitle] = useState(session.title);
  const inputRef = useRef(null);
  const { sessions } = useChatStore();

  // keep draft in sync if title changes externally
  useEffect(() => { setDraftTitle(session.title); }, [session.title]);

  const commitEdit = async () => {
    const trimmed = draftTitle.trim();
    if (!trimmed || trimmed === session.title) { setEditing(false); return; }
    try {
      await import('../lib/api').then(m =>
        m.default.patch(`/api/chats/${session.id}`, { title: trimmed })
      );
      // update local sessions list
      useChatStore.setState(state => ({
        sessions: state.sessions.map(s =>
          s.id === session.id ? { ...s, title: trimmed } : s
        ),
      }));
    } catch { /* noop */ }
    setEditing(false);
  };

  const startEdit = (e) => {
    e.stopPropagation();
    setEditing(true);
    setTimeout(() => inputRef.current?.focus(), 0);
  };

  return (
    <div
      className={`chat-history-item ${isActive ? 'active' : ''} ${locked && !isActive ? 'locked' : ''}`}
      onMouseEnter={() => !locked && setHovering(true)}
      onMouseLeave={() => setHovering(false)}
      onClick={() => !editing && !locked && onSelect(session.id)}
      title={locked && !isActive ? 'Query in progress… click ⏹ Stop to switch chats' : undefined}
    >
      <div className="chat-history-icon">
        <MessageSquare size={12} strokeWidth={1.5} />
      </div>

      <div className="chat-history-body">
        {editing ? (
          <input
            ref={inputRef}
            className="chat-history-title-input"
            value={draftTitle}
            onChange={e => setDraftTitle(e.target.value)}
            onBlur={commitEdit}
            onKeyDown={e => {
              if (e.key === 'Enter') commitEdit();
              if (e.key === 'Escape') { setEditing(false); setDraftTitle(session.title); }
            }}
            onClick={e => e.stopPropagation()}
          />
        ) : (
          <span className="chat-history-title">{session.title || 'New Conversation'}</span>
        )}
        <span className="chat-history-meta">
          <Clock size={9} strokeWidth={1.5} style={{ flexShrink: 0 }} />
          {relativeTime(session.updated_at)}
          {session.message_count > 0 && (
            <span className="chat-history-count">{session.message_count}</span>
          )}
        </span>
      </div>

      {hovering && !editing && !locked && (
        <div className="chat-history-actions" onClick={e => e.stopPropagation()}>
          <button
            className="chat-history-action-btn"
            title="Rename"
            onClick={startEdit}
          >
            <Edit2 size={13} strokeWidth={1.5} />
          </button>
          <button
            className="chat-history-action-btn danger"
            title="Delete"
            onClick={() => onDelete(session.id)}
          >
            <X size={13} strokeWidth={1.5} />
          </button>
        </div>
      )}
    </div>
  );
}

// ── Main ChatPage ─────────────────────────────────────────────────
const ChatPage = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const { accounts, selectedAccount, selectAccount, fetchAccounts } = useAccountStore();
  const {
    messages, isLoading, clearMessages,
    selectedRegion, setRegion,
    sessions, sessionsLoading, fetchSessions,
    activeSessionId, loadSession, newSession, deleteSession,
  } = useChatStore();

  const accountBtnRef = useRef(null);
  const regionBtnRef = useRef(null);
  const scrollRef = useRef(null);
  const [accountOpen, setAccountOpen] = useState(false);
  const [regionOpen, setRegionOpen] = useState(false);
  const [showAllAccounts, setShowAllAccounts] = useState(false);

  useEffect(() => { fetchAccounts(); }, [fetchAccounts]);
  useEffect(() => { fetchSessions(); }, [fetchSessions]);

  useLayoutEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    if (messages.length === 0) return;
    el.scrollTop = el.scrollHeight;
  }, [messages, isLoading]);

  const handleLogout = () => { logout(); navigate('/login'); };

  const handleNewChat = async () => {
    const sessionId = await newSession();
    // sessionId may be null if not logged in — gracefully handled
  };

  const accountItems = accounts.map(acc => ({
    value: acc.id,
    label: acc.nickname,
    meta: acc.region === 'all' ? 'All Regions' : acc.region,
    active: selectedAccount?.id === acc.id,
  }));

  const currentRegionLabel = REGIONS.find(r => r.value === selectedRegion)?.label || selectedRegion;

  // Filter sessions: by default show only the selected account's chats
  const filteredSessions = showAllAccounts || !selectedAccount
    ? sessions
    : sessions.filter(s => s.account_id === selectedAccount.id);
  const hiddenCount = sessions.length - filteredSessions.length;

  return (
    <div className="chat-layout" style={{ position: 'relative' }}>
      <GalaxyBackground variant="chat" />

      {/* ── Sidebar ───────────────────────────────────────────── */}
      <aside className="sidebar" style={{ position: 'relative', zIndex: 2 }}>

        {/* Wordmark */}
        <div className="sidebar-logo">
          <span className="sidebar-wordmark">
            CloudComply <span className="ai">AI</span>
          </span>
        </div>

        {/* Account selector */}
        <div className="sidebar-section">
          <div className="sidebar-label">Account</div>
          <button
            ref={accountBtnRef}
            className="dropdown-pill"
            onClick={() => { setAccountOpen(v => !v); setRegionOpen(false); }}
            disabled={accounts.length === 0 || isLoading}
            title={isLoading ? 'Query in progress…' : undefined}
          >
            <span className="dropdown-pill-text">
              {selectedAccount ? selectedAccount.nickname : accounts.length === 0 ? 'No accounts' : 'Select account'}
            </span>
            <ChevronDown size={13} strokeWidth={1.5} style={{
              color: 'var(--text-dim)', flexShrink: 0,
              transform: accountOpen ? 'rotate(180deg)' : 'none',
              transition: 'transform 0.2s',
            }} />
          </button>
        </div>

        {/* Region selector */}
        <div className="sidebar-section" style={{ marginTop: 6 }}>
          <div className="sidebar-label">Region</div>
          <button
            ref={regionBtnRef}
            className="dropdown-pill"
            onClick={() => { setRegionOpen(v => !v); setAccountOpen(false); }}
          >
            <span className="dropdown-pill-text">{currentRegionLabel}</span>
            <ChevronDown size={13} strokeWidth={1.5} style={{
              color: 'var(--text-dim)', flexShrink: 0,
              transform: regionOpen ? 'rotate(180deg)' : 'none',
              transition: 'transform 0.2s',
            }} />
          </button>
        </div>

        {/* Manage accounts link */}
        <div className="sidebar-section" style={{ marginTop: 6 }}>
          <button
            className="sidebar-nav-item"
            onClick={() => navigate('/dashboard')}
            style={{ fontSize: '0.8rem', width: '100%' }}
          >
            <Plus size={13} strokeWidth={1.5} style={{ flexShrink: 0 }} />
            Manage accounts
          </button>
        </div>

        <div className="sidebar-divider" />

        {/* ── Chat History ────────────────────────────────────── */}
        <div style={{ padding: '0 14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
          <div className="sidebar-label" style={{ margin: 0 }}>Conversations</div>
          <button
            className="new-chat-btn"
            onClick={handleNewChat}
            disabled={isLoading}
            title={isLoading ? 'Query in progress…' : 'New conversation'}
          >
            <Plus size={12} strokeWidth={2} />
          </button>
        </div>

        {/* Account filter toggle pills */}
        {sessions.length > 0 && selectedAccount && (
          <div style={{ padding: '0 14px 6px', display: 'flex', alignItems: 'center', gap: 5 }}>
            <button
              className={`history-filter-pill ${!showAllAccounts ? 'active' : ''}`}
              onClick={() => setShowAllAccounts(false)}
            >
              {selectedAccount.nickname}
            </button>
            <button
              className={`history-filter-pill ${showAllAccounts ? 'active' : ''}`}
              onClick={() => setShowAllAccounts(true)}
            >
              All{hiddenCount > 0 && !showAllAccounts && (
                <span className="filter-pill-badge">+{hiddenCount}</span>
              )}
            </button>
          </div>
        )}

        {/* Sessions list */}
        <div className="chat-history-list">
          {sessionsLoading && sessions.length === 0 ? (
            <div className="chat-history-empty">Loading…</div>
          ) : filteredSessions.length === 0 ? (
            <div className="chat-history-empty">
              {sessions.length === 0
                ? 'No conversations yet'
                : `No chats for ${selectedAccount?.nickname}`}
            </div>
          ) : (
            filteredSessions.map(session => (
              <SessionItem
                key={session.id}
                session={session}
                isActive={session.id === activeSessionId}
                onSelect={loadSession}
                onDelete={deleteSession}
                locked={isLoading}
              />
            ))
          )}
        </div>


        {/* Clear current conversation */}
        {messages.length > 0 && (
          <>
            <div className="sidebar-divider" />
            <div className="sidebar-section">
              <button
                className="sidebar-nav-item"
                onClick={clearMessages}
                style={{ color: 'rgba(248,113,113,0.6)', fontSize: '0.82rem', width: '100%' }}
              >
                <Trash2 size={14} strokeWidth={1.5} style={{ flexShrink: 0 }} />
                Clear conversation
              </button>
            </div>
          </>
        )}

        {/* Bottom — user + logout */}
        <div className="sidebar-bottom">
          <span className="sidebar-user-email">{user?.email}</span>
          <button className="sidebar-logout-btn" onClick={handleLogout} title="Sign out">
            <LogOut size={14} strokeWidth={1.5} />
          </button>
        </div>
      </aside>

      {/* ── Main ──────────────────────────────────────────────── */}
      <main className="chat-main" style={{ position: 'relative', zIndex: 1 }}>

        <div ref={scrollRef} style={{ flex: 1, overflowY: 'auto', position: 'relative' }}>
          <ChatWindow
            emptyState={
              selectedAccount ? (
                <SuggestedQueries accountName={selectedAccount.nickname} />
              ) : (
                <div>
                  <p style={{ fontSize: '2rem', fontWeight: 200, letterSpacing: '-0.04em', color: 'var(--text-primary)', marginBottom: 10 }}>
                    No account selected
                  </p>
                  <p style={{ color: 'var(--text-muted)', fontWeight: 300, marginBottom: 24 }}>
                    Choose an account in the sidebar to start investigating.
                  </p>
                  <button
                    onClick={() => navigate('/dashboard')}
                    style={{
                      display: 'inline-flex', alignItems: 'center', gap: 8,
                      padding: '10px 20px', background: 'var(--surface-active)',
                      border: '1px solid var(--glass-border-cta)', color: 'var(--text-primary)',
                      borderRadius: 'var(--r-md)', cursor: 'pointer',
                      fontFamily: 'var(--font-sans)', fontSize: '0.85rem',
                      transition: 'all 0.2s',
                    }}
                  >
                    <Plus size={14} strokeWidth={1.5} />
                    Add an account
                  </button>
                </div>
              )
            }
          />
        </div>

        <div className="chat-input-area" style={{
          opacity: selectedAccount ? 1 : 0.35,
          pointerEvents: selectedAccount ? 'auto' : 'none',
        }}>
          <InputBar />
        </div>
      </main>

      {/* Portal dropdowns */}
      <PortalDropdown
        open={accountOpen}
        anchorRef={accountBtnRef}
        onClose={() => setAccountOpen(false)}
        items={accountItems}
        onSelect={(item) => {
          const acc = accounts.find(a => a.id === item.value);
          if (acc) selectAccount(acc);
          setAccountOpen(false);
        }}
        emptyText="No accounts configured"
      />

      <PortalDropdown
        open={regionOpen}
        anchorRef={regionBtnRef}
        onClose={() => setRegionOpen(false)}
        items={REGIONS.map(r => ({ label: r.label, value: r.value, active: selectedRegion === r.value }))}
        onSelect={(item) => {
          setRegion(item.value);
          setRegionOpen(false);
        }}
      />
    </div>
  );
};

export default ChatPage;
