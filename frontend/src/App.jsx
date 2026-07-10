import React, { useState, useCallback, useRef, useEffect } from 'react';
import useWebSocket from './hooks/useWebSocket.js';
import Header from './components/Header.jsx';
import Sidebar from './components/Sidebar.jsx';
import ChatArea from './components/ChatArea.jsx';
import InputBar from './components/InputBar.jsx';
import AudioPlayer from './components/AudioPlayer.jsx';
import TypingIndicator from './components/TypingIndicator.jsx';

const API_BASE = `http://${location.hostname}:${window.location.port || '8000'}`;
const STORAGE_THEME = 'ai-voice-theme';

export default function App() {
  const [messages, setMessages] = useState([]);
  const [status, setStatus] = useState({ state: 'connecting', label: 'Connecting...' });
  const [isTyping, setIsTyping] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isDark, setIsDark] = useState(() => localStorage.getItem(STORAGE_THEME) === 'dark');
  const [pages, setPages] = useState([]);
  const [ttsBlob, setTtsBlob] = useState(null);
  const [showPlayer, setShowPlayer] = useState(false);
  const [dbBanner, setDbBanner] = useState(null);
  const [scrapeStatus, setScrapeStatus] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const messagesEndRef = useRef(null);

  // --- Theme ---
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
    localStorage.setItem(STORAGE_THEME, isDark ? 'dark' : 'light');
  }, [isDark]);

  // --- WebSocket handler ---
  const handleWsMessage = useCallback((data) => {
    if (data.type === '__audio__') {
      setTtsBlob(data.blob);
      setShowPlayer(true);
      return;
    }

    switch (data.type) {
      case 'connection_established':
        setStatus({ state: 'connected', label: `Connected v${data.version}` });
        break;

      case 'processing_started':
        setStatus({ state: 'processing', label: data.stage || 'Processing...' });
        setIsTyping(true);
        break;

      case 'transcription_complete':
        addMessage('user', `🎤 "${data.transcript}"`);
        break;

      case 'db_results_found':
        setDbBanner(`📚 ${data.count} relevant page(s) found`);
        break;

      case 'db_lookup_skipped':
        setDbBanner(null);
        break;

      case 'query_result':
        setStatus({ state: 'connected', label: 'Connected' });
        setIsTyping(false);
        if (data.message) addMessage('assistant', data.message, data.sources);
        if (data.tts_error) addMessage('system', `⚠️ TTS error: ${data.tts_error}`);
        break;

      case 'error':
        setStatus({ state: 'connected', label: 'Connected' });
        setIsTyping(false);
        addMessage('system', `❌ ${data.message}`);
        break;
    }
  }, [addMessage]);

  const handleWsStatus = useCallback((state, label) => {
    setStatus({ state, label });
  }, []);

  const { send, reconnect } = useWebSocket({
    onMessage: handleWsMessage,
    onStatusChange: handleWsStatus,
  });

  // --- Messages ---
  const addMessage = useCallback((role, text, sources) => {
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    setMessages(prev => [...prev, { role, text, time, sources: sources || [] }]);
  }, []);

  // --- Send text ---
  function sendQuery(text) {
    if (!text.trim()) return;
    addMessage('user', text);
    setStatus({ state: 'processing', label: 'Processing...' });
    const sent = send({ type: 'chat', content: text });
    if (!sent) {
      addMessage('system', '❌ Not connected. Reconnecting...');
      reconnect();
    }
  }

  // --- Voice recording ---
  async function toggleMic() {
    if (isRecording) {
      stopRecording();
    } else {
      await startRecording();
    }
  }

  async function startRecording() {
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
      addMessage('system', `❌ Microphone: ${err.message}`);
    }
  }

  function stopRecording() {
    if (mediaRecorderRef.current?.state !== 'inactive') {
      mediaRecorderRef.current?.stop();
    }
  }

  function sendAudio(blob) {
    addMessage('system', `🎤 Audio (${(blob.size / 1024).toFixed(1)} KB)`);
    setStatus({ state: 'processing', label: 'Audio...' });
    const reader = new FileReader();
    reader.onload = () => {
      const b64 = reader.result.split(',')[1];
      send({ type: 'audio_transcribe', format: 'webm', data: b64 });
    };
    reader.readAsDataURL(blob);
  }

  // --- Scrape URL ---
  const scrapeUrl = useCallback(async (url) => {
    if (!url.trim()) return;
    setScrapeStatus('⏳ Scraping...');
    try {
      const res = await fetch(`${API_BASE}/scrape?url=${encodeURIComponent(url)}`, { method: 'POST' });
      const data = await res.json();
      if (data.error) {
        setScrapeStatus(`❌ ${data.error}`);
      } else {
        setScrapeStatus(`✅ Scraped: ${data.title || data.url}`);
        addMessage('system', `📄 Added "${data.title || data.url}" to knowledge base`);
        loadPages();
      }
    } catch (err) {
      setScrapeStatus(`❌ ${err.message}`);
    }
  }, [addMessage]);

  // --- Pages ---
  const loadPages = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/pages`);
      const data = await res.json();
      setPages(data.pages || []);
    } catch {
      // DB might not be running
    }
  }, []);

  const clearPages = useCallback(async () => {
    try {
      await fetch(`${API_BASE}/pages`, { method: 'DELETE' });
      addMessage('system', '🗑️ Knowledge base cleared');
      loadPages();
    } catch {}
  }, [addMessage, loadPages]);

  useEffect(() => { loadPages(); }, []);

  // --- Audio player ---
  function closePlayer() {
    setShowPlayer(false);
    setTtsBlob(null);
  }

  return (
    <div className="app">
      <Header
        status={status}
        isDark={isDark}
        onToggleTheme={() => setIsDark(p => !p)}
        onToggleSidebar={() => setSidebarOpen(p => !p)}
      />

      <div className="layout">
        <div className={`overlay ${sidebarOpen ? 'visible' : ''}`} onClick={() => setSidebarOpen(false)} />

        <Sidebar
          open={sidebarOpen}
          pages={pages}
          scrapeStatus={scrapeStatus}
          onScrape={scrapeUrl}
          onClearPages={clearPages}
          onCloseMobile={() => setSidebarOpen(false)}
        />

        <main className="main">
          {dbBanner && <div className="db-banner">{dbBanner}</div>}

          <ChatArea messages={messages} messagesEndRef={messagesEndRef} />

          <TypingIndicator visible={isTyping} />

          {isRecording && (
            <div className="voice-wave">
              <span /><span /><span /><span /><span />
            </div>
          )}

          <AudioPlayer
            visible={showPlayer}
            blob={ttsBlob}
            onClose={closePlayer}
          />

          <InputBar
            onSend={sendQuery}
            isRecording={isRecording}
            onToggleMic={toggleMic}
          />
        </main>
      </div>
    </div>
  );
}
