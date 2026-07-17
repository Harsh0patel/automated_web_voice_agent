import '@testing-library/jest-dom';
import { vi, afterEach } from 'vitest';

// ---- Mock HTMLMediaElement (Audio) for jsdom ----
if (typeof HTMLMediaElement !== 'undefined') {
  HTMLMediaElement.prototype.play = () => Promise.resolve();
  HTMLMediaElement.prototype.pause = () => {};
  HTMLMediaElement.prototype.load = () => {};
  HTMLMediaElement.prototype.addTextTrack = () => {};
}

// ---- Mock Element.scrollIntoView (not available in jsdom) ----
if (typeof Element !== 'undefined' && !Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = vi.fn();
}

// ---- Mock window.scrollTo ----
if (!window.scrollTo) {
  window.scrollTo = vi.fn();
}

// ---- Mock crypto.randomUUID ----
if (!globalThis.crypto?.randomUUID) {
  Object.defineProperty(globalThis, 'crypto', {
    value: {
      randomUUID: () => 'test-uuid-' + Math.random().toString(36).slice(2, 10),
    },
    writable: true,
  });
}

// ---- Mock WebSocket globally (simple class-based mock) ----
class MockWebSocketClass {
  constructor(url) {
    this.url = url;
    this.send = vi.fn();
    this.close = vi.fn();
    this.readyState = 1; // WebSocket.OPEN
    this.onopen = null;
    this.onclose = null;
    this.onmessage = null;
    this.onerror = null;

    MockWebSocketClass.__instances.push(this);

    // Auto-trigger onopen asynchronously (matches real browser behavior)
    setTimeout(() => {
      if (this.onopen) this.onopen();
    }, 0);
  }

  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;
  static __instances = [];
}

globalThis.WebSocket = MockWebSocketClass;

/**
 * Get the most recent WebSocket mock instance (for sending test messages).
 */
globalThis.__getLastWsInstance = () => {
  const instances = MockWebSocketClass.__instances;
  return instances[instances.length - 1] || null;
};

/**
 * Clean up WebSocket instances between tests.
 */
globalThis.__resetWsMocks = () => {
  MockWebSocketClass.__instances = [];
};

// ---- Auto-reset DOM and WS mocks after each test ----
afterEach(() => {
  document.body.innerHTML = '';
  globalThis.__resetWsMocks();
});
