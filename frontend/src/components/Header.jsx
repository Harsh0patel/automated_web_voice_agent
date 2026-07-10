import React from 'react';

export default function Header({ status, isDark, onToggleTheme, onToggleSidebar }) {
  return (
    <header className="header">
      <div className="header-brand">
        <button className="sidebar-toggle" onClick={onToggleSidebar} aria-label="Menu">
          ☰
        </button>
        <span className="logo">🎙️</span>
        <span className="brand-text">AI Voice Assistant</span>
      </div>
      <div className="header-actions">
        <div className="header-status">
          <span className={`status-dot ${status.state}`} />
          <span className="status-label">{status.label}</span>
        </div>
        <button className="theme-btn" onClick={onToggleTheme} title="Toggle theme">
          {isDark ? '☀️' : '🌙'}
        </button>
      </div>
    </header>
  );
}
