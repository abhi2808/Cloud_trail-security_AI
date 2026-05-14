import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Shield, Plus, ArrowRight, CheckCircle, AlertCircle, Trash2, LogOut, MessageSquare } from 'lucide-react';
import useAuthStore from '../store/authStore';
import useAccountStore from '../store/accountStore';
import AddAccountModal from '../components/AddAccountModal';
import GalaxyBackground from '../components/GalaxyBackground';

const ease = [0.16, 1, 0.3, 1];

const cardVariants = {
  initial: { opacity: 0, y: 20, filter: 'blur(4px)' },
  animate: (i) => ({
    opacity: 1, y: 0, filter: 'blur(0px)',
    transition: { duration: 0.55, ease, delay: i * 0.07 },
  }),
};

const DashboardPage = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const { accounts, fetchAccounts, deleteAccount, isLoading } = useAccountStore();
  const [showAddModal, setShowAddModal] = useState(false);

  useEffect(() => { fetchAccounts(); }, [fetchAccounts]);

  const handleLogout = () => { logout(); navigate('/login'); };
  const handleDelete = async (id) => {
    if (window.confirm('Remove this AWS account?')) {
      try { await deleteAccount(id); } catch { alert('Failed to delete account'); }
    }
  };

  return (
    <div className="dashboard-layout" style={{ position: 'relative' }}>
      <GalaxyBackground variant="chat" />

      {/* Nav */}
      <nav className="dash-nav" style={{ position: 'relative', zIndex: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Shield size={18} strokeWidth={1.5} style={{ color: 'var(--text-muted)' }} />
          <span className="dash-nav-logo">CloudComply <span className="ai">AI</span></span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          {user?.email && (
            <span style={{ color: 'var(--text-dim)', fontSize: '0.78rem', fontFamily: 'var(--font-mono)' }}>
              {user.email}
            </span>
          )}
          <button
            onClick={handleLogout}
            style={{
              background: 'none', border: '1px solid rgba(255,255,255,0.08)', color: 'var(--text-muted)',
              padding: '5px 12px', borderRadius: 'var(--r-sm)', cursor: 'pointer',
              fontSize: '0.8rem', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', gap: 6,
              transition: 'all 0.2s',
            }}
            onMouseEnter={e => { e.currentTarget.style.color = 'var(--text-primary)'; e.currentTarget.style.borderColor = 'rgba(255,255,255,0.18)'; }}
            onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-muted)'; e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)'; }}
          >
            <LogOut size={13} strokeWidth={1.5} />
            Sign out
          </button>
        </div>
      </nav>

      {/* Main */}
      <main className="dash-main" style={{ position: 'relative', zIndex: 1 }}>
        <motion.div
          initial={{ opacity: 0, y: 16, filter: 'blur(4px)' }}
          animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          transition={{ duration: 0.55, ease }}
        >
          <div className="dash-toprow">
            <div>
              <h2 className="dash-page-title">AWS Accounts</h2>
              <p className="dash-page-sub">Manage accounts for investigation</p>
            </div>
            <button className="dash-add-btn" onClick={() => setShowAddModal(true)}>
              <Plus size={15} strokeWidth={2} />
              Add Account
            </button>
          </div>
        </motion.div>

        {isLoading && accounts.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '80px 0', color: 'var(--text-dim)', fontSize: '0.85rem' }}>
            Loading accounts...
          </div>
        ) : accounts.length === 0 ? (
          <motion.div
            className="dash-empty"
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, ease }}
          >
            <div className="dash-empty-icon">
              <Shield size={26} strokeWidth={1.5} />
            </div>
            <p style={{ fontSize: '1.2rem', fontWeight: 300, color: 'var(--text-primary)', marginBottom: 8, letterSpacing: '-0.03em' }}>
              No accounts yet
            </p>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', fontWeight: 300, maxWidth: 360, marginBottom: 28 }}>
              Add your first AWS account to start investigating CloudTrail events with natural language.
            </p>
            <button className="dash-add-btn" onClick={() => setShowAddModal(true)}>
              <Plus size={15} strokeWidth={2} />
              Add Account
            </button>
          </motion.div>
        ) : (
          <div className="dash-grid">
            {accounts.map((acc, i) => (
              <motion.div
                key={acc.id}
                className="dash-card"
                custom={i}
                variants={cardVariants}
                initial="initial"
                animate="animate"
              >
                <button
                  className="dash-delete-btn"
                  onClick={() => handleDelete(acc.id)}
                  title="Remove account"
                >
                  <Trash2 size={14} strokeWidth={1.5} />
                </button>

                <div className="dash-card-nick">{acc.nickname}</div>

                <div className="dash-card-meta">
                  <span style={{ color: 'var(--text-dim)' }}>Region</span>
                  <span className="dash-region-badge">{acc.region === 'all' ? 'All Regions' : acc.region}</span>
                </div>

                <div className="dash-card-meta">
                  <span style={{ color: 'var(--text-dim)' }}>Last verified</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>
                    {acc.last_verified ? new Date(acc.last_verified).toLocaleDateString('en-IN') : 'Never'}
                  </span>
                </div>

                <div className="dash-card-footer">
                  {acc.last_verified ? (
                    <span className="verified-tag">
                      <CheckCircle size={13} strokeWidth={2} />
                      Verified
                    </span>
                  ) : (
                    <span className="unverified-tag">
                      <AlertCircle size={13} strokeWidth={1.5} />
                      Unverified
                    </span>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        )}

        {accounts.length > 0 && (
          <motion.div
            style={{ marginTop: 40, display: 'flex', justifyContent: 'flex-end' }}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease, delay: 0.3 }}
          >
            <button className="dash-proceed-btn" onClick={() => navigate('/chat')}>
              <MessageSquare size={16} strokeWidth={1.5} />
              Start Investigating
              <ArrowRight size={16} strokeWidth={1.5} />
            </button>
          </motion.div>
        )}
      </main>

      {showAddModal && <AddAccountModal onClose={() => setShowAddModal(false)} />}
    </div>
  );
};

export default DashboardPage;
