import React, { useState } from 'react';

export default function Sidebar({ open, pages, scrapeStatus, onScrape, onClearPages, onCloseMobile }) {
  const [url, setUrl] = useState('');

  function handleScrape() {
    onScrape(url);
    setUrl('');
  }

  return (
    <aside className={`sidebar ${open ? 'open' : ''}`}>
      <div className="sidebar-header">
        <h3>🔗 Knowledge Base</h3>
        <div className="scrape-group">
          <input
            type="url"
            value={url}
            onChange={e => setUrl(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleScrape()}
            placeholder="https://example.com"
          />
          <button onClick={handleScrape}>Scrape</button>
        </div>
        {scrapeStatus && <div className="scrape-status">{scrapeStatus}</div>}
      </div>

      <div className="sidebar-body">
        <div className="pages-header">
          <span className="section-title">Scraped Pages</span>
          <span className="page-count">{pages.length} page{pages.length !== 1 ? 's' : ''}</span>
        </div>

        <div className="pages-list">
          {pages.length === 0 ? (
            <div className="pages-empty">
              <div className="empty-icon">📚</div>
              <p>No pages yet. Paste a URL above to start building your knowledge base!</p>
            </div>
          ) : (
            pages.map((p, i) => (
              <div className="page-item" key={p.url || i} title={p.url}>
                <img
                  className="favicon"
                  src={`https://www.google.com/s2/favicons?domain=${encodeURIComponent(new URL(p.url).hostname)}&sz=16`}
                  alt=""
                  onError={e => (e.target.style.display = 'none')}
                />
                <div className="page-info">
                  <div className="page-title">{p.title || p.url.replace(/^https?:\/\//, '')}</div>
                  <div className="page-url">{p.url.replace(/^https?:\/\//, '')}</div>
                </div>
              </div>
            ))
          )}
        </div>

        {pages.length > 0 && (
          <div className="sidebar-footer">
            <button className="clear-btn" onClick={onClearPages}>
              🗑️ Clear all
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}
