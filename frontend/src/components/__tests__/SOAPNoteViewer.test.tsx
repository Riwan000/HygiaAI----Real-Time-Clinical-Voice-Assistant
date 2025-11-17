import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '../../test/utils';
import userEvent from '@testing-library/user-event';
import { SOAPNoteViewer } from '../SOAPNoteViewer';
import type { SOAPNote, CaseMetadata } from '../../types';

const mockSOAPNote: SOAPNote = {
  subjective: 'Patient reports fever and persistent cough for 3 days',
  objective: 'Temperature: 38.5°C, Lungs: clear to auscultation',
  assessment: 'Acute bronchitis',
  plan: 'Prescribe antibiotics and rest. Follow-up in 1 week.',
};

const mockMetadata: CaseMetadata = {
  timestamp: '2024-01-15T10:00:00Z',
  age_group: 'adult',
  region: 'Rural Kerala',
  diagnosis: 'Acute Bronchitis',
  outcome: 'recovered',
};

describe('SOAPNoteViewer', () => {
  it('renders all SOAP sections', () => {
    render(
      <SOAPNoteViewer
        soapNote={mockSOAPNote}
        patientInfo={{ id: 'PAT001', age: 'adult' }}
        caseMetadata={mockMetadata}
      />
    );
    
    expect(screen.getByText(/subjective/i)).toBeInTheDocument();
    expect(screen.getByText(/objective/i)).toBeInTheDocument();
    expect(screen.getByText(/assessment/i)).toBeInTheDocument();
    expect(screen.getByText(/plan/i)).toBeInTheDocument();
  });

  it('displays SOAP note content', () => {
    render(
      <SOAPNoteViewer
        soapNote={mockSOAPNote}
        patientInfo={{ id: 'PAT001', age: 'adult' }}
        caseMetadata={mockMetadata}
      />
    );
    
    expect(screen.getByText(mockSOAPNote.subjective)).toBeInTheDocument();
    expect(screen.getByText(mockSOAPNote.objective)).toBeInTheDocument();
    expect(screen.getByText(mockSOAPNote.assessment)).toBeInTheDocument();
    expect(screen.getByText(mockSOAPNote.plan)).toBeInTheDocument();
  });

  it('allows editing when editable prop is true', async () => {
    const user = userEvent.setup();
    const handleSave = vi.fn();
    
    render(
      <SOAPNoteViewer
        soapNote={mockSOAPNote}
        patientInfo={{ id: 'PAT001', age: 'adult' }}
        caseMetadata={mockMetadata}
        editable={true}
        onSave={handleSave}
      />
    );
    
    const editButton = screen.getByRole('button', { name: /edit soap note/i });
    await user.click(editButton);
    
    // Should show editable fields - check for textarea instead of input
    const subjectiveTextarea = screen.getByDisplayValue(mockSOAPNote.subjective);
    expect(subjectiveTextarea).toBeInTheDocument();
  });

  it('calls onSave when save button is clicked', async () => {
    const user = userEvent.setup();
    const handleSave = vi.fn();
    
    render(
      <SOAPNoteViewer
        soapNote={mockSOAPNote}
        patientInfo={{ id: 'PAT001', age: 'adult' }}
        caseMetadata={mockMetadata}
        editable={true}
        onSave={handleSave}
      />
    );
    
    const editButton = screen.getByRole('button', { name: /edit soap note/i });
    await user.click(editButton);
    
    const saveButton = screen.getByRole('button', { name: /save changes/i });
    await user.click(saveButton);
    
    expect(handleSave).toHaveBeenCalled();
  });

  it('shows export buttons', () => {
    render(
      <SOAPNoteViewer
        soapNote={mockSOAPNote}
        patientInfo={{ id: 'PAT001', age: 'adult' }}
        caseMetadata={mockMetadata}
      />
    );
    
    // Only PDF export is currently implemented
    expect(screen.getByRole('button', { name: /export.*pdf/i })).toBeInTheDocument();
    // DOCX export shows an alert, not a button, so we don't test for it
  });
});

