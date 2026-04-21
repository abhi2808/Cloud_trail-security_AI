import React, { useState } from 'react';
import { IAM_POLICY_JSON, IAM_SETUP_STEPS } from '../constants/iamPolicy';

const SetupInstructions = () => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(IAM_POLICY_JSON, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
      {IAM_SETUP_STEPS.map(step => (
        <div key={step.step} style={{ display: 'flex', gap: '14px', alignItems: 'flex-start' }}>
          <div style={{
            flexShrink: 0, width: '24px', height: '24px', borderRadius: '50%',
            background: 'rgba(0,255,136,0.1)', border: '1px solid rgba(0,255,136,0.3)',
            color: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '0.72rem', fontWeight: 700,
          }}>
            {step.step}
          </div>
          <div>
            <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '2px' }}>{step.title}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{step.description}</div>
          </div>
        </div>
      ))}

      <div style={{ marginTop: '8px', position: 'relative', background: '#0a0d12', border: '1px solid var(--border-subtle)', borderRadius: '8px', overflow: 'hidden' }}>
        <button
          onClick={handleCopy}
          style={{
            position: 'absolute', top: '10px', right: '10px',
            padding: '4px 12px', fontSize: '0.72rem', fontFamily: 'var(--font-sans)',
            background: copied ? 'rgba(0,255,136,0.15)' : 'var(--bg-surface)',
            border: `1px solid ${copied ? 'rgba(0,255,136,0.4)' : 'var(--border-subtle)'}`,
            color: copied ? 'var(--accent)' : 'var(--text-secondary)',
            borderRadius: '4px', cursor: 'pointer', fontWeight: 600, transition: 'all 0.2s',
          }}
        >
          {copied ? '✓ Copied' : 'Copy'}
        </button>
        <pre style={{
          padding: '16px', paddingTop: '40px', margin: 0, overflowX: 'auto',
          fontFamily: 'var(--font-mono)', fontSize: '0.72rem',
          color: 'var(--accent)', lineHeight: 1.6,
        }}>
          {JSON.stringify(IAM_POLICY_JSON, null, 2)}
        </pre>
      </div>
    </div>
  );
};

export default SetupInstructions;
