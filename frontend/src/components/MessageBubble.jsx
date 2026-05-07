import React from 'react';
import EventCard from './EventCard';
import InvestigationTimeline from './InvestigationTimeline';

const SEVERITY_CONFIG = {
  CRITICAL: { color: '#ff4444', bg: 'rgba(255,68,68,0.12)', border: 'rgba(255,68,68,0.3)',  icon: '🔴' },
  HIGH:     { color: '#ff8c00', bg: 'rgba(255,140,0,0.12)', border: 'rgba(255,140,0,0.3)',  icon: '🟠' },
  MEDIUM:   { color: '#ffd700', bg: 'rgba(255,215,0,0.10)', border: 'rgba(255,215,0,0.3)',  icon: '🟡' },
  LOW:      { color: '#58a6ff', bg: 'rgba(88,166,255,0.10)', border: 'rgba(88,166,255,0.3)', icon: '🔵' },
  NONE:     { color: '#00ff88', bg: 'rgba(0,255,136,0.08)', border: 'rgba(0,255,136,0.25)', icon: '🟢' },
};

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  const sev = message.severity ? SEVERITY_CONFIG[message.severity] : null;

  return (
    <div className={`message-bubble ${isUser ? 'message-user' : 'message-assistant'}`}>
      <div className="message-avatar">
        {isUser ? (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
        ) : (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          </svg>
        )}
      </div>

      <div className="message-content-wrapper">
        {/* Header */}
        <div className="message-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="message-role">{isUser ? 'You' : 'cloudComply Investigator AI'}</span>
            {/* Severity badge next to AI label */}
            {!isUser && sev && message.severity !== 'NONE' && (
              <span style={{
                fontSize: '0.65rem', fontWeight: 700, padding: '2px 6px',
                borderRadius: '4px', letterSpacing: '0.05em', textTransform: 'uppercase',
                background: sev.bg, border: `1px solid ${sev.border}`, color: sev.color,
              }}>
                {sev.icon} {message.severity}
              </span>
            )}
          </div>
          <span className="message-time">
            {new Date(message.timestamp).toLocaleTimeString('en-IN', {
              timeZone: 'Asia/Kolkata',
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
        </div>

        {/* Message text */}
        <div className="message-text">
          {message.content.split('\n').map((line, i) => (
            <span key={i}>
              {line}
              {i < message.content.split('\n').length - 1 && <br />}
            </span>
          ))}
        </div>

        {/* Investigation Timeline */}
        {!isUser && message.steps_taken && message.steps_taken.length > 0 && (
          <InvestigationTimeline
            steps={message.steps_taken}
            severity={message.severity}
            isLoading={false}
          />
        )}

        {/* Recommended Actions */}
        {!isUser && message.recommended_actions && message.recommended_actions.length > 0 && (
          <div style={{
            marginTop: '12px', padding: '12px 14px', borderRadius: '8px',
            background: 'rgba(88,166,255,0.05)', border: '1px solid rgba(88,166,255,0.2)',
          }}>
            <div style={{
              fontSize: '0.72rem', fontWeight: 700, color: '#58a6ff',
              textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '8px',
            }}>
              ✅ Recommended Actions
            </div>
            <ol style={{ margin: 0, paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '5px' }}>
              {message.recommended_actions.map((action, i) => (
                <li key={i} style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  {action}
                </li>
              ))}
            </ol>
          </div>
        )}

        {/* Raw Events (legacy / backward compat) */}
        {!isUser && message.rawEvents && message.rawEvents.length > 0 && (
          <EventCard events={message.rawEvents} count={message.eventsCount} />
        )}
      </div>
    </div>
  );
}
