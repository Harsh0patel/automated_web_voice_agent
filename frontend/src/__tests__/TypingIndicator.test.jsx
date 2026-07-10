import React from 'react';
import { render } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import TypingIndicator from '../components/TypingIndicator.jsx';

describe('TypingIndicator', () => {
  it('renders when visible', () => {
    const { container } = render(<TypingIndicator visible={true} />);
    expect(container.querySelector('.typing-indicator')).toBeInTheDocument();
    expect(container.querySelectorAll('span').length).toBe(3);
  });

  it('does not render when not visible', () => {
    const { container } = render(<TypingIndicator visible={false} />);
    expect(container.querySelector('.typing-indicator')).toBeNull();
  });

  it('does not render when visible is undefined', () => {
    const { container } = render(<TypingIndicator />);
    expect(container.querySelector('.typing-indicator')).toBeNull();
  });
});
