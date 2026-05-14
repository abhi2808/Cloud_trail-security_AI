import { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';

export default function PortalDropdown({ open, anchorRef, onClose, items, onSelect, emptyText }) {
  const menuRef = useRef(null);

  const getPosition = () => {
    if (!anchorRef.current) return { top: 0, left: 0, width: 0 };
    const rect = anchorRef.current.getBoundingClientRect();
    return {
      top: rect.bottom + 6,
      left: rect.left,
      width: Math.max(rect.width, 180),
    };
  };

  useEffect(() => {
    if (!open) return;
    const handleClick = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target) &&
          anchorRef.current && !anchorRef.current.contains(e.target)) {
        onClose();
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [open, onClose, anchorRef]);

  const pos = getPosition();

  return createPortal(
    <AnimatePresence>
      {open && (
        <motion.div
          ref={menuRef}
          className="portal-dropdown"
          style={{ top: pos.top, left: pos.left, minWidth: pos.width }}
          initial={{ opacity: 0, y: -6, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -4, scale: 0.98 }}
          transition={{ duration: 0.18, ease: [0.16, 1, 0.3, 1] }}
        >
          {items.length === 0 ? (
            <div style={{ padding: '10px 14px', fontSize: '0.76rem', color: 'var(--text-dim)' }}>
              {emptyText || 'No options'}
            </div>
          ) : (
            items.map((item, i) => (
              <button
                key={item.value}
                className={`portal-dropdown-item${item.active ? ' active' : ''}`}
                onClick={() => onSelect(item)}
              >
                {item.active && (
                  <span style={{ width: 5, height: 5, borderRadius: '50%', background: 'var(--accent)', flexShrink: 0, display: 'inline-block' }} />
                )}
                <span style={{ flex: 1 }}>{item.label}</span>
                {item.meta && (
                  <span style={{ fontSize: '0.66rem', color: 'var(--text-dim)', marginLeft: 4 }}>{item.meta}</span>
                )}
              </button>
            ))
          )}
        </motion.div>
      )}
    </AnimatePresence>,
    document.body
  );
}
