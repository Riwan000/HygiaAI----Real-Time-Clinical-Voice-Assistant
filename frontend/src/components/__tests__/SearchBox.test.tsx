import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '../../test/utils';
import userEvent from '@testing-library/user-event';
import { SearchBox } from '../SearchBox';

describe('SearchBox', () => {
  it('renders search input', () => {
    render(
      <SearchBox
        value=""
        onChange={vi.fn()}
        onSubmit={vi.fn()}
      />
    );
    expect(screen.getByRole('searchbox')).toBeInTheDocument();
  });

  it('calls onChange when typing', async () => {
    const user = userEvent.setup();
    const handleChange = vi.fn();
    const handleSubmit = vi.fn();
    
    render(
      <SearchBox
        value=""
        onChange={handleChange}
        onSubmit={handleSubmit}
      />
    );
    
    const input = screen.getByRole('searchbox');
    await user.type(input, 'fever');
    
    expect(handleChange).toHaveBeenCalled();
  });

  it('calls onSubmit when Enter is pressed', async () => {
    const user = userEvent.setup();
    const handleChange = vi.fn();
    const handleSubmit = vi.fn();
    
    render(
      <SearchBox
        value="fever"
        onChange={handleChange}
        onSubmit={handleSubmit}
      />
    );
    
    const input = screen.getByRole('searchbox');
    await user.type(input, '{Enter}');
    
    expect(handleSubmit).toHaveBeenCalledWith('fever');
  });

  it('clears search when clear button is clicked', async () => {
    const user = userEvent.setup();
    const handleChange = vi.fn();
    const handleSubmit = vi.fn();
    
    render(
      <SearchBox
        value="fever"
        onChange={handleChange}
        onSubmit={handleSubmit}
      />
    );
    
    const clearButton = screen.getByLabelText('Clear search');
    await user.click(clearButton);
    
    expect(handleChange).toHaveBeenCalledWith('');
  });

  it('has proper accessibility attributes', () => {
    render(
      <SearchBox
        value=""
        onChange={vi.fn()}
        onSubmit={vi.fn()}
      />
    );
    const input = screen.getByRole('searchbox');
    expect(input).toHaveAttribute('aria-label');
  });
});

