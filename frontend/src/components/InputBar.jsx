import React, { useState } from 'react';

export default function InputBar({ onSend, isRecording, onToggleMic }) {
  const [text, setText] = useState('');

  function handleSend() {
    if (!text.trim()) return;
    onSend(text);
    setText('');
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="input-bar">
      <input
        type="text"
        value={text}
        onChange={e => setText(e.target.value)}
        onKeyDown={handleKey}
        placeholder="Ask a question..."
      />
      <button
        className={`btn-mic ${isRecording ? 'recording' : ''}`}
        onClick={onToggleMic}
        title={isRecording ? 'Stop recording' : 'Record voice'}
      >
        🎤
      </button>
      <button className="btn-send" onClick={handleSend} title="Send">
        ➤
      </button>
    </div>
  );
}
