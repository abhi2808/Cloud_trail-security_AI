import { useState, useEffect } from 'react';

const thinkingStages = [
  'Parsing your query...',
  'Querying CloudTrail...',
  'Analyzing events...',
];

export default function ThinkingIndicator() {
  const [stageIndex, setStageIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setStageIndex((prev) => (prev + 1) % thinkingStages.length);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="thinking-indicator">
      <div className="thinking-avatar">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        </svg>
      </div>
      <div className="thinking-content">
        <div className="thinking-dots">
          <span className="dot dot-1" />
          <span className="dot dot-2" />
          <span className="dot dot-3" />
        </div>
        <span className="thinking-text">{thinkingStages[stageIndex]}</span>
      </div>
    </div>
  );
}
