import React, { useState } from 'react';

const TOOL_LABELS = {
  search_cloudtrail:        'CloudTrail Search',
  get_iam_user_permissions: 'IAM Permission Check',
  get_iam_role_permissions: 'IAM Role Analysis',
  list_iam_users:           'IAM User Enumeration',
  simulate_iam_permissions: 'Permission Simulation',
  check_access_keys:        'Access Key Audit',
  describe_ec2_instance:    'EC2 Instance Lookup',
  describe_security_group:  'Security Group Analysis',
  list_ec2_instances:       'EC2 Instance Scan',
  get_cloudwatch_alarms:    'CloudWatch Alarms',
  get_metric_anomalies:     'Metric Anomaly Detection',
  list_s3_buckets:          'S3 Bucket Scan',
  get_s3_bucket_policy:     'S3 Policy Check',
  get_caller_identity:      'Account Identity Check',
};

const TOOL_ICONS = {
  search_cloudtrail:        '📋',
  get_iam_user_permissions: '🔑',
  get_iam_role_permissions: '🎭',
  list_iam_users:           '👥',
  simulate_iam_permissions: '🧪',
  check_access_keys:        '🗝️',
  describe_ec2_instance:    '💻',
  describe_security_group:  '🛡️',
  list_ec2_instances:       '🖥️',
  get_cloudwatch_alarms:    '🔔',
  get_metric_anomalies:     '📈',
  list_s3_buckets:          '🪣',
  get_s3_bucket_policy:     '📜',
  get_caller_identity:      '🔍',
};

const SEVERITY_CONFIG = {
  CRITICAL: { color: '#ff4444', bg: 'rgba(255,68,68,0.12)', border: 'rgba(255,68,68,0.3)',  icon: '🔴' },
  HIGH:     { color: '#ff8c00', bg: 'rgba(255,140,0,0.12)', border: 'rgba(255,140,0,0.3)',  icon: '🟠' },
  MEDIUM:   { color: '#ffd700', bg: 'rgba(255,215,0,0.10)', border: 'rgba(255,215,0,0.3)',  icon: '🟡' },
  LOW:      { color: '#58a6ff', bg: 'rgba(88,166,255,0.10)', border: 'rgba(88,166,255,0.3)', icon: '🔵' },
  NONE:     { color: '#00ff88', bg: 'rgba(0,255,136,0.08)', border: 'rgba(0,255,136,0.25)', icon: '🟢' },
};

export default function InvestigationTimeline({ steps = [], severity, isLoading }) {
  const [expanded, setExpanded] = useState(false);

  const sev = SEVERITY_CONFIG[severity] || SEVERITY_CONFIG['NONE'];

  if (isLoading && steps.length === 0) {
    return (
      <div style={containerStyle}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--text-secondary)', fontSize: '0.82rem' }}>
          <span style={pulseStyle}>⚙️</span>
          <span>Initialising investigation...</span>
        </div>
      </div>
    );
  }

  if (steps.length === 0) return null;

  return (
    <div style={containerStyle}>
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: expanded ? '16px' : 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {/* Severity badge */}
          {severity && (
            <span style={{
              fontSize: '0.7rem', fontWeight: 700, padding: '3px 8px',
              borderRadius: '4px', letterSpacing: '0.06em', textTransform: 'uppercase',
              background: sev.bg, border: `1px solid ${sev.border}`, color: sev.color,
            }}>
              {sev.icon} {severity}
            </span>
          )}
          <span style={{ fontSize: '0.78rem', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
            {steps.length} investigation step{steps.length !== 1 ? 's' : ''}
          </span>
        </div>
        <button
          onClick={() => setExpanded(v => !v)}
          style={{
            background: 'none', border: '1px solid var(--border-subtle)',
            color: 'var(--text-secondary)', borderRadius: '5px',
            fontSize: '0.72rem', fontFamily: 'var(--font-sans)', fontWeight: 600,
            padding: '3px 10px', cursor: 'pointer', transition: 'all 0.15s',
          }}
          onMouseEnter={e => { e.target.style.color = 'var(--text-primary)'; e.target.style.borderColor = 'var(--text-secondary)'; }}
          onMouseLeave={e => { e.target.style.color = 'var(--text-secondary)'; e.target.style.borderColor = 'var(--border-subtle)'; }}
        >
          {expanded ? '▲ Hide Steps' : `▼ View Investigation Steps (${steps.length})`}
        </button>
      </div>

      {/* Timeline */}
      {expanded && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
          {steps.map((step, i) => {
            const isLast = i === steps.length - 1;
            const label = TOOL_LABELS[step.tool] || step.tool;
            const icon = TOOL_ICONS[step.tool] || '🔧';
            return (
              <div key={i} style={{ display: 'flex', gap: '14px' }}>
                {/* Vertical connector */}
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
                  <div style={{
                    width: '28px', height: '28px', borderRadius: '50%',
                    background: 'rgba(0,255,136,0.08)', border: '1px solid rgba(0,255,136,0.25)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '0.78rem', flexShrink: 0, marginTop: '2px',
                  }}>
                    {icon}
                  </div>
                  {!isLast && (
                    <div style={{ width: '1px', flex: 1, background: 'var(--border)', margin: '4px 0', minHeight: '16px' }} />
                  )}
                </div>

                {/* Content */}
                <div style={{ flex: 1, paddingBottom: isLast ? 0 : '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span style={{ fontSize: '0.68rem', color: 'var(--accent)', fontFamily: 'var(--font-mono)' }}>
                      Step {step.step}
                    </span>
                    <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {label}
                    </span>
                  </div>
                  {step.reasoning && (
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '4px', fontStyle: 'italic' }}>
                      "{step.reasoning}"
                    </div>
                  )}
                  <div style={{
                    fontSize: '0.75rem', color: 'var(--text-tertiary)',
                    padding: '6px 10px', borderRadius: '6px',
                    background: 'var(--bg-tertiary)', border: '1px solid var(--border)',
                    fontFamily: 'var(--font-mono)',
                  }}>
                    {step.tool.startsWith('parallel_batch') && step.parallel_results && step.parallel_results.length > 0 ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        {step.parallel_results.map((pr, idx) => (
                          <div key={idx} style={{ display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>↳</span>
                            <span style={{ fontWeight: 600, color: 'var(--text-primary)', whiteSpace: 'nowrap' }}>
                              {TOOL_LABELS[pr.tool] || pr.tool}
                            </span>
                            <span style={{ color: 'var(--text-secondary)' }}>→</span>
                            <span style={{ color: 'var(--text-secondary)' }}>{pr.summary}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      step.summary
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

const containerStyle = {
  marginTop: '12px',
  padding: '12px 14px',
  borderRadius: '8px',
  background: 'rgba(0,255,136,0.03)',
  border: '1px solid var(--border)',
};

const pulseStyle = {
  display: 'inline-block',
  animation: 'pulse-dot 1.5s ease-in-out infinite',
};
