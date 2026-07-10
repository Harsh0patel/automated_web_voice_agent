import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import InputBar from '../components/InputBar.jsx';

describe('InputBar', () => {
  it('renders input and buttons', () => {
    render(<InputBar onSend={vi.fn()} isRecording={false} onToggleMic={vi.fn()} />);
    expect(screen.getByPlaceholderText('Ask a question...')).toBeInTheDocument();
    expect(screen.getByTitle('Send')).toBeInTheDocument();
    expect(screen.getByTitle('Record voice')).toBeInTheDocument();
  });

  it('calls onSend when send button clicked', () => {
    const onSend = vi.fn();
    render(<InputBar onSend={onSend} isRecording={false} onToggleMic={vi.fn()} />);
    const input = screen.getByPlaceholderText('Ask a question...');
    fireEvent.change(input, { target: { value: 'Hello' } });
    fireEvent.click(screen.getByTitle('Send'));
    expect(onSend).toHaveBeenCalledWith('Hello');
  });

  it('calls onSend on Enter key', () => {
    const onSend = vi.fn();
    render(<InputBar onSend={onSend} isRecording={false} onToggleMic={vi.fn()} />);
    const input = screen.getByPlaceholderText('Ask a question...');
    fireEvent.change(input, { target: { value: 'Test' } });
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: false });
    expect(onSend).toHaveBeenCalledWith('Test');
  });

  it('does not call onSend for empty input', () => {
    const onSend = vi.fn();
    render(<InputBar onSend={onSend} isRecording={false} onToggleMic={vi.fn()} />);
    fireEvent.click(screen.getByTitle('Send'));
    expect(onSend).not.toHaveBeenCalled();
  });

  it('does not call onSend on Shift+Enter', () => {
    const onSend = vi.fn();
    render(<InputBar onSend={onSend} isRecording={false} onToggleMic={vi.fn()} />);
    const input = screen.getByPlaceholderText('Ask a question...');
    fireEvent.change(input, { target: { value: 'Hello' } });
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: true });
    expect(onSend).not.toHaveBeenCalled();
  });

  it('calls onToggleMic when mic button clicked', () => {
    const onToggleMic = vi.fn();
    render(<InputBar onSend={vi.fn()} isRecording={false} onToggleMic={onToggleMic} />);
    fireEvent.click(screen.getByTitle('Record voice'));
    expect(onToggleMic).toHaveBeenCalledTimes(1);
  });

  it('shows recording state on mic button', () => {
    render(<InputBar onSend={vi.fn()} isRecording={true} onToggleMic={vi.fn()} />);
    const micBtn = screen.getByTitle('Stop recording');
    expect(micBtn.classList.contains('recording')).toBe(true);
  });

  it('clears input after sending', () => {
    const onSend = vi.fn();
    render(<InputBar onSend={onSend} isRecording={false} onToggleMic={vi.fn()} />);
    const input = screen.getByPlaceholderText('Ask a question...');
    fireEvent.change(input, { target: { value: 'Hello' } });
    fireEvent.click(screen.getByTitle('Send'));
    expect(input.value).toBe('');
  });
});
