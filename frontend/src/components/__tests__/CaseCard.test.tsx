import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '../../test/utils';
import userEvent from '@testing-library/user-event';
import { CaseCard } from '../CaseCard';
import type { Case, CaseMetadata } from '../../types';

const mockCase: Case = {
  case_id: 'case_001',
  patient_id: 'PAT001',
  similarity_score: 0.95,
  case_data: {
    transcript: 'Patient presents with fever',
    soap_note: {
      subjective: 'Patient reports fever',
      objective: 'Temperature: 38.5°C',
      assessment: 'Acute bronchitis',
      plan: 'Prescribe antibiotics',
    },
  },
  metadata: {
    timestamp: '2024-01-15T10:00:00Z',
    age_group: 'adult',
    region: 'Rural Kerala',
    diagnosis: 'Acute Bronchitis',
    outcome: 'recovered',
  } as CaseMetadata,
};

describe('CaseCard', () => {
  it('renders case information', () => {
    render(<CaseCard case={mockCase} />);
    
    expect(screen.getByText(/case_001/i)).toBeInTheDocument();
    expect(screen.getByText(/PAT001/i)).toBeInTheDocument();
    expect(screen.getByText(/Acute Bronchitis/i)).toBeInTheDocument();
  });

  it('displays similarity score', () => {
    render(<CaseCard case={mockCase} />);
    expect(screen.getByText(/95%/i)).toBeInTheDocument();
  });

  it('calls onClick when clicked', async () => {
    const user = userEvent.setup();
    const handleClick = vi.fn();
    
    render(<CaseCard case={mockCase} onClick={handleClick} />);
    
    const card = screen.getByRole('button');
    await user.click(card);
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('has proper ARIA label', () => {
    render(<CaseCard case={mockCase} />);
    const card = screen.getByRole('button');
    expect(card).toHaveAttribute('aria-label');
    expect(card.getAttribute('aria-label')).toContain('case_001');
  });

  it('supports keyboard navigation', async () => {
    const user = userEvent.setup();
    const handleClick = vi.fn();
    
    render(<CaseCard case={mockCase} onClick={handleClick} />);
    
    const card = screen.getByRole('button');
    card.focus();
    await user.keyboard('{Enter}');
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});

