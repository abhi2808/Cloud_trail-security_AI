import React from 'react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '../store/authStore';
import useAccountStore from '../store/accountStore';
import useChatStore from '../store/chatStore';
import ChatWindow from '../components/ChatWindow';
import InputBar from '../components/InputBar';
import AccountSelector from '../components/AccountSelector';
import SuggestedQueries from '../components/SuggestedQueries';

const ChatPage = () => {
  const { user, logout } = useAuthStore();
  const { selectedAccount } = useAccountStore();
  const { messages, clearMessages } = useChatStore();
  const navigate = useNavigate();

  const handleLogout = () => { logout(); navigate('/login'); };

  return (
    <div style={{
      height: '100vh', background: 'var(--bg-primary)',
      display: 'flex', flexDirection: 'column', fontFamily: 'var(--font-sans)', overflow: 'hidden',
    }}>
      {/* Navbar */}
      <nav style={{
        background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border)',
        padding: '10px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '34px', height: '34px', borderRadius: '8px',
            background: 'rgba(0,255,136,0.1)', border: '1px solid rgba(0,255,136,0.2)',
            color: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/>
            </svg>
          </div>
          <div>
            <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.2 }}>
              CloudTrail AI Investigator
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          {user?.email && (
            <span style={{ color: 'var(--text-tertiary)', fontSize: '0.78rem', fontFamily: 'var(--font-mono)' }}>
              {user.email}
            </span>
          )}
          <button onClick={handleLogout} style={{
            background: 'none', border: '1px solid var(--border-subtle)',
            color: 'var(--text-secondary)', padding: '5px 12px', borderRadius: '6px',
            cursor: 'pointer', fontSize: '0.8rem', fontFamily: 'var(--font-sans)', transition: 'all 0.2s',
          }}
            onMouseEnter={e => { e.target.style.color = 'var(--text-primary)'; e.target.style.borderColor = 'var(--text-secondary)'; }}
            onMouseLeave={e => { e.target.style.color = 'var(--text-secondary)'; e.target.style.borderColor = 'var(--border-subtle)'; }}
          >
            Logout
          </button>
        </div>
      </nav>

      {/* Account Selector Bar */}
      <AccountSelector />

      {/* Main chat area */}
      <main style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column', position: 'relative' }}>

        {/* Clear button */}
        {messages.length > 0 && (
          <div style={{ position: 'absolute', top: '12px', right: '16px', zIndex: 20 }}>
            <button onClick={clearMessages} title="Clear conversation" style={{
              background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)',
              color: 'var(--text-secondary)', padding: '6px 10px', borderRadius: '6px',
              cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px',
              fontSize: '0.75rem', fontFamily: 'var(--font-sans)', transition: 'all 0.2s',
            }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--error)'; e.currentTarget.style.color = 'var(--error)'; }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border-subtle)'; e.currentTarget.style.color = 'var(--text-secondary)'; }}
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
              </svg>
              Clear
            </button>
          </div>
        )}

        {/* Empty state — show suggestions */}
        {messages.length === 0 && (
          <div style={{
            position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center', padding: '32px',
            pointerEvents: 'none', zIndex: 10,
          }}>
            <div style={{ pointerEvents: 'auto', width: '100%', maxWidth: '640px', textAlign: 'center' }}>
              {selectedAccount ? (
                <>
                  <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px', letterSpacing: '-0.02em' }}>
                    How can I help you investigate?
                  </div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '28px' }}>
                    Investigating <span style={{ color: 'var(--accent)', fontFamily: 'var(--font-mono)' }}>{selectedAccount.nickname}</span>{' '}
                    <span style={{ color: 'var(--text-tertiary)' }}>({selectedAccount.region})</span>
                  </div>
                  <SuggestedQueries />
                </>
              ) : (
                <div style={{ color: 'var(--text-secondary)' }}>
                  <div style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>No account selected</div>
                  Select an AWS account above to start investigating.
                </div>
              )}
            </div>
          </div>
        )}

        {/* Chat messages */}
        <div style={{ flex: 1, overflowY: 'auto' }}>
          <ChatWindow />
        </div>
      </main>

      {/* Input Bar */}
      <footer style={{
        flexShrink: 0, padding: '12px 20px 16px',
        borderTop: '1px solid var(--border)', background: 'var(--bg-secondary)',
      }}>
        <div style={{
          maxWidth: '900px', margin: '0 auto',
          opacity: selectedAccount ? 1 : 0.4,
          pointerEvents: selectedAccount ? 'auto' : 'none',
        }}>
          <InputBar />
        </div>
        {!selectedAccount && (
          <div style={{ textAlign: 'center', marginTop: '6px', fontSize: '0.72rem', color: 'var(--text-tertiary)' }}>
            ↑ Select an AWS account to enable the chat
          </div>
        )}
      </footer>
    </div>
  );
};

export default ChatPage;
