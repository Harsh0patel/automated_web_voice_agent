import React, { useState, useEffect, Suspense } from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import Navbar from './components/Navbar.jsx';
import Footer from './components/Footer.jsx';
import SkeletonLoader from './components/SkeletonLoader.jsx';
import { preloadPages, preloadPage } from './utils/preload.js';

// Lazy-loaded page components — each becomes a separate JS chunk
const Home = React.lazy(() => import('./pages/Home.jsx'));
const Services = React.lazy(() => import('./pages/Services.jsx'));
const Doctors = React.lazy(() => import('./pages/Doctors.jsx'));
const About = React.lazy(() => import('./pages/About.jsx'));
const Contact = React.lazy(() => import('./pages/Contact.jsx'));
const Insurance = React.lazy(() => import('./pages/Insurance.jsx'));
const Blog = React.lazy(() => import('./pages/Blog.jsx'));
const Careers = React.lazy(() => import('./pages/Careers.jsx'));
const Pharmacy = React.lazy(() => import('./pages/Pharmacy.jsx'));
const Booking = React.lazy(() => import('./pages/Booking.jsx'));
const NotFound = React.lazy(() => import('./pages/NotFound.jsx'));

const STORAGE_THEME = 'medicare-theme';
/* ── Likely next-page map based on current route ── */
const NEXT_PAGES = {
  '/':        ['/services', '/doctors', '/about', '/booking'],
  '/services': ['/booking', '/doctors', '/'],
  '/doctors':  ['/booking', '/services', '/'],
  '/about':    ['/services', '/doctors', '/contact'],
  '/contact':  ['/', '/booking'],
  '/insurance':['/booking', '/services', '/'],
  '/blog':     ['/', '/about'],
  '/careers':  ['/about', '/contact', '/'],
  '/pharmacy': ['/booking', '/services', '/'],
  '/booking':  ['/', '/services', '/doctors'],
};

export default function App() {
  const location = useLocation();
  const [isDark, setIsDark] = useState(() => localStorage.getItem(STORAGE_THEME) === 'dark');

  // Scroll to top on route change
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [location.pathname]);

  // Theme persistence
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
    localStorage.setItem(STORAGE_THEME, isDark ? 'dark' : 'light');
  }, [isDark]);

  /* ── Preload likely next pages on route change ── */
  useEffect(() => {
    const pages = NEXT_PAGES[location.pathname];
    if (pages) {
      preloadPages(pages);
    }
  }, [location.pathname]);

  /* ── Warm up high‑priority pages after initial paint ── */
  useEffect(() => {
    const id = requestIdleCallback
      ? requestIdleCallback(() => preloadPages(['/services', '/booking', '/about']), { timeout: 2000 })
      : setTimeout(() => preloadPages(['/services', '/booking', '/about']), 1000);
    return () => {
      if (requestIdleCallback) cancelIdleCallback(id);
      else clearTimeout(id);
    };
  }, []);

  return (
    <div className="app">
      <Navbar isDark={isDark} onToggleTheme={() => setIsDark(p => !p)} />
      <main className="main-content">
        <Suspense fallback={<SkeletonLoader />}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/services" element={<Services />} />
            <Route path="/doctors" element={<Doctors />} />
            <Route path="/about" element={<About />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="/insurance" element={<Insurance />} />
            <Route path="/blog" element={<Blog />} />
            <Route path="/careers" element={<Careers />} />
            <Route path="/pharmacy" element={<Pharmacy />} />
            <Route path="/booking" element={<Booking />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
      </main>
      <Footer />
    </div>
  );
}
