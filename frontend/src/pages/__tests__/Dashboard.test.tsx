import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '../../test/utils';
import { Dashboard } from '../Dashboard';
import { ClinicalMemoryService } from '../../services/clinicalMemoryService';

// Mock the service
vi.mock('../../services/clinicalMemoryService', () => ({
  ClinicalMemoryService: {
    recallSimilarCases: vi.fn(() =>
      Promise.resolve({
        success: true,
        data: {
          similar_cases: [],
          total_found: 0,
        },
      })
    ),
  },
}));

describe('Dashboard', () => {
  it('renders dashboard page', () => {
    render(<Dashboard />);
    expect(screen.getByRole('heading', { name: /dashboard/i })).toBeInTheDocument();
  });

  it('displays search box', () => {
    render(<Dashboard />);
    expect(screen.getByRole('searchbox')).toBeInTheDocument();
  });

  it('loads cases on mount', async () => {
    render(<Dashboard />);
    
    await waitFor(() => {
      expect(ClinicalMemoryService.recallSimilarCases).toHaveBeenCalled();
    });
  });

  it('displays empty state when no cases found', async () => {
    render(<Dashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/no cases found/i)).toBeInTheDocument();
    });
  });
});

