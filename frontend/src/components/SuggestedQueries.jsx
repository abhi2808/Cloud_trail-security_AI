import useChatStore from '../store/chatStore';
import demoQueries from '../constants/demoQueries';

export default function SuggestedQueries() {
  const sendMessage = useChatStore((state) => state.sendMessage);

  return (
    <div className="suggested-queries">
      <h3 className="suggested-title">Try asking...</h3>
      <div className="suggested-chips">
        {demoQueries.map((item, idx) => (
          <button
            key={idx}
            className="suggested-chip"
            onClick={() => sendMessage(item.query)}
            id={`demo-query-${idx}`}
          >
            <span className="chip-label">{item.label}</span>
            <span className="chip-query">{item.query}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
