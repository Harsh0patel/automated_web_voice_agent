import React from 'react';
import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <section className="section" style={{ textAlign: 'center', padding: '120px 0' }}>
      <div className="container animate-in">
        <div style={{ fontSize: '5rem', marginBottom: '20px' }}>🔍</div>
        <h1 style={{ fontSize: '3rem', fontWeight: 800, marginBottom: '12px', color: 'var(--text-primary)' }}>
          404
        </h1>
        <p style={{ fontSize: '1.125rem', color: 'var(--text-secondary)', marginBottom: '32px', maxWidth: '500px', margin: '0 auto 32px' }}>
          Oops! The page you're looking for doesn't exist. It might have been moved or deleted.
        </p>
        <Link to="/" className="btn btn-primary">
          Back to Home
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
        </Link>
      </div>
    </section>
  );
}
