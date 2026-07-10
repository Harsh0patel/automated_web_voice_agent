import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import ChatArea from '../components/ChatArea.jsx';

describe('ChatArea', () => {
  it('shows welcome message when no messages', () => {
    render(<ChatArea messages={[]} messagesEndRef={null} />);
    expect(screen.getByText('Welcome to AI Voice Assistant')).toBeInTheDocument();
  });

  it('renders user messages', () => {
    const messages = [
      { role: 'user', text: 'Hello!', time: '12:00', sources: [] },
    ];
    render(<ChatArea messages={messages} messagesEndRef={null} />);
    expect(screen.getByText('Hello!')).toBeInTheDocument();
  });

  it('renders assistant messages with time', () => {
    const messages = [
      { role: 'assistant', text: 'Hi there!', time: '12:01', sources: [] },
    ];
    render(<ChatArea messages={messages} messagesEndRef={null} />);
    expect(screen.getByText('Hi there!')).toBeInTheDocument();
    expect(screen.getByText('12:01')).toBeInTheDocument();
  });

  it('renders system messages', () => {
    const messages = [
      { role: 'system', text: '⚠️ TTS error', time: '12:02', sources: [] },
    ];
    render(<ChatArea messages={messages} messagesEndRef={null} />);
    expect(screen.getByText('⚠️ TTS error')).toBeInTheDocument();
  });

  it('renders source tags for assistant messages', () => {
    const messages = [
      {
        role: 'assistant',
        text: 'Found results',
        time: '12:03',
        sources: [{ title: 'Medical Page', url: 'https://example.com' }],
      },
    ];
    render(<ChatArea messages={messages} messagesEndRef={null} />);
    expect(screen.getByText('Medical Page')).toBeInTheDocument();
  });
});
