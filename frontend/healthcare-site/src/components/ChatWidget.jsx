import React, { useState, useRef, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

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
        addMessage('user', `🎤 "${data.transcript}"`);
        break;
      case 'db_results_found':
        break;
      case 'query_result':
        setIsTyping(false);
        if (data.message) addMessage('assistant', data.message);
        // Execute action if the LLM provided one
        if (data.action) {
          executeAction(data.action);
        }
        if (data.tts_error) addMessage('system', `⚠️ Voice: ${data.tts_error}`);
        break;
      case 'error':
        setIsTyping(false);
        addMessage('system', `❌ ${data.message}`);
        break;
    }
  }

  // ── Execute LLM actions (navigate, scroll, etc.) ──
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
          const el = document.querySelector(action.selector);
          if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'start' });
            addMessage('system', `👆 Scrolling to ${action.selector}...`);
          }
        }
        break;
    }
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
