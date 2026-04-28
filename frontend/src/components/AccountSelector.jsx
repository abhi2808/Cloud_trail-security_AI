import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import useAccountStore from '../store/accountStore';
import useChatStore from '../store/chatStore';

const AccountSelector = () => {
  const { accounts, selectedAccount, fetchAccounts, selectAccount, isLoading } = useAccountStore();
  const { selectedRegion, setRegion } = useChatStore();

  useEffect(() => { fetchAccounts(); }, [fetchAccounts]);

  useEffect(() => {
    if (accounts.length > 0 && !selectedAccount && !isLoading) {
      selectAccount(accounts[0]);
    }
  }, [accounts, selectedAccount, selectAccount, isLoading]);

  const barStyle = {
    background: 'var(--bg-secondary)',
    borderBottom: '1px solid var(--border)',
    padding: '10px 20px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexShrink: 0,
    fontSize: '0.82rem',
  };

  if (isLoading && accounts.length === 0) {
    return <div style={{ ...barStyle, color: 'var(--text-tertiary)' }}>Loading accounts...</div>;
  }

  if (accounts.length === 0) {
    return (
      <div style={{ ...barStyle, background: 'rgba(255,170,0,0.05)', borderBottom: '1px solid rgba(255,170,0,0.3)' }}>
        <span style={{ color: 'var(--warning)' }}>
          ⚠ No AWS accounts configured.
        </span>
        <Link to="/dashboard" style={{ color: 'var(--warning)', fontWeight: 600, textDecoration: 'none' }}>
          Add Account →
        </Link>
      </div>
    );
  }

  return (
    <div style={barStyle}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span style={{ color: 'var(--text-tertiary)' }}>Investigating:</span>
        <select
          value={selectedAccount?.id || ''}
          onChange={e => {
            const acc = accounts.find(a => a.id === e.target.value);
            if (acc) selectAccount(acc);
          }}
          style={{
            background: 'var(--bg-primary)',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-primary)',
            padding: '4px 10px', borderRadius: '6px',
            fontFamily: 'var(--font-sans)', fontSize: '0.82rem',
            cursor: 'pointer', outline: 'none',
          }}
        >
          <option value="" disabled>Select an account...</option>
          {accounts.map(acc => (
            <option key={acc.id} value={acc.id}>
              {acc.nickname} — {acc.region === 'all' ? 'All Regions' : acc.region}
            </option>
          ))}
        </select>
      </div>

      {selectedAccount && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent)', fontFamily: 'var(--font-mono)', fontSize: '0.76rem' }}>
            <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: 'var(--accent)', display: 'inline-block', animation: 'pulse-dot 2s infinite' }} />
            Connected
          </div>
          <select
            value={selectedRegion}
            onChange={e => setRegion(e.target.value)}
            style={{
              background: 'var(--bg-primary)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-primary)',
              padding: '4px 10px', borderRadius: '6px',
              fontFamily: 'var(--font-sans)', fontSize: '0.82rem',
              cursor: 'pointer', outline: 'none',
            }}
          >
            <option value="all">All Regions</option>
            <option value="ap-south-1">ap-south-1</option>
            <option value="us-east-1">us-east-1</option>
            <option value="us-east-2">us-east-2</option>
            <option value="us-west-1">us-west-1</option>
            <option value="us-west-2">us-west-2</option>
            <option value="eu-west-1">eu-west-1</option>
            <option value="eu-west-2">eu-west-2</option>
            <option value="eu-central-1">eu-central-1</option>
            <option value="ap-southeast-1">ap-southeast-1</option>
            <option value="ap-southeast-2">ap-southeast-2</option>
            <option value="ap-northeast-1">ap-northeast-1</option>
            <option value="ca-central-1">ca-central-1</option>
            <option value="sa-east-1">sa-east-1</option>
          </select>
          <Link to="/dashboard" style={{ color: 'var(--info)', textDecoration: 'none', fontSize: '0.8rem' }}>
            Switch
          </Link>
        </div>
      )}
    </div>
  );
};

export default AccountSelector;
