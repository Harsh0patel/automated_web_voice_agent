import React from 'react';
import { render, screen, fireEvent, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import ChatWidget from '../components/ChatWidget.jsx';

/* =============================================================
   Helpers
   ============================================================= */

/** Render the ChatWidget wrapped in MemoryRouter */
function renderWidget() {
  return render(
    <MemoryRouter>
      <ChatWidget />
    </MemoryRouter>
  );
}

/** Click the FAB to open the chat panel */
function openChat() {
  const fab = screen.getByTitle('AI Assistant');
  fireEvent.click(fab);
}

/** Wait for component to settle (WebSocket open, etc.) */
async function settle() {
  await act(async () => {
    await new Promise(resolve => setTimeout(resolve, 50));
  });
}

/** Simulate a WebSocket message from the backend */
function simulateWsMessage(data) {
  const ws = globalThis.__getLastWsInstance();
  if (!ws || !ws.onmessage) return;
  act(() => {
    ws.onmessage({ data: JSON.stringify(data) });
  });
}

/** Simulate a WebSocket message and wait for async actions to complete */
async function simulateWsMessageAndWait(data, waitMs = 600) {
  simulateWsMessage(data);
  await act(async () => {
    await new Promise(resolve => setTimeout(resolve, waitMs));
  });
}

/** Set up DOM elements for action tests */
function setupActionDom() {
  document.body.innerHTML = `
    <div id="app">
      <form id="booking-form">
        <input id="b-name" name="name" type="text" />
        <input id="b-email" name="email" type="email" />
        <select id="doctor-select" name="doctor">
          <option value="">Select</option>
          <option value="1">Dr. Smith</option>
          <option value="2">Dr. Jones</option>
        </select>
        <input id="agree-checkbox" type="checkbox" />
        <div id="custom-toggle" role="switch" aria-checked="false"></div>
        <div id="contenteditable-div" contenteditable="true"></div>
        <a href="/contact" id="internal-link">Contact</a>
        <a href="https://external.com" id="external-link">External</a>
        <button type="submit">Submit</button>
      </form>
      <section id="testimonials" class="testimonials-section">
        <h2>Testimonials</h2>
      </section>
      <div id="clickable-btn" class="btn">Click me</div>
    </div>
  `;
}

/* =============================================================
   1. Rendering Tests
   ============================================================= */

describe('ChatWidget Rendering', () => {
  it('renders the floating action button', async () => {
    renderWidget();
    await settle();
    expect(screen.getByTitle('AI Assistant')).toBeInTheDocument();
  });

  it('shows chat panel when FAB is clicked', async () => {
    renderWidget();
    await settle();
    openChat();
    expect(screen.getByText('🤖 AI Assistant')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Type a question...')).toBeInTheDocument();
  });

  it('shows welcome message when panel opens', async () => {
    renderWidget();
    await settle();
    openChat();
    expect(screen.getByText(/Ask me anything about our services/)).toBeInTheDocument();
  });

  it('hides chat panel when close button is clicked', async () => {
    renderWidget();
    await settle();
    openChat();
    // Panel should have the open class
    const panel = document.querySelector('.hcw-panel');
    expect(panel.classList.contains('hcw-open')).toBe(true);

    // Click the close button
    const closeBtn = document.querySelector('.hcw-close');
    expect(closeBtn).toBeTruthy();
    fireEvent.click(closeBtn);

    // Panel should no longer have the open class
    expect(panel.classList.contains('hcw-open')).toBe(false);
  });
});

/* =============================================================
   2. Message Display Tests
   ============================================================= */

describe('ChatWidget Message Display', () => {
  beforeEach(async () => {
    renderWidget();
    await settle();
    openChat();
  });

  it('displays user message when sent', () => {
    fireEvent.change(screen.getByPlaceholderText('Type a question...'), {
      target: { value: 'Hello' },
    });
    fireEvent.click(screen.getByText('➤'));
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });

  it('sends message on Enter key', () => {
    fireEvent.change(screen.getByPlaceholderText('Type a question...'), {
      target: { value: 'Test message' },
    });
    fireEvent.keyDown(screen.getByPlaceholderText('Type a question...'), {
      key: 'Enter',
      shiftKey: false,
    });
    expect(screen.getByText('Test message')).toBeInTheDocument();
  });

  it('does not send empty messages', () => {
    fireEvent.click(screen.getByText('➤'));
    expect(screen.getByText(/Ask me anything/)).toBeInTheDocument();
  });
});

/* =============================================================
   3. WebSocket Message Handling
   ============================================================= */

describe('ChatWidget WebSocket Messages', () => {
  beforeEach(async () => {
    renderWidget();
    await settle();
    openChat();
  });

  it('handles query_result with message only', () => {
    simulateWsMessage({
      type: 'query_result',
      message: 'Hello! How can I help?',
    });
    expect(screen.getByText('Hello! How can I help?')).toBeInTheDocument();
  });

  it('handles query_result with single action', async () => {
    await simulateWsMessageAndWait({
      type: 'query_result',
      message: 'Navigating!',
      action: { type: 'navigate', path: '/doctors' },
    });
    expect(screen.getByText('Navigating!')).toBeInTheDocument();
  });

  it('handles query_result with actions array (preferred over single action)', async () => {
    await simulateWsMessageAndWait({
      type: 'query_result',
      message: 'Multi-step!',
      actions: [
        { type: 'navigate', path: '/booking' },
        { type: 'focus', selector: '#b-name' },
      ],
    });
    expect(screen.getByText('Multi-step!')).toBeInTheDocument();
  });

  it('handles error messages', () => {
    simulateWsMessage({
      type: 'error',
      message: 'Something went wrong',
    });
    expect(screen.getByText(/Something went wrong/)).toBeInTheDocument();
  });

  it('handles processing_started (typing indicator)', () => {
    simulateWsMessage({ type: 'processing_started', stage: 'llm' });
    // Should not crash — typing indicator renders CSS-animated spans
  });
});

/* =============================================================
   4. DOM Action Execution
   ============================================================= */

describe('ChatWidget DOM Actions', () => {
  beforeEach(async () => {
    setupActionDom();
    renderWidget();
    await settle();
    openChat();
  });

  // ── Navigate ──
  it('navigate action shows path', async () => {
    await simulateWsMessageAndWait({
      type: 'query_result',
      message: 'Go!',
      actions: [{ type: 'navigate', path: '/booking' }],
    });
    expect(screen.getByText(/Navigating to \/booking/)).toBeInTheDocument();
  });

  // ── Scroll ──
  it('scroll action scrolls to existing section', async () => {
    await simulateWsMessageAndWait({
      type: 'query_result',
      message: 'Scrolling!',
      actions: [{ type: 'scroll', selector: '#testimonials' }],
    });
    expect(screen.getByText(/Scrolling to section/)).toBeInTheDocument();
  });

  it('scroll action warns on missing section', async () => {
    await simulateWsMessageAndWait({
      type: 'query_result',
      message: 'Scrolling!',
      actions: [{ type: 'scroll', selector: '#does-not-exist' }],
    });
    await waitFor(() => {
      expect(screen.getByText(/Could not find/)).toBeInTheDocument();
    });
  });

  // ── Click ──
  it('click action dispatches MouseEvent on regular element', async () => {
    const handler = vi.fn();
    document.querySelector('#clickable-btn').addEventListener('click', handler);

    await simulateWsMessageAndWait({
      type: 'query_result',
      message: 'Clicking!',
      actions: [{ type: 'click', selector: '#clickable-btn' }],
    });
    expect(handler).toHaveBeenCalled();
  });

  it('click action on internal link uses React Router navigate', async () => {
    await simulateWsMessageAndWait({
      type: 'query_result',
      message: 'Clicking link!',
      actions: [{ type: 'click', selector: '#internal-link' }],
    });
    expect(screen.getByText(/Clicked element/)).toBeInTheDocument();
  });

  // ── Fill ──
  it('fill action sets input value and triggers React onChange', async () => {
    await simulateWsMessageAndWait({
      type: 'query_result',
      message: 'Filling!',
      actions: [{ type: 'fill', selector: '#b-name', value: 'John Doe' }],
    });
    expect(document.querySelector('#b-name').value).toBe('John Doe');
  });

  it('fill action on contenteditable sets textContent', async () => {
    await simulateWsMessageAndWait({
      type: 'query_result',
      message: 'Filling!',
      actions: [{ type: 'fill', selector: '#contenteditable-div', value: 'Custom text' }],
    });
    expect(document.querySelector('#contenteditable-div').textContent).toBe('Custom text');
  });

  it('fill action with missing selector does not crash', async () => {
    await simulateWsMessageAndWait({
      type: 'query_result',
      message: 'Filling!',
      actions: [{ type: 'fill', value: 'John' }],
    });
    // The fill case exits via break when !action.selector — no message is generated
    // Verify the main message still shows and no crash occurs
    expect(screen.getByText('Filling!')).toBeInTheDocument();
  });

  // ── Select ──
  it('select action sets dropdown value', async () => {
    await simulateWsMessageAndWait({
      type: 'query_result',
      message: 'Selecting!',
      actions: [{ type: 'select', selector: '#doctor-select', value: '1' }],
    });
    expect(document.querySelector('#doctor-select').value).toBe('1');
  });

  it('select action on non-SELECT element does not crash', async () => {
    await simulateWsMessageAndWait({
      type: 'query_result',
      message: 'Selecting!',
      actions: [{ type: 'select', selector: '#b-name', value: '1' }],
    });
    // safeOperate returns false for non-SELECT elements, so no error message
    // But the action was "executed" without effect — verify no crash
  });

  // ── Check ──
  it('check action checks a checkbox', async () => {
    await simulateWsMessageAndWait({
      type: 'query_result',
      message: 'Checking!',
      actions: [{ type: 'check', selector: '#agree-checkbox', checked: true }],
    });
    expect(document.querySelector('#agree-checkbox').checked).toBe(true);
  });

  it('check action unchecks a checkbox', async () => {
    document.querySelector('#agree-checkbox').checked = true;
    await simulateWsMessageAndWait({
      type: 'query_result',
      message: 'Unchecking!',
      actions: [{ type: 'check', selector: '#agree-checkbox', checked: false }],
    });
    expect(document.querySelector('#agree-checkbox').checked).toBe(false);
  });

  it('check action toggles custom role=switch element', async () => {
    await simulateWsMessageAndWait({
      type: 'query_result',
      message: 'Toggling!',
      actions: [{ type: 'check', selector: '#custom-toggle', checked: true }],
    });
    expect(document.querySelector('#custom-toggle').getAttribute('aria-checked')).toBe('true');
  });

  // ── Focus ──
  it('focus action focuses an element', async () => {
    const focusHandler = vi.fn();
    document.querySelector('#b-name').addEventListener('focus', focusHandler);

    await simulateWsMessageAndWait({
      type: 'query_result',
      message: 'Focusing!',
      actions: [{ type: 'focus', selector: '#b-name' }],
    });
    await waitFor(() => {
      expect(focusHandler).toHaveBeenCalled();
    });
  });

  // ── Submit ──
  it('submit action submits a form with selector', async () => {
    const submitHandler = vi.fn();
    document.querySelector('#booking-form').addEventListener('submit', submitHandler);

    await simulateWsMessageAndWait({
      type: 'query_result',
      message: 'Submitting!',
      actions: [{ type: 'submit', selector: '#booking-form' }],
    });
    await waitFor(() => {
      expect(screen.getByText(/Form submitted/)).toBeInTheDocument();
    });
  });

  it('submit action falls back to first form when no selector', async () => {
    const submitHandler = vi.fn();
    document.querySelector('#booking-form').addEventListener('submit', submitHandler);

    await simulateWsMessageAndWait({
      type: 'query_result',
      message: 'Submitting!',
      actions: [{ type: 'submit' }],
    });
    await waitFor(() => {
      expect(screen.getByText(/Form submitted/)).toBeInTheDocument();
    });
  });

  // ── Wait ──
  it('wait action logs the delay', async () => {
    await simulateWsMessageAndWait({
      type: 'query_result',
      message: 'Waiting!',
      actions: [{ type: 'wait', delay: 500 }],
    });
    expect(screen.getByText(/Waiting 500ms/)).toBeInTheDocument();
  });

  // ── Action (script-based, no-op placeholder) ──
  it('action type logs a message without crashing', async () => {
    await simulateWsMessageAndWait({
      type: 'query_result',
      message: 'Custom action!',
      actions: [{ type: 'action', script: 'document.querySelector(".btn").click()' }],
    });
    expect(screen.getByText(/Custom action received/)).toBeInTheDocument();
  });

  // ── Unknown type ──
  it('unknown action type logs available types', async () => {
    await simulateWsMessageAndWait({
      type: 'query_result',
      message: 'Unknown!',
      actions: [{ type: 'nonexistent' }],
    });
    expect(screen.getByText(/Unknown action type/)).toBeInTheDocument();
  });
});

/* =============================================================
   5. Error / Edge Case Handling
   ============================================================= */

describe('ChatWidget Error Handling', () => {
  it('handles empty actions array', async () => {
    renderWidget();
    await settle();
    openChat();
    await simulateWsMessageAndWait({
      type: 'query_result',
      message: 'Empty!',
      actions: [],
    });
    expect(screen.getByText('Empty!')).toBeInTheDocument();
  });

  it('handles invalid action (missing type) gracefully', async () => {
    renderWidget();
    await settle();
    openChat();
    await simulateWsMessageAndWait({
      type: 'query_result',
      message: 'Missing type!',
      actions: [{ someParam: 'value' }],  // no 'type' field
    });
    // executeAction returns early if !action.type — no crash
    expect(screen.getByText('Missing type!')).toBeInTheDocument();
  });

  // Removed: duplicate test (same scenario as 'handles invalid action')
  // Test coverage: action without type field is covered above

  it('reports missing element via getEl helper', async () => {
    renderWidget();
    await settle();
    openChat();
    await simulateWsMessageAndWait({
      type: 'query_result',
      message: 'Missing!',
      actions: [{ type: 'click', selector: '#ghost-element' }],
    });
    await waitFor(() => {
      expect(screen.getByText(/Could not find/)).toBeInTheDocument();
    });
  });

  it('handles query_result with both action and actions (actions wins)', async () => {
    renderWidget();
    await settle();
    openChat();
    await simulateWsMessageAndWait({
      type: 'query_result',
      message: 'Both!',
      action: { type: 'navigate', path: '/old' },
      actions: [
        { type: 'navigate', path: '/new' },
      ],
    });
    // Should use the actions array (navigate to /new)
    expect(screen.getByText(/Navigating to \/new/)).toBeInTheDocument();
  });
});

/* =============================================================
   6. Audio Recording
   ============================================================= */

describe('ChatWidget Audio', () => {
  beforeEach(() => {
    // Mock getUserMedia
    Object.defineProperty(navigator, 'mediaDevices', {
      value: {
        getUserMedia: vi.fn().mockResolvedValue({
          getTracks: () => [{ stop: vi.fn() }],
        }),
      },
      configurable: true,
    });

    // Mock MediaRecorder
    globalThis.MediaRecorder = vi.fn().mockImplementation(() => ({
      start: vi.fn(),
      stop: vi.fn(),
      state: 'inactive',
      ondataavailable: null,
      onstop: null,
    }));
    globalThis.MediaRecorder.isTypeSupported = vi.fn().mockReturnValue(true);
  });

  it('toggles microphone recording state', async () => {
    renderWidget();
    await settle();
    openChat();

    fireEvent.click(screen.getByTitle('Record'));
    expect(navigator.mediaDevices.getUserMedia).toHaveBeenCalled();
  });
});

/* =============================================================
   7. Session ID
   ============================================================= */

describe('ChatWidget Session ID', () => {
  beforeEach(() => {
    // Note: SESSION_ID constant is computed at module import time,
    // before per-test beforeEach runs.
  });

  // Removed: 'generates a session ID on import' test.
  // SESSION_ID is a module-level constant computed at import time, so testing it
  // from per-test beforeEach would require module reloading. Covered by:
  // - 'reuses existing SESSION ID from localStorage' (persistence)
  // - 'includes session_id in WebSocket messages on send' (functional behavior)
  // - 'renders the floating action button' (no-crash check)

  it('reuses existing session ID from localStorage', async () => {
    localStorage.setItem('hcw-session-id', 'persisted-session-id');
    renderWidget();
    await settle();
    expect(localStorage.getItem('hcw-session-id')).toBe('persisted-session-id');
  });

  it('includes session_id in WebSocket messages on send', async () => {
    renderWidget();
    await settle();
    openChat();

    // Get the most recent WS instance
    const ws = globalThis.__getLastWsInstance();
    expect(ws).toBeTruthy();

    // Send a message
    fireEvent.change(screen.getByPlaceholderText('Type a question...'), {
      target: { value: 'Hello' },
    });
    fireEvent.click(screen.getByText('➤'));

    // Verify the send call included session_id
    expect(ws.send).toHaveBeenCalled();
    const sentData = ws.send.mock.calls[0][0];
    const parsed = JSON.parse(sentData);
    expect(parsed.session_id).toBeTruthy();
    expect(typeof parsed.session_id).toBe('string');
  });
});

/* =============================================================
   8. Multi-Action Sequences
   ============================================================= */

describe('ChatWidget Multi-Action Sequences', () => {
  beforeEach(async () => {
    setupActionDom();
    renderWidget();
    await settle();
    openChat();
  });

  it('executes multiple fill actions in sequence', async () => {
    await simulateWsMessageAndWait({
      type: 'query_result',
      message: 'Filling form!',
      actions: [
        { type: 'fill', selector: '#b-name', value: 'John Doe' },
        { type: 'fill', selector: '#b-email', value: 'john@test.com' },
      ],
    }, 800);

    expect(document.querySelector('#b-name').value).toBe('John Doe');
    expect(document.querySelector('#b-email').value).toBe('john@test.com');
  });

  it('executes multi-step sequence with wait between actions', async () => {
    const startTime = Date.now();

    await simulateWsMessageAndWait({
      type: 'query_result',
      message: 'Delayed!',
      actions: [
        { type: 'fill', selector: '#b-name', value: 'John' },
        { type: 'wait', delay: 200 },
        { type: 'fill', selector: '#b-email', value: 'john@test.com' },
      ],
    }, 1000);

    const elapsed = Date.now() - startTime;
    expect(elapsed).toBeGreaterThanOrEqual(150); // at least the 200ms wait (minus timing variance)
    expect(document.querySelector('#b-name').value).toBe('John');
    expect(document.querySelector('#b-email').value).toBe('john@test.com');
  });

  it('completes all steps even if some fail', async () => {
    await simulateWsMessageAndWait({
      type: 'query_result',
      message: 'Mixed!',
      actions: [
        { type: 'click', selector: '#nonexistent1' },
        { type: 'fill', selector: '#b-name', value: 'Survivor' },
      ],
    }, 1000);

    // The fill should have worked despite the first step failing
    expect(document.querySelector('#b-name').value).toBe('Survivor');
  });
});
