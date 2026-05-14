import { useState } from 'react';
import { ChevronDown, Table } from 'lucide-react';

function toIST(dateStr) {
  try {
    return new Date(dateStr).toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
    });
  } catch { return dateStr; }
}

export default function EventCard({ events, count }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="event-card">
      <button className="event-toggle" onClick={() => setIsExpanded(!isExpanded)}>
        <Table size={13} strokeWidth={1.5} style={{ flexShrink: 0 }} />
        <ChevronDown
          size={13}
          strokeWidth={1.5}
          className={`event-toggle-chevron${isExpanded ? ' open' : ''}`}
          style={{ flexShrink: 0 }}
        />
        <span>Raw events ({count})</span>
      </button>

      {isExpanded && (
        <div className="event-table-wrap">
          <table className="event-table">
            <thead>
              <tr>
                <th>Time (IST)</th>
                <th>Event</th>
                <th>User</th>
                <th>Source IP</th>
                <th>Region</th>
                <th>Error</th>
              </tr>
            </thead>
            <tbody>
              {events.map((event, idx) => (
                <tr key={event.event_id || idx} className={event.error_code ? 'event-row-error' : ''}>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{toIST(event.event_time)}</td>
                  <td className="event-name-cell">{event.event_name}</td>
                  <td>{event.username || '—'}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{event.source_ip || '—'}</td>
                  <td>{event.aws_region || '—'}</td>
                  <td className={event.error_code ? 'event-error-text' : ''}>{event.error_code || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
