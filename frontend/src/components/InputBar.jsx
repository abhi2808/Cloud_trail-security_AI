import { useState, useRef, useEffect } from 'react';
import { ArrowUp } from 'lucide-react';
import useChatStore from '../store/chatStore';

const MAX_CHARS = 500;

export default function InputBar() {
  const [text, setText] = useState('');
  const isLoading = useChatStore((state) => state.isLoading);
  const sendMessage = useChatStore((state) => state.sendMessage);
  const textareaRef = useRef(null);

  useEffect(() => {
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = 'auto';
      ta.style.height = Math.min(ta.scrollHeight, 120) + 'px';
    }
  }, [text]);

  const handleSubmit = () => {
    const trimmed = text.trim();
    if (!trimmed || isLoading || trimmed.length > MAX_CHARS) return;
    sendMessage(trimmed);
    setText('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const charCount = text.length;
  const showCounter = charCount > MAX_CHARS * 0.8;
  const isOverLimit = charCount > MAX_CHARS;

  return (
    <div>
      <div className="input-glass">
        <textarea
          ref={textareaRef}
          className="input-textarea"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything about your AWS account..."
          disabled={isLoading}
          rows={1}
          id="query-input"
        />
        {showCounter && (
          <span className={`char-counter${isOverLimit ? ' char-over' : ''}`}>
            {charCount}/{MAX_CHARS}
          </span>
        )}
        <button
          className="send-btn"
          onClick={handleSubmit}
          disabled={isLoading || !text.trim() || isOverLimit}
          title="Send"
          id="send-button"
        >
          <ArrowUp size={16} strokeWidth={2} />
        </button>
      </div>
    </div>
  );
}
