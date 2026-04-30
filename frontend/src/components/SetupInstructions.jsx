import React, { useState } from 'react';
import { IAM_POLICIES, IAM_SETUP_STEPS } from '../constants/iamPolicy';

const SHORT_LABELS = ['Core Access', 'Monitoring', 'Data Services'];

const SetupInstructions = () => {
  const [activePolicy, setActivePolicy] = useState(0);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(IAM_POLICIES[activePolicy].policy, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>

      {/* Setup Steps */}
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

      {/* Policy Selector */}
      <div style={{ marginTop: '4px' }}>

        {/* Pill Selectors — centered, equal width */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '6px', marginBottom: '8px' }}>
          {IAM_POLICIES.map((p, idx) => (
            <button
              key={p.id}
              onClick={() => { setActivePolicy(idx); setCopied(false); }}
              style={{
                padding: '7px 4px',
                fontSize: '0.72rem',
                fontFamily: 'var(--font-sans)',
                fontWeight: 600,
                borderRadius: '6px',
                cursor: 'pointer',
                border: `1px solid ${activePolicy === idx ? 'rgba(0,255,136,0.5)' : 'var(--border-subtle)'}`,
                background: activePolicy === idx ? 'rgba(0,255,136,0.1)' : 'rgba(255,255,255,0.03)',
                color: activePolicy === idx ? 'var(--accent)' : 'var(--text-secondary)',
                transition: 'all 0.15s',
                textAlign: 'center',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {SHORT_LABELS[idx]}
            </button>
          ))}
        </div>

        {/* Policy Panel */}
        <div style={{
          background: '#0a0d12',
          border: '1px solid var(--border-subtle)',
          borderRadius: '8px',
          overflow: 'hidden',
        }}>
          {/* Services covered */}
          <div style={{
            padding: '6px 12px',
            borderBottom: '1px solid rgba(255,255,255,0.05)',
            background: 'rgba(255,255,255,0.02)',
            fontSize: '0.7rem',
            color: 'var(--text-secondary)',
            fontFamily: 'var(--font-mono)',
          }}>
            {IAM_POLICIES[activePolicy].description}
          </div>

          {/* JSON Preview */}
          <pre style={{
            padding: '12px',
            margin: 0,
            overflowX: 'auto',
            overflowY: 'auto',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.68rem',
            color: 'var(--accent)',
            lineHeight: 1.55,
            maxHeight: '200px',
          }}>
            {JSON.stringify(IAM_POLICIES[activePolicy].policy, null, 2)}
          </pre>
        </div>

        {/* Centered copy button */}
        <button
          onClick={handleCopy}
          style={{
            marginTop: '8px',
            width: '100%',
            padding: '9px',
            fontSize: '0.78rem',
            fontFamily: 'var(--font-sans)',
            fontWeight: 700,
            background: copied ? 'rgba(0,255,136,0.15)' : 'rgba(0,255,136,0.07)',
            border: `1px solid ${copied ? 'rgba(0,255,136,0.5)' : 'rgba(0,255,136,0.2)'}`,
            color: copied ? 'var(--accent)' : 'var(--text-secondary)',
            borderRadius: '6px',
            cursor: 'pointer',
            transition: 'all 0.2s',
            letterSpacing: '0.02em',
          }}
        >
          {copied ? `✓ Copied!` : `⎘  Copy ${SHORT_LABELS[activePolicy]}`}
        </button>

        <p style={{ marginTop: '6px', fontSize: '0.7rem', color: 'var(--text-secondary)', opacity: 0.6, textAlign: 'center' }}>
          Attach all 3 policies to the same IAM user
        </p>
      </div>
    </div>
  );
};

export default SetupInstructions;
