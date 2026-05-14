import { motion } from 'framer-motion';
import { Search, Shield, Database, AlertTriangle } from 'lucide-react';
import useChatStore from '../store/chatStore';
import demoQueries from '../constants/demoQueries';

const ease = [0.16, 1, 0.3, 1];

const CHIP_ICONS = [Search, Shield, Database, AlertTriangle];

export default function SuggestedQueries({ accountName }) {
  const sendMessage = useChatStore((state) => state.sendMessage);

  return (
    <div className="suggested-wrap">
      <motion.p
        className="suggested-eyebrow"
        initial={{ opacity: 0, y: 20, filter: 'blur(6px)' }}
        animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
        transition={{ duration: 0.7, ease }}
      >
        Ask anything about your AWS account
      </motion.p>
      {accountName && (
        <motion.p
          className="suggested-sub"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease, delay: 0.1 }}
        >
          Investigating <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>{accountName}</span>
        </motion.p>
      )}
      <div className="suggested-chips">
        {demoQueries.map((item, idx) => {
          const Icon = CHIP_ICONS[idx] || Search;
          return (
            <motion.button
              key={idx}
              className="suggested-chip"
              onClick={() => sendMessage(item.query)}
              id={`demo-query-${idx}`}
              initial={{ opacity: 0, y: 14, filter: 'blur(3px)' }}
              animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
              transition={{ duration: 0.5, ease, delay: 0.18 + idx * 0.07 }}
            >
              <Icon size={14} strokeWidth={1.5} style={{ color: 'var(--text-dim)', flexShrink: 0, marginTop: 1 }} />
              <span className="chip-label">{item.label}</span>
              <span className="chip-query">{item.query}</span>
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}
