import { http, HttpResponse } from 'msw';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const handlers = [
  // Clinical Memory API
  http.get(`${API_BASE_URL}/clinical-memory/recall`, () => {
    return HttpResponse.json({
      success: true,
      data: {
        similar_cases: [
          {
            case_id: 'case_001',
            patient_id: 'PAT001',
            similarity_score: 0.95,
            case_data: {
              transcript: 'Patient presents with fever and cough',
              soap_note: {
                subjective: 'Patient reports fever and persistent cough',
                objective: 'Temperature: 38.5°C, Lungs: clear',
                assessment: 'Acute bronchitis',
                plan: 'Prescribe antibiotics and rest',
              },
            },
            metadata: {
              timestamp: '2024-01-15T10:00:00Z',
              age_group: 'adult',
              region: 'Rural Kerala',
              diagnosis: 'Acute Bronchitis',
              outcome: 'recovered',
            },
          },
        ],
        total_found: 1,
      },
    });
  }),

  http.post(`${API_BASE_URL}/clinical-memory/ingest`, () => {
    return HttpResponse.json({
      success: true,
      data: {
        case_id: 'case_new_001',
        message: 'Case ingested successfully',
      },
    });
  }),

  // SOAP Notes
  http.get(`${API_BASE_URL}/clinical-memory/soap-notes`, () => {
    return HttpResponse.json({
      success: true,
      data: {
        notes: [
          {
            id: 'soap_001',
            case_id: 'case_001',
            patient_id: 'PAT001',
            soap_note: {
              subjective: 'Patient reports fever',
              objective: 'Temperature: 38.5°C',
              assessment: 'Acute bronchitis',
              plan: 'Prescribe antibiotics',
            },
            generated_at: '2024-01-15T10:00:00Z',
          },
        ],
      },
    });
  }),

  // Knowledge Base
  http.get(`${API_BASE_URL}/knowledge/search`, () => {
    return HttpResponse.json({
      success: true,
      data: {
        results: [
          {
            id: 'kb_001',
            content: 'Normal blood pressure for adults is 120/80 mmHg',
            domain: 'vital_signs',
            source: 'WHO Guidelines',
            year: 2023,
          },
        ],
        total: 1,
      },
    });
  }),

  // Timeline
  http.get(`${API_BASE_URL}/clinical-memory/timeline/:patientId`, () => {
    return HttpResponse.json({
      success: true,
      data: {
        events: [
          {
            id: 'event_001',
            type: 'consultation',
            timestamp: '2024-01-15T10:00:00Z',
            description: 'Initial consultation',
            metadata: {},
          },
        ],
      },
    });
  }),

  // Transcription WebSocket (mock)
  http.get(`${API_BASE_URL}/transcription/ws`, () => {
    return HttpResponse.json({
      success: true,
      message: 'WebSocket endpoint',
    });
  }),
];

