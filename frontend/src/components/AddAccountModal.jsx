import React, { useState } from 'react';
import useAccountStore from '../store/accountStore';
import SetupInstructions from './SetupInstructions';

const REGIONS = [
  'ap-south-1','us-east-1','us-east-2','us-west-1','us-west-2',
  'eu-west-1','eu-west-2','eu-central-1','ap-southeast-1','ap-southeast-2',
  'ap-northeast-1','ca-central-1','sa-east-1',
];

const inputStyle = {
  width: '100%', padding: '10px 14px', borderRadius: '8px',
  border: '1px solid var(--border-subtle)',
  background: 'var(--bg-primary)', color: 'var(--text-primary)',
  fontFamily: 'var(--font-sans)', fontSize: '0.85rem',
  outline: 'none', boxSizing: 'border-box', transition: 'border-color 0.2s',
};

const labelStyle = {
  display: 'block', fontSize: '0.75rem', fontWeight: 600,
  color: 'var(--text-secondary)', marginBottom: '6px',
  letterSpacing: '0.04em', textTransform: 'uppercase',
};

const AddAccountModal = ({ onClose }) => {
  const { addAccount, testConnection } = useAccountStore();
  const [form, setForm] = useState({ nickname: '', region: 'ap-south-1', access_key_id: '', secret_access_key: '' });
  const [showSecret, setShowSecret] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');

  const handleChange = e => { setForm({ ...form, [e.target.name]: e.target.value }); setTestResult(null); };

  const valid = form.nickname.length > 0 && form.nickname.length <= 30
    && form.access_key_id.length === 20
    && (form.access_key_id.startsWith('AKIA') || form.access_key_id.startsWith('ASIA'))
    && form.secret_access_key.length >= 40;

  const handleTest = async () => {
    setTesting(true); setTestResult(null);
    const result = await testConnection(form);
    setTestResult(result); setTesting(false);
  };

  const handleSave = async () => {
    if (!testResult?.success) return;
    setSaving(true); setSaveError('');
    try { await addAccount(form); onClose(); }
    catch (e) { setSaveError(e.response?.data?.detail || e.message || 'Failed to save account'); }
    finally { setSaving(false); }
  };

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 1000,
      background: 'rgba(13,17,23,0.85)', backdropFilter: 'blur(6px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '16px',
    }} onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
      <div style={{
        background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)',
        borderRadius: '16px', overflow: 'hidden', boxShadow: '0 24px 80px rgba(0,0,0,0.6)',
        width: '100%', maxWidth: '920px', display: 'flex', flexDirection: 'row',
        maxHeight: '90vh', overflowY: 'auto',
      }}>

        {/* Left: Instructions */}
        <div style={{
          flex: 1, padding: '32px', borderRight: '1px solid var(--border)',
          background: 'rgba(13,17,23,0.4)',
          minWidth: 0,
        }}>
          <div style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--accent)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: '8px' }}>
            Step-by-Step
          </div>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 24px 0' }}>
            IAM Setup Instructions
          </h2>
          <SetupInstructions />
        </div>

        {/* Right: Credentials Form */}
        <div style={{ flex: 1, padding: '32px', display: 'flex', flexDirection: 'column', minWidth: '300px' }}>
          <div style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--info)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: '8px' }}>
            Credentials
          </div>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 24px 0' }}>
            Add AWS Account
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', flex: 1 }}>

            <div>
              <label style={labelStyle}>Account Nickname</label>
              <input name="nickname" value={form.nickname} onChange={handleChange}
                placeholder="e.g. prod-us-east" style={inputStyle}
                onFocus={e => e.target.style.borderColor = 'var(--accent)'}
                onBlur={e => e.target.style.borderColor = 'var(--border-subtle)'}
              />
            </div>

            <div>
              <label style={labelStyle}>AWS Region</label>
              <select name="region" value={form.region} onChange={handleChange}
                style={{ ...inputStyle, cursor: 'pointer' }}>
                {REGIONS.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>

            <div>
              <label style={labelStyle}>Access Key ID</label>
              <input name="access_key_id" value={form.access_key_id} onChange={handleChange}
                placeholder="AKIA..." autoComplete="off"
                style={{
                  ...inputStyle, fontFamily: 'var(--font-mono)', fontSize: '0.82rem',
                  borderColor: form.access_key_id
                    ? (form.access_key_id.length === 20 && (form.access_key_id.startsWith('AKIA') || form.access_key_id.startsWith('ASIA')))
                      ? 'var(--accent)' : 'var(--error)'
                    : 'var(--border-subtle)',
                }}
              />
              {form.access_key_id && form.access_key_id.length !== 20 && (
                <div style={{ fontSize: '0.72rem', color: 'var(--error)', marginTop: '4px' }}>Must be 20 characters (starts with AKIA or ASIA)</div>
              )}
            </div>

            <div>
              <label style={labelStyle}>Secret Access Key</label>
              <div style={{ position: 'relative' }}>
                <input name="secret_access_key" value={form.secret_access_key} onChange={handleChange}
                  type={showSecret ? 'text' : 'password'} placeholder="••••••••" autoComplete="off"
                  style={{
                    ...inputStyle, fontFamily: 'var(--font-mono)', fontSize: '0.82rem',
                    paddingRight: '44px',
                    borderColor: form.secret_access_key
                      ? form.secret_access_key.length >= 40 ? 'var(--accent)' : 'var(--error)'
                      : 'var(--border-subtle)',
                  }}
                />
                <button type="button" onClick={() => setShowSecret(v => !v)} style={{
                  position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)',
                  background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)',
                  fontSize: '0.72rem', fontFamily: 'var(--font-sans)', fontWeight: 600, padding: '2px 6px',
                }}>
                  {showSecret ? 'Hide' : 'Show'}
                </button>
              </div>
            </div>

            {testResult && (
              <div style={{
                padding: '10px 14px', borderRadius: '8px', fontSize: '0.82rem',
                background: testResult.success ? 'rgba(0,255,136,0.08)' : 'rgba(255,68,68,0.08)',
                border: `1px solid ${testResult.success ? 'rgba(0,255,136,0.3)' : 'rgba(255,68,68,0.3)'}`,
                color: testResult.success ? 'var(--accent)' : 'var(--error)',
              }}>
                {testResult.success ? '✓ ' : '✗ '}{testResult.message}
              </div>
            )}

            {saveError && (
              <div style={{
                padding: '10px 14px', borderRadius: '8px', fontSize: '0.82rem',
                background: 'rgba(255,68,68,0.08)', border: '1px solid rgba(255,68,68,0.3)',
                color: 'var(--error)',
              }}>
                ⚠ {saveError}
              </div>
            )}
          </div>

          {/* Buttons */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '24px' }}>
            <button onClick={handleTest} disabled={!valid || testing} style={{
              padding: '11px', borderRadius: '8px', fontFamily: 'var(--font-sans)', fontSize: '0.88rem', fontWeight: 600, cursor: valid && !testing ? 'pointer' : 'not-allowed',
              background: valid && !testing ? 'rgba(88,166,255,0.12)' : 'var(--bg-tertiary)',
              border: `1px solid ${valid && !testing ? 'rgba(88,166,255,0.3)' : 'var(--border)'}`,
              color: valid && !testing ? '#58a6ff' : 'var(--text-tertiary)', transition: 'all 0.2s',
            }}>
              {testing ? '⟳  Verifying Connection...' : '⎘  Test Connection'}
            </button>

            <button onClick={handleSave} disabled={!testResult?.success || saving} style={{
              padding: '11px', borderRadius: '8px', fontFamily: 'var(--font-sans)', fontSize: '0.88rem', fontWeight: 600, cursor: testResult?.success && !saving ? 'pointer' : 'not-allowed',
              background: testResult?.success && !saving ? 'rgba(0,255,136,0.12)' : 'var(--bg-tertiary)',
              border: `1px solid ${testResult?.success && !saving ? 'rgba(0,255,136,0.3)' : 'var(--border)'}`,
              color: testResult?.success && !saving ? 'var(--accent)' : 'var(--text-tertiary)', transition: 'all 0.2s',
            }}>
              {saving ? '⟳  Saving...' : '✦  Save Account'}
            </button>

            <button onClick={onClose} style={{
              padding: '9px', borderRadius: '8px', fontFamily: 'var(--font-sans)', fontSize: '0.85rem',
              background: 'none', border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer',
              transition: 'color 0.2s',
            }}
              onMouseEnter={e => e.target.style.color = 'var(--text-primary)'}
              onMouseLeave={e => e.target.style.color = 'var(--text-tertiary)'}
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AddAccountModal;
