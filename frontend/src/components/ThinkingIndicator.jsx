import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Shield } from 'lucide-react';

const stages = [
  'Parsing your query...',
  'Querying CloudTrail...',
  'Cross-referencing services...',
  'Analyzing findings...',
];

const ease = [0.16, 1, 0.3, 1];

export default function ThinkingIndicator() {
  const [stageIndex, setStageIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setStageIndex((prev) => (prev + 1) % stages.length);
    }, 2200);
    return () => clearInterval(interval);
  }, []);

  return (
    <motion.div
      className="thinking-wrap"
      initial={{ opacity: 0, y: 12, filter: 'blur(4px)' }}
      animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
      transition={{ duration: 0.5, ease }}
    >
      <div className="thinking-header">
        <Shield size={13} strokeWidth={1.5} style={{ color: 'var(--text-dim)' }} />
        <span style={{ fontSize: '0.72rem', fontWeight: 500, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          AI Investigator
        </span>
      </div>
      <div className="thinking-card">
        <div className="thinking-dots">
          {[0, 1, 2].map((i) => (
            <motion.span
              key={i}
              className="thinking-dot"
              animate={{
                opacity: [0.25, 1, 0.25],
                scale: [0.8, 1, 0.8],
              }}
              transition={{
                duration: 1.4,
                repeat: Infinity,
                ease: 'easeInOut',
                delay: i * 0.18,
              }}
            />
          ))}
        </div>
        <motion.span
          key={stageIndex}
          className="thinking-text"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.4 }}
        >
          {stages[stageIndex]}
        </motion.span>
      </div>
    </motion.div>
  );
}
