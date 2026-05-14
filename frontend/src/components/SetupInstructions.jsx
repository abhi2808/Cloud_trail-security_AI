import React, { useState } from 'react';
import { IAM_POLICIES, IAM_SETUP_STEPS } from '../constants/iamPolicy';
import { Copy, Check } from 'lucide-react';

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
    <div className="setup-steps">
      {IAM_SETUP_STEPS.map(step => (
        <div key={step.step} className="setup-step-row">
          <div className="setup-step-num">{step.step}</div>
          <div>
            <div style={{ fontWeight: 500, color: 'var(--text-primary)', marginBottom: 2, fontSize: '0.82rem' }}>
              {step.title}
            </div>
            <div style={{ fontSize: '0.77rem', color: 'var(--text-muted)', lineHeight: 1.55 }}>
              {step.description}
            </div>
          </div>
        </div>
      ))}

      <div style={{ marginTop: 4 }}>
        <div className="setup-policy-tabs">
          {IAM_POLICIES.map((p, idx) => (
            <button
              key={p.id}
              onClick={() => { setActivePolicy(idx); setCopied(false); }}
              className={`setup-policy-tab${activePolicy === idx ? ' active' : ''}`}
            >
              {SHORT_LABELS[idx]}
            </button>
          ))}
        </div>

        <div className="setup-policy-panel">
          <div className="setup-policy-desc">{IAM_POLICIES[activePolicy].description}</div>
          <pre className="setup-policy-pre">
            {JSON.stringify(IAM_POLICIES[activePolicy].policy, null, 2)}
          </pre>
        </div>

        <button onClick={handleCopy} className={`setup-copy-btn${copied ? ' copied' : ''}`}>
          <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
            {copied ? <Check size={13} strokeWidth={2} /> : <Copy size={13} strokeWidth={1.5} />}
            {copied ? 'Copied!' : `Copy ${SHORT_LABELS[activePolicy]}`}
          </span>
        </button>

        <p style={{ marginTop: 6, fontSize: '0.68rem', color: 'var(--text-dim)', textAlign: 'center' }}>
          Attach all 3 policies to the same IAM user
        </p>
      </div>
    </div>
  );
};

export default SetupInstructions;
