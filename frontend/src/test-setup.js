import '@testing-library/jest-dom';

// Mock HTMLMediaElement for jsdom (Audio/Video elements)
if (typeof HTMLMediaElement !== 'undefined') {
  HTMLMediaElement.prototype.play = () => Promise.resolve();
  HTMLMediaElement.prototype.pause = () => {};
  HTMLMediaElement.prototype.load = () => {};
  HTMLMediaElement.prototype.addTextTrack = () => {};
}
