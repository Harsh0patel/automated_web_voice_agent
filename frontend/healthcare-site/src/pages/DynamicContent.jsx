import React, { useState, useEffect } from 'react';
import DynamicPageRenderer from './DynamicPageRenderer.jsx';
import './DynamicPageRenderer.css';

const API_BASE = `http://${window.location.hostname}:8000`;

export default function DynamicContent() {
  const [components, setComponents] = useState([]);
  const [types, setTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchComponents() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${API_BASE}/components?limit=200`);
        if (!res.ok) throw new Error(`API returned ${res.status}`);
        const data = await res.json();
        if (cancelled) return;
        setComponents(data.components || []);
        setTypes(data.types || []);
      } catch (err) {
        if (cancelled) return;
        setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchComponents();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <div className="dp-page">
        <div className="dp-page-header">
          <div className="container dp-page-header__inner">
            <h1>Scraped Content</h1>
            <p>Loading components from the registry...</p>
          </div>
        </div>
        <div className="dp-loading">
          <div className="dp-spinner" />
          <p className="dp-loading__text">Fetching scraped components...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dp-page">
        <div className="dp-page-header">
          <div className="container dp-page-header__inner">
            <h1>Scraped Content</h1>
            <p>Something went wrong loading the data.</p>
          </div>
        </div>
        <div className="dp-error">
          <div className="dp-error__icon">⚠️</div>
          <h2 className="dp-error__title">Failed to load components</h2>
          <p className="dp-error__msg">{error}</p>
          <p className="dp-error__hint">
            Make sure the backend is running on port 8000 and you have scraped some data.
          </p>
          <button className="dp-retry-btn" onClick={() => window.location.reload()}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <DynamicPageRenderer
      components={components}
      title="Scraped Content"
      subtitle={`${components.length} components across ${types.length} types — rendered dynamically from the registry`}
    />
  );
}
