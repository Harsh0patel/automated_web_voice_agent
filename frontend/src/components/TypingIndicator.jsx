import React from 'react';

export default function TypingIndicator({ visible }) {
  if (!visible) return null;
  return (
    <div className="typing-indicator">
      <span /><span /><span />
    </div>
  );
}
