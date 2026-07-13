import React from 'react';
import './SkeletonLoader.css';

/**
 * SkeletonLoader — mimics the site's page layout so the user sees
 * a realistic placeholder while the lazy chunk loads.
 *
 * Renders: page-header → grid of content cards → CTA banner
 */
export default function SkeletonLoader() {
  return (
    <div className="skeleton">
      {/* ── Page Header Skeleton ── */}
      <section className="skeleton__header">
        <div className="container skeleton__header-inner">
          <div className="skeleton__block skeleton__tag" />
          <div className="skeleton__block skeleton__title" />
          <div className="skeleton__block skeleton__subtitle" />
        </div>
      </section>

      {/* ── Content Grid Skeleton ── */}
      <section className="section skeleton__body">
        <div className="container">
          {/* Section header */}
          <div className="skeleton__section-header">
            <div className="skeleton__block skeleton__tag skeleton__tag--sm" />
            <div className="skeleton__block skeleton__title skeleton__title--sm" />
            <div className="skeleton__block skeleton__text skeleton__text--narrow" />
          </div>

          {/* Card grid */}
          <div className="skeleton__grid">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="skeleton__card">
                <div className="skeleton__block skeleton__icon-box" />
                <div className="skeleton__block skeleton__card-title" />
                <div className="skeleton__block skeleton__card-text" />
                <div className="skeleton__block skeleton__card-text skeleton__card-text--short" />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA Banner Skeleton ── */}
      <section className="skeleton__cta">
        <div className="container">
          <div className="skeleton__cta-inner">
            <div className="skeleton__block skeleton__title skeleton__title--sm" />
            <div className="skeleton__block skeleton__text skeleton__text--narrow" />
            <div className="skeleton__block skeleton__btn" />
          </div>
        </div>
      </section>
    </div>
  );
}
