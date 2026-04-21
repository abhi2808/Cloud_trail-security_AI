import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '../store/authStore';
import useAccountStore from '../store/accountStore';
import AddAccountModal from '../components/AddAccountModal';

const s = {
  page: { minHeight: '100vh', background: 'var(--bg-primary)', display: 'flex', flexDirection: 'column', fontFamily: 'var(--font-sans)' },
  nav: { background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border)', padding: '12px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 },
  navTitle: { fontSize: '1.15rem', fontWeight: 700, background: 'linear-gradient(90deg, #58a6ff, #00ff88)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' },
  navRight: { display: 'flex', alignItems: 'center', gap: '20px' },
  navEmail: { color: 'var(--text-secondary)', fontSize: '0.82rem' },
  logoutBtn: { background: 'none', border: '1px solid var(--border-subtle)', color: 'var(--text-secondary)', padding: '5px 12px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.82rem', fontFamily: 'var(--font-sans)', transition: 'all 0.2s' },
  main: { flex: 1, maxWidth: '1100px', width: '100%', margin: '0 auto', padding: '40px 24px' },
  topRow: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '36px', flexWrap: 'wrap', gap: '16px' },
  pageTitle: { fontSize: '2rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.03em', margin: 0 },
  pageSubtitle: { color: 'var(--text-secondary)', fontSize: '0.88rem', marginTop: '6px' },
  addBtn: { display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 20px', background: 'rgba(88,166,255,0.12)', border: '1px solid rgba(88,166,255,0.3)', color: '#58a6ff', borderRadius: '8px', cursor: 'pointer', fontFamily: 'var(--font-sans)', fontSize: '0.88rem', fontWeight: 600, transition: 'all 0.2s', whiteSpace: 'nowrap' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' },
  card: { background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: '12px', padding: '24px', position: 'relative', overflow: 'hidden', transition: 'border-color 0.2s, box-shadow 0.2s' },
  cardTop: { position: 'absolute', top: 0, left: 0, width: '100%', height: '2px', background: 'linear-gradient(90deg, var(--accent), transparent)' },
  cardNick: { fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '16px', paddingRight: '32px' },
  cardMeta: { fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' },
  regionBadge: { background: 'var(--bg-primary)', border: '1px solid var(--border)', padding: '2px 8px', borderRadius: '4px', fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--text-secondary)' },
  cardFooter: { display: 'flex', alignItems: 'center', marginTop: '20px', paddingTop: '16px', borderTop: '1px solid var(--border)' },
  verifiedTag: { display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent)', fontSize: '0.82rem', fontWeight: 500 },
  unverifiedTag: { display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--warning)', fontSize: '0.82rem', fontWeight: 500 },
  deleteBtn: { position: 'absolute', top: '16px', right: '16px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)', padding: '4px', borderRadius: '4px', display: 'flex', transition: 'color 0.2s' },
  emptyCard: { background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: '16px', padding: '48px 24px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center' },
  emptyIcon: { width: '64px', height: '64px', borderRadius: '50%', background: 'var(--accent-glow)', border: '1px solid rgba(0,255,136,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent)', marginBottom: '20px' },
  emptyTitle: { fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px' },
  emptySubtitle: { color: 'var(--text-secondary)', fontSize: '0.88rem', maxWidth: '360px', marginBottom: '24px' },
  proceedBtn: { display: 'flex', alignItems: 'center', gap: '10px', padding: '14px 32px', background: 'rgba(0,255,136,0.12)', border: '1px solid rgba(0,255,136,0.3)', color: 'var(--accent)', borderRadius: '10px', cursor: 'pointer', fontFamily: 'var(--font-sans)', fontSize: '0.95rem', fontWeight: 700, transition: 'all 0.2s', float: 'right' },
};

const DashboardPage = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const { accounts, fetchAccounts, deleteAccount, isLoading } = useAccountStore();
  const [showAddModal, setShowAddModal] = useState(false);

  useEffect(() => { fetchAccounts(); }, [fetchAccounts]);

  const handleLogout = () => { logout(); navigate('/login'); };
  const handleDelete = async (id) => {
    if (window.confirm('Remove this account?')) {
      try { await deleteAccount(id); } catch { alert('Failed to delete account'); }
    }
  };

  return (
    <div style={s.page}>
      <nav style={s.nav}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ color: 'var(--accent)', display: 'flex' }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/></svg>
          </div>
          <span style={s.navTitle}>CloudTrail AI Investigator</span>
        </div>
        <div style={s.navRight}>
          {user?.email && <span style={s.navEmail}>{user.email}</span>}
          <button style={s.logoutBtn} onClick={handleLogout}
            onMouseEnter={e => { e.target.style.color = 'var(--text-primary)'; e.target.style.borderColor = 'var(--text-secondary)'; }}
            onMouseLeave={e => { e.target.style.color = 'var(--text-secondary)'; e.target.style.borderColor = 'var(--border-subtle)'; }}>
            Logout
          </button>
        </div>
      </nav>

      <main style={s.main}>
        <div style={s.topRow}>
          <div>
            <h2 style={s.pageTitle}>AWS Accounts</h2>
            <p style={s.pageSubtitle}>Manage the accounts you want to investigate</p>
          </div>
          <button style={s.addBtn} onClick={() => setShowAddModal(true)}
            onMouseEnter={e => { e.currentTarget.style.background = 'rgba(88,166,255,0.2)'; }}
            onMouseLeave={e => { e.currentTarget.style.background = 'rgba(88,166,255,0.12)'; }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M12 4v16m8-8H4"/></svg>
            Add Account
          </button>
        </div>

        {isLoading && accounts.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '80px 0', color: 'var(--text-tertiary)' }}>Loading accounts...</div>
        ) : accounts.length === 0 ? (
          <div style={s.emptyCard}>
            <div style={s.emptyIcon}>
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/></svg>
            </div>
            <h3 style={s.emptyTitle}>No accounts yet</h3>
            <p style={s.emptySubtitle}>Add your first AWS account to start investigating CloudTrail events with natural language.</p>
            <button style={{...s.addBtn, float: 'none'}} onClick={() => setShowAddModal(true)}>Add Account</button>
          </div>
        ) : (
          <div style={s.grid}>
            {accounts.map(acc => (
              <div key={acc.id} style={s.card}
                onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.boxShadow = 'var(--shadow-md)'; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border-subtle)'; e.currentTarget.style.boxShadow = 'none'; }}>
                <div style={s.cardTop} />
                <button style={s.deleteBtn} onClick={() => handleDelete(acc.id)}
                  onMouseEnter={e => { e.currentTarget.style.color = 'var(--error)'; }}
                  onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-tertiary)'; }}
                  title="Remove account">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                </button>
                <div style={s.cardNick}>{acc.nickname}</div>
                <div style={s.cardMeta}>
                  <span style={{ color: 'var(--text-tertiary)' }}>Region</span>
                  <span style={s.regionBadge}>{acc.region}</span>
                </div>
                <div style={s.cardMeta}>
                  <span style={{ color: 'var(--text-tertiary)' }}>Verified</span>
                  <span>{acc.last_verified ? new Date(acc.last_verified).toLocaleString() : 'Never'}</span>
                </div>
                <div style={s.cardFooter}>
                  {acc.last_verified ? (
                    <span style={s.verifiedTag}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                      Verified
                    </span>
                  ) : (
                    <span style={s.unverifiedTag}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                      Unverified
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {accounts.length > 0 && (
          <div style={{ marginTop: '40px', display: 'flex', justifyContent: 'flex-end' }}>
            <button style={s.proceedBtn} onClick={() => navigate('/chat')}
              onMouseEnter={e => { e.currentTarget.style.background = 'rgba(0,255,136,0.2)'; e.currentTarget.style.boxShadow = '0 0 30px rgba(0,255,136,0.15)'; }}
              onMouseLeave={e => { e.currentTarget.style.background = 'rgba(0,255,136,0.12)'; e.currentTarget.style.boxShadow = 'none'; }}>
              Start Investigating
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg>
            </button>
          </div>
        )}
      </main>

      {showAddModal && <AddAccountModal onClose={() => setShowAddModal(false)} />}
    </div>
  );
};

export default DashboardPage;
