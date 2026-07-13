/* =============================================
   Shared SVG Icon Components
   Use these throughout the app instead of
   inlining raw SVGs to reduce bundle size.
   ============================================= */

import React from 'react';

const defaults = {
  fill: 'none',
  stroke: 'currentColor',
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
};

export function ArrowRight({ size = 18, strokeWidth = 2.5, ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...defaults} strokeWidth={strokeWidth} {...props}>
      <path d="M5 12h14M12 5l7 7-7 7" />
    </svg>
  );
}

export function ArrowLeft({ size = 18, strokeWidth = 2.5, ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...defaults} strokeWidth={strokeWidth} {...props}>
      <path d="M19 12H5M12 19l-7-7 7-7" />
    </svg>
  );
}

export function ChevronDown({ size = 20, strokeWidth = 2.5, className, ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...defaults} strokeWidth={strokeWidth} className={className} {...props}>
      <polyline points="6 9 12 15 18 9" />
    </svg>
  );
}

export function ChevronLeft({ size = 18, strokeWidth = 2.5, ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...defaults} strokeWidth={strokeWidth} {...props}>
      <polyline points="15 18 9 12 15 6" />
    </svg>
  );
}

export function ChevronRight({ size = 18, strokeWidth = 2.5, ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...defaults} strokeWidth={strokeWidth} {...props}>
      <polyline points="9 18 15 12 9 6" />
    </svg>
  );
}

export function Check({ size = 16, strokeWidth = 2.5, ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...defaults} strokeWidth={strokeWidth} color="#0d9488" {...props}>
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

export function Location({ size = 16, ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...defaults} stroke="#0d9488" strokeWidth="2" {...props}>
      <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
      <circle cx="12" cy="10" r="3" />
    </svg>
  );
}

export function Phone({ size = 16, ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...defaults} stroke="#0d9488" strokeWidth="2" {...props}>
      <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
    </svg>
  );
}

export function Mail({ size = 16, ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...defaults} stroke="#0d9488" strokeWidth="2" {...props}>
      <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
      <polyline points="22,6 12,13 2,6" />
    </svg>
  );
}
