import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, Eye, EyeOff, AlertCircle } from 'lucide-react';
import useAuthStore from '../store/authStore';
import GalaxyBackground from '../components/GalaxyBackground';
import StarTrailLoader from '../components/StarTrailLoader';

const itemVariants = {
  initial: { opacity: 0, y: 16, filter: 'blur(4px)' },
  animate: { opacity: 1, y: 0, filter: 'blur(0px)' },
};
const ease = [0.16, 1, 0.3, 1];

const LoginPage = () => {
  const navigate = useNavigate();
  const { login, register, activateAuth } = useAuthStore();

  const [isLoginTab, setIsLoginTab] = useState(true);
  const [formData, setFormData] = useState({ email: '', password: '', confirmPassword: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showLoader, setShowLoader] = useState(false);
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
      setShowLoader(true);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Authentication failed.');
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <GalaxyBackground variant="login" />

      {/* Star trail renders behind the card (z-index 1), card stays on top */}
      <AnimatePresence>
        {showLoader && (
          <StarTrailLoader onComplete={() => { activateAuth(); navigate('/dashboard'); }} />
        )}
      </AnimatePresence>

      <motion.div
        className="login-content"
        style={{ position: 'relative', zIndex: 2 }}
        initial="initial"
        animate="animate"
        variants={{ animate: { transition: { staggerChildren: 0.08 } } }}
      >
        {/* Logo */}
        <motion.div className="login-logo-area" variants={itemVariants} transition={{ duration: 0.6, ease }}>
          <div className="login-logo-icon">
            <Shield size={26} strokeWidth={1.5} />
          </div>
          <h1 className="login-title">
            CloudComply <span className="ai">AI</span>
          </h1>
          <p className="login-subtitle">Security Investigation Platform</p>
        </motion.div>

        {/* Card */}
        <motion.div className="login-card" variants={itemVariants} transition={{ duration: 0.6, ease }}>
          {/* Tabs */}
          <div className="login-tabs">
            {[{ label: 'Sign In', idx: 0 }, { label: 'Register', idx: 1 }].map(({ label, idx }) => (
              <button
                key={label}
                className={`login-tab${isLoginTab === (idx === 0) ? ' active' : ''}`}
                onClick={() => { setIsLoginTab(idx === 0); setError(''); }}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Form */}
          <form className="login-form" onSubmit={handleSubmit}>
            <div>
              <label className="field-label">Email Address</label>
              <input
                type="email" name="email" required
                value={formData.email} onChange={handleInputChange}
                placeholder="you@company.com"
                className="field-input"
              />
            </div>

            <div>
              <label className="field-label">
                Password{!isLoginTab && <span style={{ color: 'var(--text-dim)', fontWeight: 400, textTransform: 'none', marginLeft: 6 }}>min. 8 chars</span>}
              </label>
              <div className="field-input-wrap">
                <input
                  type={showPassword ? 'text' : 'password'}
                  name="password" required
                  value={formData.password} onChange={handleInputChange}
                  placeholder="••••••••"
                  className="field-input field-mono"
                  style={{ paddingRight: 40 }}
                />
                <button type="button" className="field-eye-btn" onClick={() => setShowPassword(v => !v)}>
                  {showPassword ? <EyeOff size={15} strokeWidth={1.5} /> : <Eye size={15} strokeWidth={1.5} />}
                </button>
              </div>
            </div>

            {!isLoginTab && (
              <div>
                <label className="field-label">Confirm Password</label>
                <div className="field-input-wrap">
                  <input
                    type={showConfirm ? 'text' : 'password'}
                    name="confirmPassword" required
                    value={formData.confirmPassword} onChange={handleInputChange}
                    placeholder="••••••••"
                    className="field-input field-mono"
                    style={{
                      paddingRight: 40,
                      borderColor: formData.confirmPassword && formData.password !== formData.confirmPassword
                        ? 'rgba(248,113,113,0.5)' : undefined,
                    }}
                  />
                  <button type="button" className="field-eye-btn" onClick={() => setShowConfirm(v => !v)}>
                    {showConfirm ? <EyeOff size={15} strokeWidth={1.5} /> : <Eye size={15} strokeWidth={1.5} />}
                  </button>
                </div>
              </div>
            )}

            {error && (
              <div className="login-error">
                <AlertCircle size={14} strokeWidth={1.5} style={{ flexShrink: 0 }} />
                {error}
              </div>
            )}

            <button type="submit" className="login-submit" disabled={loading}>
              {loading ? 'Authenticating...' : isLoginTab ? 'Sign In' : 'Create Account'}
            </button>
          </form>
        </motion.div>

      </motion.div>
    </div>
  );
};

export default LoginPage;
