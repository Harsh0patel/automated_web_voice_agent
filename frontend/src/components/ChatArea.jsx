import React from 'react';

export default function ChatArea({ messages, messagesEndRef }) {
  return (
    <div className="chat-area">
      {messages.length === 0 ? (
        <div className="welcome">
          <div className="welcome-icon">🎙️</div>
          <h2>Welcome to AI Voice Assistant</h2>
          <p>
            Start by adding a website to the knowledge base using the sidebar.
            Then ask questions — I'll search the scraped content and respond with
            text and voice. You can also use your microphone!
          </p>
        </div>
      ) : (
        messages.map((msg, i) => <MessageBubble key={i} msg={msg} />)
      )}
      <div ref={messagesEndRef} />
    </div>
  );
}

function MessageBubble({ msg }) {
  return (
    <div className={`msg ${msg.role}`}>
      <div className="msg-text">{msg.text}</div>
      {msg.sources?.length > 0 && (
        <div className="msg-sources">
          {msg.sources.map((s, i) => (
            <span className="source-tag" key={i} title={s.url}>
              {s.page || s.url.replace(/^https?:\/\//, '')}
            </span>
          ))}
        </div>
      )}
      <div className="msg-time">{msg.time}</div>
    </div>
  );
}
