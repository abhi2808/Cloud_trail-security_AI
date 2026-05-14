import React, { useRef, useEffect, useLayoutEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogOut, ChevronDown, Trash2, Plus } from 'lucide-react';
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

const ChatPage = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const { accounts, selectedAccount, selectAccount, fetchAccounts } = useAccountStore();
  const { messages, isLoading, clearMessages, selectedRegion, setRegion } = useChatStore();

  const accountBtnRef = useRef(null);
  const regionBtnRef = useRef(null);
  const scrollRef = useRef(null);
  const prevMsgCount = useRef(0);
  const [accountOpen, setAccountOpen] = React.useState(false);
  const [regionOpen, setRegionOpen] = React.useState(false);

  useEffect(() => { fetchAccounts(); }, [fetchAccounts]);

  useLayoutEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    if (messages.length === 0) { prevMsgCount.current = 0; return; }
    el.scrollTop = el.scrollHeight;
    prevMsgCount.current = messages.length;
  }, [messages, isLoading]);

  const handleLogout = () => { logout(); navigate('/login'); };

  const accountItems = accounts.map(acc => ({
    value: acc.id,
    label: acc.nickname,
    meta: acc.region === 'all' ? 'All Regions' : acc.region,
    active: selectedAccount?.id === acc.id,
  }));

  const currentRegionLabel = REGIONS.find(r => r.value === selectedRegion)?.label || selectedRegion;

  return (
    <div className="chat-layout" style={{ position: 'relative' }}>
      <GalaxyBackground variant="chat" />

      {/* ── Sidebar ─────────────────────────────────────────── */}
      <aside className="sidebar" style={{ position: 'relative', zIndex: 2 }}>

        {/* Wordmark — bigger, no icon */}
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
            disabled={accounts.length === 0}
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

        {/* Region selector — sits below account, pushed down naturally */}
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

        {/* Clear conversation */}
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

      {/* ── Main — no header bar ────────────────────────────── */}
      <main className="chat-main" style={{ position: 'relative', zIndex: 1 }}>

        {/* Single stable scroll container */}
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

        {/* Input */}
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
