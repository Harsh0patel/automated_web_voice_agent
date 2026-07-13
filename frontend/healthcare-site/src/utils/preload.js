/*
 * Page Preloading Utility
 *
 * Maps each route path to its dynamic import so we can eagerly start
 * loading a lazy chunk *before* the user navigates — e.g. on hover.
 *
 * Because Vite caches dynamic imports, calling loader() here and
 * React.lazy(() => import(...)) in App.jsx share the same module promise.
 * The first call triggers the HTTP request; subsequent calls resolve
 * instantly from the module cache.
 */

const pageLoaders = {
  '/':        () => import('../pages/Home.jsx'),
  '/services': () => import('../pages/Services.jsx'),
  '/doctors':  () => import('../pages/Doctors.jsx'),
  '/about':    () => import('../pages/About.jsx'),
  '/contact':  () => import('../pages/Contact.jsx'),
  '/insurance':() => import('../pages/Insurance.jsx'),
  '/blog':     () => import('../pages/Blog.jsx'),
  '/careers':  () => import('../pages/Careers.jsx'),
  '/pharmacy': () => import('../pages/Pharmacy.jsx'),
  '/booking':  () => import('../pages/Booking.jsx'),
};

/**
 * Start downloading a page chunk immediately.
 * Safe to call multiple times — the module is only fetched once.
 */
export function preloadPage(path) {
  const loader = pageLoaders[path];
  if (loader) {
    loader().catch(() => {});
  }
}

/**
 * Preload multiple pages in parallel.
 * Useful for initial/pre-boot warmup.
 */
export function preloadPages(paths) {
  paths.forEach(preloadPage);
}

/**
 * Preload all available pages (for aggressive strategies).
 */
export function preloadAll() {
  Object.values(pageLoaders).forEach((loader) => {
    loader().catch(() => {});
  });
}
