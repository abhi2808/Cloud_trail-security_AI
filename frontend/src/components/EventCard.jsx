import { useState } from 'react';

/**
 * Converts a UTC datetime string to IST formatted string.
 */
function toIST(dateStr) {
  try {
    const date = new Date(dateStr);
    return date.toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  } catch {
    return dateStr;
  }
}

export default function EventCard({ events, count }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="event-card">
      <button
        className="event-card-toggle"
        onClick={() => setIsExpanded(!isExpanded)}
        id="toggle-events"
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          className={`toggle-chevron ${isExpanded ? 'expanded' : ''}`}
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
        <span>View Raw Events ({count})</span>
      </button>

      {isExpanded && (
        <div className="event-table-container">
          <table className="event-table">
            <thead>
              <tr>
                <th>Time (IST)</th>
                <th>Event Name</th>
                <th>User</th>
                <th>Source IP</th>
                <th>Region</th>
                <th>Error</th>
              </tr>
            </thead>
            <tbody>
              {events.map((event, idx) => (
                <tr
                  key={event.event_id || idx}
                  className={event.error_code ? 'event-row-error' : ''}
                >
                  <td className="mono">{toIST(event.event_time)}</td>
                  <td className="event-name-cell">{event.event_name}</td>
                  <td>{event.username || '—'}</td>
                  <td className="mono">{event.source_ip || '—'}</td>
                  <td>{event.aws_region || '—'}</td>
                  <td className={event.error_code ? 'error-text' : ''}>
                    {event.error_code || '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
