import { describe, it, expect } from 'vitest';
import { render } from '../../test/utils';
import { axe, toHaveNoViolations } from 'jest-axe';
import { Loading } from '../Loading';
import { Breadcrumbs } from '../Breadcrumbs';
import { CaseCard } from '../CaseCard';
import { SearchBox } from '../SearchBox';
import type { Case, CaseMetadata } from '../../types';

expect.extend(toHaveNoViolations);

const mockCase: Case = {
  case_id: 'case_001',
  patient_id: 'PAT001',
  similarity_score: 0.95,
  case_data: {
    transcript: 'Test transcript',
    soap_note: {
      subjective: 'Test',
      objective: 'Test',
      assessment: 'Test',
      plan: 'Test',
    },
  },
  metadata: {
    timestamp: '2024-01-15T10:00:00Z',
    age_group: 'adult',
    region: 'Rural Kerala',
  } as CaseMetadata,
};

describe('Accessibility Tests', () => {
  it('Loading component has no accessibility violations', async () => {
    const { container } = render(<Loading />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('Breadcrumbs component has no accessibility violations', async () => {
    const { container } = render(
      <Breadcrumbs items={[{ name: 'Home' }, { name: 'Dashboard' }]} />
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('CaseCard component has no accessibility violations', async () => {
    const { container } = render(<CaseCard case={mockCase} />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('SearchBox component has no accessibility violations', async () => {
    const { container } = render(
      <SearchBox
        value=""
        onChange={() => {}}
        onSubmit={() => {}}
      />
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});

