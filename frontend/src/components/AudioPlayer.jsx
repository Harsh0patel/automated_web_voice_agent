import React, { useRef, useState, useEffect } from 'react';

export default function AudioPlayer({ visible, blob, onClose }) {
  const [playing, setPlaying] = useState(false);
  const [time, setTime] = useState('0:00');
  const [progress, setProgress] = useState(0);
  const audioRef = useRef(null);
  const urlRef = useRef(null);

  // Cleanup previous URL
  useEffect(() => {
    return () => {
      if (urlRef.current) URL.revokeObjectURL(urlRef.current);
    };
  }, []);

  useEffect(() => {
    if (!visible || !blob) return;

    // Revoke old URL
    if (urlRef.current) URL.revokeObjectURL(urlRef.current);

    const objectUrl = URL.createObjectURL(blob);
    urlRef.current = objectUrl;
    const audio = new Audio(objectUrl);
    audioRef.current = audio;

    audio.onloadedmetadata = () => {
      const mins = Math.floor(audio.duration / 60);
      const secs = Math.floor(audio.duration % 60);
      setTime(`${mins}:${secs.toString().padStart(2, '0')}`);
    };

    audio.ontimeupdate = () => {
      setProgress(audio.currentTime / (audio.duration || 1));
    };

    audio.onended = () => {
      setPlaying(false);
      setProgress(0);
    };

    audio.play().catch(() => {
      // Browser autoplay blocked — user can click play manually
    });
    setPlaying(true);

    return () => {
      audio.pause();
    };
  }, [visible, blob]);

  function togglePlay() {
    const audioElem = audioRef.current;
    if (!audioElem) return;
    if (playing) {
      audioElem.pause();
    } else {
      audioElem.play();
    }
    setPlaying(!playing);
  }

  function handleClose() {
    audioRef.current?.pause();
    if (urlRef.current) {
      URL.revokeObjectURL(urlRef.current);
      urlRef.current = null;
    }
    setPlaying(false);
    setProgress(0);
    onClose();
  }

  if (!visible || !blob) return null;

  return (
    <div className="audio-player-bar">
      <button className="play-btn" onClick={togglePlay}>
        {playing ? '⏸️' : '▶️'}
      </button>
      <div className="waveform">
        {Array.from({ length: 40 }, (_, i) => (
          <span
            key={i}
            className={i / 40 < progress ? 'active' : ''}
            style={{ height: `${Math.sin(i * 0.3) * 10 + 12}px` }}
          />
        ))}
      </div>
      <span className="audio-time">{time}</span>
      <button className="close-btn" onClick={handleClose}>✕</button>
    </div>
  );
}
