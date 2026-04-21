import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '../store/authStore';

const ShieldIcon = () => (
  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    <path d="M9 12l2 2 4-4" />
  </svg>
);

const EyeIcon = ({ open }) => open ? (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
  </svg>
) : (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
    <line x1="1" y1="1" x2="23" y2="23"/>
  </svg>
);

const LoginPage = () => {
  const navigate = useNavigate();
  const { login, register } = useAuthStore();

  const [isLoginTab, setIsLoginTab] = useState(true);
  const [formData, setFormData] = useState({ email: '', password: '', confirmPassword: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.email || !formData.password) { setError('Please fill in all fields.'); return; }
    if (!isLoginTab) {
      if (formData.password.length < 8) { setError('Password must be at least 8 characters.'); return; }
      if (formData.password !== formData.confirmPassword) { setError('Passwords do not match.'); return; }
    }

    setLoading(true);
    setError('');
    try {
      if (isLoginTab) { await login(formData.email, formData.password); }
      else { await register(formData.email, formData.password); }
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Authentication failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--bg-primary)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
      fontFamily: 'var(--font-sans)',
      overflow: 'auto',
      position: 'relative',
    }}>
      {/* Background glow orbs */}
      <div style={{
        position: 'fixed', top: '-20%', left: '-10%',
        width: '600px', height: '600px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(0,255,136,0.04) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />
      <div style={{
        position: 'fixed', bottom: '-20%', right: '-10%',
        width: '500px', height: '500px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(88,166,255,0.04) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />

      <div style={{ width: '100%', maxWidth: '420px', position: 'relative', zIndex: 1 }}>

        {/* Logo & Title */}
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            width: '72px', height: '72px', borderRadius: '20px',
            background: 'linear-gradient(135deg, rgba(0,255,136,0.15), rgba(0,255,136,0.05))',
            border: '1px solid rgba(0,255,136,0.25)',
            color: 'var(--accent)',
            marginBottom: '20px',
            boxShadow: '0 0 40px rgba(0,255,136,0.1)',
          }}>
            <ShieldIcon />
          </div>
          <h1 style={{
            fontSize: '1.6rem', fontWeight: 800,
            color: 'var(--text-primary)', letterSpacing: '-0.03em',
            margin: 0, marginBottom: '6px',
          }}>
            CloudTrail AI
          </h1>
          <p style={{ color: 'var(--text-tertiary)', fontSize: '0.82rem', margin: 0, letterSpacing: '0.06em', textTransform: 'uppercase' }}>
            Security Investigation Platform
          </p>
        </div>

        {/* Card */}
        <div style={{
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '16px',
          overflow: 'hidden',
          boxShadow: '0 8px 40px rgba(0,0,0,0.5)',
        }}>

          {/* Tabs */}
          <div style={{ display: 'flex', borderBottom: '1px solid var(--border)' }}>
            {[{ label: 'Sign In', active: isLoginTab }, { label: 'Register', active: !isLoginTab }].map(({ label, active }, i) => (
              <button
                key={label}
                onClick={() => { setIsLoginTab(i === 0); setError(''); }}
                style={{
                  flex: 1, padding: '16px', border: 'none', cursor: 'pointer',
                  background: active ? 'rgba(0,255,136,0.05)' : 'transparent',
                  color: active ? 'var(--accent)' : 'var(--text-secondary)',
                  fontFamily: 'var(--font-sans)', fontSize: '0.88rem', fontWeight: 600,
                  borderBottom: active ? '2px solid var(--accent)' : '2px solid transparent',
                  transition: 'all 0.2s ease',
                  letterSpacing: '0.02em',
                }}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} style={{ padding: '28px' }}>

            {/* Email */}
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '8px', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
                Email Address
              </label>
              <input
                type="email" name="email" required
                value={formData.email} onChange={handleInputChange}
                placeholder="you@example.com"
                style={{
                  width: '100%', padding: '11px 14px', borderRadius: '8px',
                  border: '1px solid var(--border-subtle)',
                  background: 'var(--bg-primary)',
                  color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', fontSize: '0.88rem',
                  outline: 'none', boxSizing: 'border-box',
                  transition: 'border-color 0.2s',
                }}
                onFocus={(e) => e.target.style.borderColor = 'var(--accent)'}
                onBlur={(e) => e.target.style.borderColor = 'var(--border-subtle)'}
              />
            </div>

            {/* Password */}
            <div style={{ marginBottom: isLoginTab ? '24px' : '16px' }}>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '8px', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
                Password {!isLoginTab && <span style={{ color: 'var(--text-tertiary)', fontWeight: 400, fontSize: '0.72rem', textTransform: 'none' }}>(min. 8 characters)</span>}
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  type={showPassword ? 'text' : 'password'} name="password" required
                  value={formData.password} onChange={handleInputChange}
                  placeholder="••••••••"
                  style={{
                    width: '100%', padding: '11px 40px 11px 14px', borderRadius: '8px',
                    border: '1px solid var(--border-subtle)',
                    background: 'var(--bg-primary)',
                    color: 'var(--text-primary)', fontFamily: 'var(--font-mono)', fontSize: '0.88rem',
                    outline: 'none', boxSizing: 'border-box', transition: 'border-color 0.2s',
                  }}
                  onFocus={(e) => e.target.style.borderColor = 'var(--accent)'}
                  onBlur={(e) => e.target.style.borderColor = 'var(--border-subtle)'}
                />
                <button type="button" onClick={() => setShowPassword(v => !v)} style={{
                  position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)',
                  background: 'none', border: 'none', cursor: 'pointer',
                  color: 'var(--text-tertiary)', padding: '2px', display: 'flex',
                }}>
                  <EyeIcon open={showPassword} />
                </button>
              </div>
            </div>

            {/* Confirm Password (register only) */}
            {!isLoginTab && (
              <div style={{ marginBottom: '24px' }}>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '8px', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
                  Confirm Password
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    type={showConfirm ? 'text' : 'password'} name="confirmPassword" required
                    value={formData.confirmPassword} onChange={handleInputChange}
                    placeholder="••••••••"
                    style={{
                      width: '100%', padding: '11px 40px 11px 14px', borderRadius: '8px',
                      border: `1px solid ${formData.confirmPassword && formData.password !== formData.confirmPassword ? 'var(--error)' : 'var(--border-subtle)'}`,
                      background: 'var(--bg-primary)',
                      color: 'var(--text-primary)', fontFamily: 'var(--font-mono)', fontSize: '0.88rem',
                      outline: 'none', boxSizing: 'border-box', transition: 'border-color 0.2s',
                    }}
                    onFocus={(e) => e.target.style.borderColor = 'var(--accent)'}
                    onBlur={(e) => e.target.style.borderColor = formData.confirmPassword && formData.password !== formData.confirmPassword ? 'var(--error)' : 'var(--border-subtle)'}
                  />
                  <button type="button" onClick={() => setShowConfirm(v => !v)} style={{
                    position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)',
                    background: 'none', border: 'none', cursor: 'pointer',
                    color: 'var(--text-tertiary)', padding: '2px', display: 'flex',
                  }}>
                    <EyeIcon open={showConfirm} />
                  </button>
                </div>
              </div>
            )}

            {/* Error */}
            {error && (
              <div style={{
                marginBottom: '16px', padding: '12px 14px', borderRadius: '8px',
                background: 'var(--error-dim)', border: '1px solid rgba(255,68,68,0.3)',
                color: 'var(--error)', fontSize: '0.83rem', display: 'flex', alignItems: 'center', gap: '8px',
              }}>
                <span>⚠</span> {error}
              </div>
            )}

            {/* Submit */}
            <button
              type="submit" disabled={loading}
              style={{
                width: '100%', padding: '13px', borderRadius: '8px',
                border: '1px solid rgba(0,255,136,0.3)',
                background: loading ? 'rgba(0,255,136,0.05)' : 'rgba(0,255,136,0.12)',
                color: loading ? 'var(--text-tertiary)' : 'var(--accent)',
                fontFamily: 'var(--font-sans)', fontSize: '0.9rem', fontWeight: 700,
                cursor: loading ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s ease', letterSpacing: '0.04em',
                boxShadow: loading ? 'none' : '0 0 20px rgba(0,255,136,0.08)',
              }}
              onMouseEnter={(e) => { if (!loading) { e.target.style.background = 'rgba(0,255,136,0.2)'; e.target.style.boxShadow = '0 0 30px rgba(0,255,136,0.2)'; }}}
              onMouseLeave={(e) => { if (!loading) { e.target.style.background = 'rgba(0,255,136,0.12)'; e.target.style.boxShadow = '0 0 20px rgba(0,255,136,0.08)'; }}}
            >
              {loading ? '⟳  Processing...' : (isLoginTab ? '⎘  Sign In' : '✦  Create Account')}
            </button>
          </form>
        </div>

        {/* Footer */}
        <p style={{ textAlign: 'center', marginTop: '20px', color: 'var(--text-tertiary)', fontSize: '0.72rem', letterSpacing: '0.03em' }}>
          AWS CloudTrail Log Investigation · Powered by AI
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
