import { useState, useRef, useEffect } from 'react';
import ChatWindow from '../components/ChatWindow';
import InputBar from '../components/InputBar';
import useChatStore from '../store/chatStore';

const AWS_REGIONS = [
  { value: 'all', label: '🌐 All Regions' },
  { value: 'us-east-1', label: 'us-east-1' },
  { value: 'us-east-2', label: 'us-east-2' },
  { value: 'us-west-1', label: 'us-west-1' },
  { value: 'us-west-2', label: 'us-west-2' },
  { value: 'eu-west-1', label: 'eu-west-1' },
  { value: 'eu-west-2', label: 'eu-west-2' },
  { value: 'eu-west-3', label: 'eu-west-3' },
  { value: 'eu-central-1', label: 'eu-central-1' },
  { value: 'eu-north-1', label: 'eu-north-1' },
  { value: 'ap-south-1', label: 'ap-south-1' },
  { value: 'ap-southeast-1', label: 'ap-southeast-1' },
  { value: 'ap-southeast-2', label: 'ap-southeast-2' },
  { value: 'ap-northeast-1', label: 'ap-northeast-1' },
  { value: 'ap-northeast-2', label: 'ap-northeast-2' },
  { value: 'ap-northeast-3', label: 'ap-northeast-3' },
  { value: 'ca-central-1', label: 'ca-central-1' },
  { value: 'sa-east-1', label: 'sa-east-1' },
];

export default function HomePage() {
  const messagesCount = useChatStore((state) => state.messages.length);
  const selectedRegion = useChatStore((state) => state.selectedRegion);
  const setRegion = useChatStore((state) => state.setRegion);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handler = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const currentRegionLabel =
    AWS_REGIONS.find((r) => r.value === selectedRegion)?.label || selectedRegion;

  return (
    <div className="app-layout">
      {/* Header */}
      <header className="app-header">
        <div className="header-left">
          <div className="header-logo">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              <path d="M9 12l2 2 4-4" />
            </svg>
          </div>
          <div>
            <h1 className="header-title">CloudTrail AI Investigator</h1>
            <p className="header-subtitle">Natural Language Security Investigation</p>
          </div>
        </div>

        <div className="header-right">
          {/* Region Dropdown */}
          <div className="region-dropdown-wrapper" ref={dropdownRef}>
            <button
              className="region-dropdown-trigger"
              onClick={() => setDropdownOpen((o) => !o)}
              id="region-selector"
              title="Select AWS Region"
            >
              <span className="badge-dot" />
              <span className="region-trigger-label">{currentRegionLabel}</span>
              <svg
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                className={`region-chevron ${dropdownOpen ? 'open' : ''}`}
              >
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </button>

            {dropdownOpen && (
              <div className="region-dropdown-menu">
                <div className="region-dropdown-header">Select Region</div>
                {AWS_REGIONS.map((r) => (
                  <button
                    key={r.value}
                    className={`region-dropdown-item ${selectedRegion === r.value ? 'active' : ''}`}
                    onClick={() => {
                      setRegion(r.value);
                      setDropdownOpen(false);
                    }}
                  >
                    {r.value === 'all' ? (
                      <span className="region-item-global">🌐</span>
                    ) : (
                      <span className="region-item-dot" />
                    )}
                    {r.label}
                    {selectedRegion === r.value && (
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ marginLeft: 'auto' }}>
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Clear button */}
          {messagesCount > 0 && (
            <button
              className="clear-button"
              onClick={() => useChatStore.getState().clearMessages()}
              title="Clear conversation"
              id="clear-chat"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="3 6 5 6 21 6" />
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              </svg>
            </button>
          )}
        </div>
      </header>

      {/* Chat Window */}
      <main className="app-main">
        <ChatWindow />
      </main>

      {/* Input Bar */}
      <footer className="app-footer">
        <InputBar />
      </footer>
    </div>
  );
}
