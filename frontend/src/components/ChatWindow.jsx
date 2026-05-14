import useChatStore from '../store/chatStore';
import MessageBubble from './MessageBubble';
import ThinkingIndicator from './ThinkingIndicator';

// Purely presentational — no scroll logic here.
// Scroll is owned by the parent's container ref.
export default function ChatWindow({ emptyState }) {
  const messages = useChatStore((state) => state.messages);
  const isLoading = useChatStore((state) => state.isLoading);

  if (messages.length === 0) {
    return (
      <div style={{
        minHeight: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '40px 32px',
        textAlign: 'center',
      }}>
        <div style={{ width: '100%', maxWidth: 620 }}>
          {emptyState}
        </div>
      </div>
    );
  }

  return (
    <div className="chat-messages">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
      {isLoading && <ThinkingIndicator />}
    </div>
  );
}
