import React from 'react';
import { motion } from 'framer-motion';
import { Shield, ShieldAlert, ShieldX, Info, CheckCircle, ChevronRight } from 'lucide-react';
import EventCard from './EventCard';
import InvestigationTimeline from './InvestigationTimeline';

const SEV = {
  CRITICAL: { color: 'var(--sev-critical)', bg: 'rgba(248,113,113,0.1)',  border: 'rgba(248,113,113,0.3)', label: 'CRITICAL' },
  HIGH:     { color: 'var(--sev-high)',     bg: 'rgba(251,146,60,0.1)',   border: 'rgba(251,146,60,0.3)',  label: 'HIGH' },
  MEDIUM:   { color: 'var(--sev-medium)',   bg: 'rgba(252,211,77,0.08)',  border: 'rgba(252,211,77,0.28)', label: 'MEDIUM' },
  LOW:      { color: 'var(--sev-low)',      bg: 'rgba(96,165,250,0.08)',  border: 'rgba(96,165,250,0.25)', label: 'LOW' },
  NONE:     { color: 'var(--sev-none)',     bg: 'rgba(74,222,128,0.06)',  border: 'rgba(74,222,128,0.22)', label: 'CLEAR' },
};

const ease = [0.16, 1, 0.3, 1];

function SeverityBadge({ severity }) {
  if (!severity) return null;
  const s = SEV[severity] || SEV.NONE;
  return (
    <span className="sev-badge" style={{ color: s.color, background: s.bg, borderColor: s.border }}>
      {s.label}
    </span>
  );
}

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <motion.div
        className="msg-user"
        initial={{ opacity: 0, y: 12, filter: 'blur(4px)' }}
        animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
        transition={{ duration: 0.5, ease }}
      >
        <div className="msg-user-bubble">
          <div className="msg-user-text">{message.content}</div>
          <div className="msg-user-time">
            {new Date(message.timestamp).toLocaleTimeString('en-IN', {
              timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit',
            })}
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      className="msg-ai"
      initial={{ opacity: 0, y: 12, filter: 'blur(4px)' }}
      animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
      transition={{ duration: 0.5, ease }}
    >
      <div className="msg-ai-header">
        <Shield size={13} strokeWidth={1.5} style={{ color: 'var(--text-dim)' }} />
        <span className="msg-ai-label">AI Investigator</span>
        {message.severity && message.severity !== 'NONE' && (
          <SeverityBadge severity={message.severity} />
        )}
      </div>

      <div className="msg-ai-card">
        <div className="msg-ai-text">{message.content}</div>

        {message.steps_taken && message.steps_taken.length > 0 && (
          <InvestigationTimeline steps={message.steps_taken} severity={message.severity} />
        )}

        {message.recommended_actions && message.recommended_actions.length > 0 && (
          <div className="rec-actions">
            <div className="rec-actions-title">
              <ChevronRight size={12} strokeWidth={2} />
              Recommended Actions
            </div>
            <ol>
              {message.recommended_actions.map((action, i) => (
                <li key={i}>{action}</li>
              ))}
            </ol>
          </div>
        )}

        {message.rawEvents && message.rawEvents.length > 0 && (
          <EventCard events={message.rawEvents} count={message.eventsCount} />
        )}

        <div className="msg-ai-time">
          {new Date(message.timestamp).toLocaleTimeString('en-IN', {
            timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit',
          })}
        </div>
      </div>
    </motion.div>
  );
}
