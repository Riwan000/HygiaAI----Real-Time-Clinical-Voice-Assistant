import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '../../test/utils';
import userEvent from '@testing-library/user-event';
import { Pagination } from '../Pagination';

describe('Pagination', () => {
  const defaultProps = {
    currentPage: 1,
    totalPages: 10,
    onPageChange: vi.fn(),
  };

  it('renders pagination controls', () => {
    render(<Pagination {...defaultProps} pageSize={10} totalItems={100} />);
    // Component renders both mobile and desktop versions, so we check for multiple
    const prevButtons = screen.getAllByLabelText('Go to previous page');
    const nextButtons = screen.getAllByLabelText('Go to next page');
    expect(prevButtons.length).toBeGreaterThan(0);
    expect(nextButtons.length).toBeGreaterThan(0);
  });

  it('disables previous button on first page', () => {
    render(<Pagination {...defaultProps} currentPage={1} pageSize={10} totalItems={100} />);
    const prevButtons = screen.getAllByLabelText('Go to previous page');
    // Check the desktop version (first one)
    expect(prevButtons[0]).toHaveAttribute('aria-disabled', 'true');
  });

  it('disables next button on last page', () => {
    render(<Pagination {...defaultProps} currentPage={10} totalPages={10} pageSize={10} totalItems={100} />);
    const nextButtons = screen.getAllByLabelText('Go to next page');
    // Check the desktop version (first one)
    expect(nextButtons[0]).toHaveAttribute('aria-disabled', 'true');
  });

  it('calls onPageChange when next button is clicked', async () => {
    const user = userEvent.setup();
    const handlePageChange = vi.fn();
    
    render(<Pagination {...defaultProps} onPageChange={handlePageChange} pageSize={10} totalItems={100} />);
    
    // Use getAllByLabelText and click the desktop version (last one)
    const nextButtons = screen.getAllByLabelText('Go to next page');
    await user.click(nextButtons[nextButtons.length - 1]);
    
    expect(handlePageChange).toHaveBeenCalledWith(2);
  });

  it('calls onPageChange when previous button is clicked', async () => {
    const user = userEvent.setup();
    const handlePageChange = vi.fn();
    
    render(<Pagination {...defaultProps} currentPage={2} onPageChange={handlePageChange} pageSize={10} totalItems={100} />);
    
    // Use getAllByLabelText and click the desktop version (last one)
    const prevButtons = screen.getAllByLabelText('Go to previous page');
    await user.click(prevButtons[prevButtons.length - 1]);
    
    expect(handlePageChange).toHaveBeenCalledWith(1);
  });

  it('displays current page with aria-current', () => {
    render(<Pagination {...defaultProps} currentPage={5} pageSize={10} totalItems={100} />);
    const currentPageButton = screen.getByLabelText('Go to page 5');
    expect(currentPageButton).toHaveAttribute('aria-current', 'page');
  });

  it('shows page range information', () => {
    render(<Pagination {...defaultProps} currentPage={1} totalPages={10} pageSize={10} totalItems={100} />);
    expect(screen.getByText(/showing/i)).toBeInTheDocument();
  });
});

