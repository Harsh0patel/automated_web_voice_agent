import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import AudioPlayer from '../components/AudioPlayer.jsx';

describe('AudioPlayer', () => {
  it('does not render when not visible', () => {
    const { container } = render(
      <AudioPlayer visible={false} blob={null} onClose={vi.fn()} />
    );
    expect(container.querySelector('.audio-player-bar')).toBeNull();
  });

  it('does not render when visible but no blob', () => {
    const { container } = render(
      <AudioPlayer visible={true} blob={null} onClose={vi.fn()} />
    );
    expect(container.querySelector('.audio-player-bar')).toBeNull();
  });

  it('renders when visible with blob', () => {
    const blob = new Blob(['test'], { type: 'audio/webm' });
    const { container } = render(
      <AudioPlayer visible={true} blob={blob} onClose={vi.fn()} />
    );
    expect(container.querySelector('.audio-player-bar')).toBeInTheDocument();
    expect(container.querySelector('.play-btn')).toBeInTheDocument();
    expect(container.querySelector('.close-btn')).toBeInTheDocument();
  });

  it('renders waveform bars', () => {
    const blob = new Blob(['test'], { type: 'audio/webm' });
    const { container } = render(
      <AudioPlayer visible={true} blob={blob} onClose={vi.fn()} />
    );
    const bars = container.querySelector('.waveform');
    expect(bars).toBeInTheDocument();
    expect(bars.children.length).toBe(40);
  });

  it('calls onClose when close button clicked', () => {
    const onClose = vi.fn();
    const blob = new Blob(['test'], { type: 'audio/webm' });
    const { container } = render(
      <AudioPlayer visible={true} blob={blob} onClose={onClose} />
    );
    fireEvent.click(container.querySelector('.close-btn'));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('has play/pause button', () => {
    const blob = new Blob(['test'], { type: 'audio/webm' });
    const { container } = render(
      <AudioPlayer visible={true} blob={blob} onClose={vi.fn()} />
    );
    const playBtn = container.querySelector('.play-btn');
    expect(playBtn).toBeInTheDocument();
    // Autoplay triggers playing state immediately
    expect(playBtn.textContent).toBe('⏸️');
  });
});
