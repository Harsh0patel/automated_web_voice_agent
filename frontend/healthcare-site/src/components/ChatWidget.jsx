import React, { useState, useRef, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

// ── Generate or retrieve a persistent session ID ──
function getSessionId() {
  const key = 'hcw-session-id';
  let sid = localStorage.getItem(key);
  if (!sid) {
    sid = crypto.randomUUID ? crypto.randomUUID() : 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
      const r = Math.random() * 16 | 0;
      return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
    localStorage.setItem(key, sid);
  }
  return sid;
}

const SESSION_ID = getSessionId();

export default function ChatWidget() {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [connected, setConnected] = useState(false);
  const [ttsBlob, setTtsBlob] = useState(null);
  const [playing, setPlaying] = useState(false);
  const wsRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const audioRef = useRef(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const ttsUrlRef = useRef(null);

  // ── WebSocket connection ──
  useEffect(() => {
    function connect() {
      const ws = new WebSocket(`ws://${location.hostname}:8000/ws`);
      wsRef.current = ws;

      ws.onopen = () => setConnected(true);
      ws.onclose = () => {
        setConnected(false);
        setTimeout(connect, 3000);
      };
      ws.onerror = () => setConnected(false);

      ws.onmessage = (event) => {
        if (event.data instanceof Blob) {
          // TTS audio received
          if (ttsUrlRef.current) URL.revokeObjectURL(ttsUrlRef.current);
          const url = URL.createObjectURL(event.data);
          ttsUrlRef.current = url;
          setTtsBlob(event.data);
          const audio = new Audio(url);
          audioRef.current = audio;
          audio.play().catch(() => {});
          setPlaying(true);
          audio.onended = () => setPlaying(false);
          return;
        }
        try {
          const data = JSON.parse(event.data);
          handleWsMessage(data);
        } catch {}
      };
    }
    connect();
    return () => {
      wsRef.current?.close();
      if (ttsUrlRef.current) URL.revokeObjectURL(ttsUrlRef.current);
    };
  }, []);

  function send(data) {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      if (typeof data === 'object') {
        // Always include session_id and current page path
        data.session_id = SESSION_ID;
        data.current_path = window.location.pathname;
      }
      wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data));
    }
  }

  function addMessage(role, text) {
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    setMessages(prev => [...prev, { role, text, time }]);
  }

  function handleWsMessage(data) {
    switch (data.type) {
      case 'processing_started':
        setIsTyping(true);
        break;
      case 'transcription_complete':
        addMessage('user', `🎤 \"${data.transcript}\"`);
        break;
      case 'db_results_found':
        break;
      case 'query_result':
        setIsTyping(false);
        if (data.message) addMessage('assistant', data.message);
        // Execute action(s): prefer 'actions' array over single 'action'
        if (data.actions && data.actions.length > 0) {
          executeActions(data.actions);
        } else if (data.action) {
          executeActions([data.action]);
        }
        if (data.tts_error) addMessage('system', `⚠️ Voice: ${data.tts_error}`);
        break;
      case 'error':
        setIsTyping(false);
        addMessage('system', `❌ ${data.message}`);
        break;
    }
  }

  // ── Helper: safely get a DOM element and warn if missing ──
  function getEl(selector, label) {
    if (!selector) {
      addMessage('system', `⚠️ Missing selector for ${label || 'action'}`);
      return null;
    }
    const el = document.querySelector(selector);
    if (!el) {
      addMessage('system', `⚠️ Could not find ${label || selector}`);
    }
    return el;
  }

  // ── Helper: try an operation and report success/failure ──
  function safeOperate(selector, actionLabel, actionFn) {
    const el = getEl(selector, actionLabel);
    if (!el) return;
    try {
      const result = actionFn(el);
      if (result !== false) {
        addMessage('system', `✅ ${actionLabel}`);
      }
    } catch (err) {
      addMessage('system', `❌ ${actionLabel} failed: ${err.message}`);
    }
  }

  // ── Execute LLM actions (navigate, scroll, submit, click, fill, select, check, focus, wait) ──
  function executeAction(action) {
    if (!action || !action.type) return;

    switch (action.type) {
      case 'navigate':
        if (action.path) {
          navigate(action.path);
          addMessage('system', `📍 Navigating to ${action.path}...`);
        }
        break;

      case 'scroll':
        if (action.selector) {
          safeOperate(action.selector, '👆 Scrolling to section', (el) => {
            // Account for fixed navbar height (76px)
            const y = el.getBoundingClientRect().top + window.scrollY - 80;
            window.scrollTo({ top: y, behavior: 'smooth' });
          });
        }
        break;

      case 'submit': {
        // Try the provided selector, or fall back to any form on the page
        const formEl = action.selector
          ? getEl(action.selector, 'form')
          : document.querySelector('form');
        if (!formEl) {
          addMessage('system', '⚠️ Could not find form');
          break;
        }
        try {
          const submitBtn = formEl.querySelector('button[type="submit"], input[type="submit"]');
          if (submitBtn) {
            submitBtn.click();
          } else {
            formEl.dispatchEvent(new Event('submit', { cancelable: true }));
          }
          addMessage('system', '✅ Form submitted');
        } catch (err) {
          addMessage('system', `❌ Submit failed: ${err.message}`);
        }
        break;
      }

      case 'click':
        safeOperate(action.selector, 'Clicked element', (el) => {
          // React Router <Link> doesn't respond to .click(); dispatch a MouseEvent
          if (el.tagName === 'A') {
            const href = el.getAttribute('href');
            if (href) {
              if (href.startsWith('/')) {
                // Internal route — use React Router navigation
                navigate(href);
              } else {
                // External link — let the browser handle it via MouseEvent
                el.dispatchEvent(new MouseEvent('click', {
                  bubbles: true, cancelable: true, button: 0,
                }));
              }
              return true;
            }
          }
          el.dispatchEvent(new MouseEvent('click', {
            bubbles: true, cancelable: true, button: 0,
          }));
        });
        break;

      case 'fill': {
        const val = action.value;
        if (val === undefined || !action.selector) break;
        safeOperate(action.selector, `✏️ Filled with "${val}"`, (el) => {
          const tag = el.tagName;
          if (tag === 'INPUT' || tag === 'TEXTAREA') {
            // Use native value setter to bypass React's controlled input interception
            const setter =
              Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set ??
              Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value')?.set;
            if (setter) {
              setter.call(el, val);
            } else {
              el.value = val;
            }
            // Dispatch both events that React listens to
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
          } else {
            // contenteditable or other element
            el.textContent = val;
            el.dispatchEvent(new Event('input', { bubbles: true }));
          }
        });
        break;
      }

      case 'select':
        safeOperate(action.selector, `📋 Selected "${action.value}"`, (el) => {
          if (el.tagName !== 'SELECT') return false;
          if (el.multiple) {
            // For multi-select, clear all and select the specified value
            Array.from(el.options).forEach(opt => opt.selected = false);
            const target = Array.from(el.options).find(o => o.value === action.value);
            if (target) target.selected = true;
          } else {
            el.value = action.value;
          }
          el.dispatchEvent(new Event('change', { bubbles: true }));
        });
        break;

      case 'check':
        safeOperate(action.selector, `☑️ ${action.checked ? 'Checked' : 'Unchecked'}`, (el) => {
          if (el.type === 'checkbox') {
            el.checked = Boolean(action.checked);
            el.dispatchEvent(new Event('change', { bubbles: true }));
          } else if (el.getAttribute('role') === 'switch' || el.getAttribute('aria-checked') !== null) {
            // Handle custom toggle/switch components
            el.setAttribute('aria-checked', String(Boolean(action.checked)));
            el.dispatchEvent(new Event('click', { bubbles: true }));
          }
        });
        break;

      case 'focus':
        safeOperate(action.selector, '🎯 Focused', (el) => {
          el.focus({ preventScroll: false });
        });
        break;

      case 'wait':
        // Wait action is async but executeAction is sync.
        // The backend should handle timing by sending actions sequentially.
        addMessage('system', `⏳ Waiting ${action.delay || action.ms || 1000}ms...`);
        break;

      case 'action':
        // The typed actions above (click, fill, select, check, focus) cover
        // every DOM operation the LLM could reasonably need. The 'action'
        // type is kept for forward compatibility — the backend should convert
        // generic action scripts into typed actions before sending.
        if (action.script) {
          addMessage('system', `⚡ Custom action received. Please use click/fill/select actions for direct DOM interaction.`);
        }
        break;

      default:
        addMessage('system', `🤔 Unknown action type: ${action.type}. Available: navigate, scroll, submit, click, fill, select, check, focus`);
    }
  }

  // ── Execute a sequence of actions with delays between them ──
  async function executeActions(actions) {
    if (!actions || actions.length === 0) return;
    addMessage('system', `⏳ Executing ${actions.length} step(s)...`);
    for (let i = 0; i < actions.length; i++) {
      const act = actions[i];
      // Handle wait/delay actions specially
      if (act.type === 'wait') {
        const ms = act.delay || act.ms || 1000;
        addMessage('system', `⏳ Waiting ${ms}ms...`);
        await new Promise(resolve => setTimeout(resolve, ms));
        continue;
      }
      // Execute the action synchronously
      executeAction(act);
      // After navigation or any DOM change, let React re-render before the next step
      // Skip extra wait for 'wait' actions since they handle their own timing
      if (act.type !== 'wait') {
        await new Promise(resolve => setTimeout(resolve, 250));
      }
    }
    addMessage('system', '✅ All steps completed');
  }

  // ── Send text ──
  function handleSend() {
    if (!input.trim()) return;
    addMessage('user', input);
    send({ type: 'chat', content: input });
    setInput('');
    setIsTyping(true);
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  // ── Voice recording ──
  async function toggleMic() {
    if (isRecording) {
      mediaRecorderRef.current?.stop();
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { sampleRate: 16000, channelCount: 1, echoCancellation: true, noiseSuppression: true },
      });
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm';
      const recorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];
      setIsRecording(true);

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        setIsRecording(false);
        stream.getTracks().forEach(t => t.stop());
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        if (blob.size > 1000) sendAudio(blob);
        else addMessage('system', '⚠️ Recording too short');
      };

      recorder.start();
    } catch (err) {
      addMessage('system', `❌ Mic: ${err.message}`);
    }
  }

  function sendAudio(blob) {
    addMessage('system', `🎤 Audio (${(blob.size / 1024).toFixed(1)} KB)`);
    setIsTyping(true);
    const reader = new FileReader();
    reader.onload = () => {
      const b64 = reader.result.split(',')[1];
      send({ type: 'audio_transcribe', format: 'webm', data: b64 });
    };
    reader.readAsDataURL(blob);
  }

  // ── Auto-scroll ──
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  // ── Focus input when panel opens ──
  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 300);
  }, [open]);

  // ── Toggle audio ──
  function toggleAudio() {
    if (!audioRef.current) return;
    if (playing) {
      audioRef.current.pause();
      setPlaying(false);
    } else {
      audioRef.current.play().catch(() => {});
      setPlaying(true);
      audioRef.current.onended = () => setPlaying(false);
    }
  }

  return (
    <>
      {/* ── Chat panel ── */}
      <div className={`hcw-panel ${open ? 'hcw-open' : ''}`}>
        <div className="hcw-header">
          <span className="hcw-title">🤖 AI Assistant</span>
          <span className={`hcw-dot ${connected ? 'connected' : ''}`} />
          <button className="hcw-close" onClick={() => setOpen(false)}>✕</button>
        </div>

        <div className="hcw-messages">
          {messages.length === 0 && (
            <div className="hcw-welcome">
              <p>Ask me anything about our services, doctors, or book an appointment!</p>
            </div>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`hcw-msg hcw-${msg.role}`}>
              <div className="hcw-msg-text">{msg.text}</div>
              <div className="hcw-msg-time">{msg.time}</div>
            </div>
          ))}
          {isTyping && (
            <div className="hcw-typing">
              <span /><span /><span />
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* ── Audio player mini bar ── */}
        {ttsBlob && (
          <div className="hcw-audio-bar">
            <button className="hcw-play-btn" onClick={toggleAudio}>
              {playing ? '⏸' : '▶️'}
            </button>
            <div className="hcw-audio-wave">
              {Array.from({ length: 20 }, (_, i) => (
                <span key={i} style={{ height: `${Math.sin(i * 0.5) * 8 + 10}px` }} />
              ))}
            </div>
          </div>
        )}

        <div className="hcw-input">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Type a question..."
          />
          <button
            className={`hcw-mic ${isRecording ? 'recording' : ''}`}
            onClick={toggleMic}
            title={isRecording ? 'Stop' : 'Record'}
          >
            🎤
          </button>
          <button className="hcw-send" onClick={handleSend}>➤</button>
        </div>
      </div>

      {/* ── FAB button ── */}
      <button className="hcw-fab" onClick={() => setOpen(p => !p)} title="AI Assistant">
        {open ? '✕' : '💬'}
      </button>
    </>
  );
}
