import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import Sidebar from '../components/Sidebar.jsx';

describe('Sidebar', () => {
  const defaultProps = {
    open: false,
    pages: [],
    scrapeStatus: '',
    onScrape: vi.fn(),
    onClearPages: vi.fn(),
    onCloseMobile: vi.fn(),
  };

  it('renders the knowledge base title', () => {
    render(<Sidebar {...defaultProps} />);
    expect(screen.getByText('🔗 Knowledge Base')).toBeInTheDocument();
  });

  it('shows empty state when no pages', () => {
    render(<Sidebar {...defaultProps} />);
    expect(screen.getByText(/No pages yet/)).toBeInTheDocument();
  });

  it('shows scrape status', () => {
    render(<Sidebar {...defaultProps} scrapeStatus="✅ Scraped: Test" />);
    expect(screen.getByText('✅ Scraped: Test')).toBeInTheDocument();
  });

  it('renders scraped pages', () => {
    const pages = [
      { url: 'https://example.com', title: 'Example Page' },
    ];
    render(<Sidebar {...defaultProps} pages={pages} />);
    expect(screen.getByText('Example Page')).toBeInTheDocument();
  });

  it('shows page count', () => {
    const pages = [
      { url: 'https://a.com', title: 'Page A' },
      { url: 'https://b.com', title: 'Page B' },
    ];
    render(<Sidebar {...defaultProps} pages={pages} />);
    expect(screen.getByText('2 pages')).toBeInTheDocument();
  });

  it('shows clear all button when pages exist', () => {
    const pages = [{ url: 'https://a.com', title: 'Page A' }];
    render(<Sidebar {...defaultProps} pages={pages} />);
    expect(screen.getByText('🗑️ Clear all')).toBeInTheDocument();
  });

  it('calls onScrape when scrape button clicked', () => {
    const onScrape = vi.fn();
    render(<Sidebar {...defaultProps} onScrape={onScrape} />);
    const input = screen.getByPlaceholderText('https://example.com');
    fireEvent.change(input, { target: { value: 'https://test.com' } });
    fireEvent.click(screen.getByText('Scrape'));
    expect(onScrape).toHaveBeenCalledWith('https://test.com');
  });

  it('calls onClearPages when clear button clicked', () => {
    const onClearPages = vi.fn();
    const pages = [{ url: 'https://a.com', title: 'Page A' }];
    render(<Sidebar {...defaultProps} pages={pages} onClearPages={onClearPages} />);
    fireEvent.click(screen.getByText('🗑️ Clear all'));
    expect(onClearPages).toHaveBeenCalledTimes(1);
  });
});
