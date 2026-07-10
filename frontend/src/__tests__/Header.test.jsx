import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import Header from '../components/Header.jsx';

describe('Header', () => {
  const defaultProps = {
    status: { state: 'connected', label: 'Connected' },
    isDark: false,
    onToggleTheme: vi.fn(),
    onToggleSidebar: vi.fn(),
  };

  it('renders the brand name', () => {
    render(<Header {...defaultProps} />);
    expect(screen.getByText('AI Voice Assistant')).toBeInTheDocument();
  });

  it('shows connection status', () => {
    render(<Header {...defaultProps} />);
    expect(screen.getByText('Connected')).toBeInTheDocument();
  });

  it('shows processing status', () => {
    render(<Header {...defaultProps} status={{ state: 'processing', label: 'Processing...' }} />);
    expect(screen.getByText('Processing...')).toBeInTheDocument();
  });

  it('calls onToggleTheme when theme button clicked', () => {
    const onToggleTheme = vi.fn();
    render(<Header {...defaultProps} onToggleTheme={onToggleTheme} />);
    fireEvent.click(screen.getByTitle('Toggle theme'));
    expect(onToggleTheme).toHaveBeenCalledTimes(1);
  });

  it('shows sun emoji in dark mode', () => {
    render(<Header {...defaultProps} isDark={true} />);
    expect(screen.getByText('☀️')).toBeInTheDocument();
  });

  it('shows moon emoji in light mode', () => {
    render(<Header {...defaultProps} isDark={false} />);
    expect(screen.getByText('🌙')).toBeInTheDocument();
  });

  it('calls onToggleSidebar when menu button clicked', () => {
    const onToggleSidebar = vi.fn();
    render(<Header {...defaultProps} onToggleSidebar={onToggleSidebar} />);
    fireEvent.click(screen.getByLabelText('Menu'));
    expect(onToggleSidebar).toHaveBeenCalledTimes(1);
  });
});
