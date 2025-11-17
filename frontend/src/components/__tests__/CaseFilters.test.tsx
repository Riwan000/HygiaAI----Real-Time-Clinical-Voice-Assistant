import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '../../test/utils';
import userEvent from '@testing-library/user-event';
import { CaseFilters } from '../CaseFilters';
import type { FilterOptions } from '../CaseFilters';

describe('CaseFilters', () => {
  const defaultProps = {
    filters: {
      ageGroup: '',
      region: '',
      diagnosis: '',
      timeRange: 'all',
      similarityScore: [0, 1],
    } as FilterOptions,
    onFiltersChange: vi.fn(),
  };

  it('renders all filter controls', () => {
    render(<CaseFilters {...defaultProps} />);
    
    expect(screen.getByLabelText(/age group/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/region/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/diagnosis/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/time range/i)).toBeInTheDocument();
  });

  it('calls onFiltersChange when age group changes', async () => {
    const user = userEvent.setup();
    const handleChange = vi.fn();
    
    render(<CaseFilters {...defaultProps} onFiltersChange={handleChange} />);
    
    const ageGroupSelect = screen.getByLabelText(/age group/i);
    await user.selectOptions(ageGroupSelect, 'adult');
    
    expect(handleChange).toHaveBeenCalled();
  });

  it('calls onFiltersChange when similarity score changes', async () => {
    const user = userEvent.setup();
    const handleChange = vi.fn();
    
    render(<CaseFilters {...defaultProps} onFiltersChange={handleChange} />);
    
    const similarityInput = screen.getByLabelText(/similarity score/i);
    await user.clear(similarityInput);
    await user.type(similarityInput, '0.8');
    
    expect(handleChange).toHaveBeenCalled();
  });

  it('has proper accessibility attributes', () => {
    render(<CaseFilters {...defaultProps} />);
    
    const ageGroupSelect = screen.getByLabelText(/age group/i);
    expect(ageGroupSelect).toHaveAttribute('id');
    
    const similarityInput = screen.getByLabelText(/similarity score/i);
    expect(similarityInput).toHaveAttribute('aria-valuemin');
    expect(similarityInput).toHaveAttribute('aria-valuemax');
  });
});

