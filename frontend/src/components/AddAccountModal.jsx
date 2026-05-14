import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Eye, EyeOff } from 'lucide-react';
import useAccountStore from '../store/accountStore';
import SetupInstructions from './SetupInstructions';

const REGIONS = [
  { value: 'all', label: 'All Regions (Recommended)' },
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

const ease = [0.16, 1, 0.3, 1];

const inputStyle = {
  width: '100%', padding: '10px 14px', borderRadius: 'var(--r-sm)',
  border: '1px solid rgba(255,255,255,0.1)',
  background: 'rgba(255,255,255,0.04)', color: 'var(--text-primary)',
  fontFamily: 'var(--font-sans)', fontSize: '0.85rem',
  outline: 'none', boxSizing: 'border-box', transition: 'border-color 0.2s, box-shadow 0.2s',
};

const labelStyle = {
  display: 'block', fontSize: '0.72rem', fontWeight: 600,
  color: 'var(--text-muted)', marginBottom: '7px',
  letterSpacing: '0.05em', textTransform: 'uppercase',
};

const AddAccountModal = ({ onClose }) => {
  const { addAccount, testConnection } = useAccountStore();
  const [form, setForm] = useState({ nickname: '', region: 'all', access_key_id: '', secret_access_key: '' });
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
    <motion.div
      className="modal-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}
    >
      <motion.div
        className="modal-card"
        initial={{ opacity: 0, scale: 0.96, filter: 'blur(8px)' }}
        animate={{ opacity: 1, scale: 1, filter: 'blur(0px)' }}
        exit={{ opacity: 0, scale: 0.96, filter: 'blur(8px)' }}
        transition={{ duration: 0.4, ease }}
      >
        {/* Left: Instructions */}
        <div className="modal-left">
          <div className="modal-section-label">Step-by-Step</div>
          <h2 className="modal-section-title">IAM Setup</h2>
          <SetupInstructions />
        </div>

        {/* Right: Form */}
        <div className="modal-right">
          <div className="modal-section-label">Credentials</div>
          <h2 className="modal-section-title">Add AWS Account</h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, flex: 1 }}>
            <div>
              <label style={labelStyle}>Account Nickname</label>
              <input name="nickname" value={form.nickname} onChange={handleChange}
                placeholder="prod-us-east"
                style={inputStyle}
                onFocus={e => { e.target.style.borderColor = 'rgba(255,255,255,0.28)'; e.target.style.boxShadow = '0 0 0 3px rgba(255,255,255,0.04)'; }}
                onBlur={e => { e.target.style.borderColor = 'rgba(255,255,255,0.1)'; e.target.style.boxShadow = 'none'; }}
              />
            </div>

            <div>
              <label style={labelStyle}>AWS Region</label>
              <select name="region" value={form.region} onChange={handleChange}
                style={{ ...inputStyle, cursor: 'pointer' }}>
                {REGIONS.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
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
                      ? 'rgba(74,222,128,0.4)' : 'rgba(248,113,113,0.4)'
                    : 'rgba(255,255,255,0.1)',
                }}
              />
              {form.access_key_id && form.access_key_id.length !== 20 && (
                <div style={{ fontSize: '0.7rem', color: 'var(--sev-critical)', marginTop: 4 }}>
                  Must be 20 characters (AKIA... or ASIA...)
                </div>
              )}
            </div>

            <div>
              <label style={labelStyle}>Secret Access Key</label>
              <div style={{ position: 'relative' }}>
                <input name="secret_access_key" value={form.secret_access_key} onChange={handleChange}
                  type={showSecret ? 'text' : 'password'} placeholder="••••••••" autoComplete="off"
                  style={{
                    ...inputStyle, fontFamily: 'var(--font-mono)', fontSize: '0.82rem',
                    paddingRight: 44,
                    borderColor: form.secret_access_key
                      ? form.secret_access_key.length >= 40 ? 'rgba(74,222,128,0.4)' : 'rgba(248,113,113,0.4)'
                      : 'rgba(255,255,255,0.1)',
                  }}
                />
                <button type="button" onClick={() => setShowSecret(v => !v)} style={{
                  position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                  background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-dim)',
                  display: 'flex', alignItems: 'center', transition: 'color 0.15s',
                }}
                  onMouseEnter={e => e.currentTarget.style.color = 'var(--text-muted)'}
                  onMouseLeave={e => e.currentTarget.style.color = 'var(--text-dim)'}
                >
                  {showSecret ? <EyeOff size={14} strokeWidth={1.5} /> : <Eye size={14} strokeWidth={1.5} />}
                </button>
              </div>
            </div>

            {testResult && (
              <div className={testResult.success ? 'test-result-success' : 'test-result-fail'}>
                {testResult.success ? '✓ ' : '✗ '}{testResult.message}
              </div>
            )}

            {saveError && (
              <div className="test-result-fail">{saveError}</div>
            )}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 20 }}>
            <button
              onClick={handleTest}
              disabled={!valid || testing}
              className={`modal-test-btn${valid && !testing ? ' enabled' : ''}`}
            >
              {testing ? 'Verifying...' : 'Test Connection'}
            </button>

            <button
              onClick={handleSave}
              disabled={!testResult?.success || saving}
              className={`modal-save-btn${testResult?.success && !saving ? ' enabled' : ''}`}
            >
              {saving ? 'Saving...' : 'Save Account'}
            </button>

            <button onClick={onClose} className="modal-cancel-btn">Cancel</button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default AddAccountModal;
