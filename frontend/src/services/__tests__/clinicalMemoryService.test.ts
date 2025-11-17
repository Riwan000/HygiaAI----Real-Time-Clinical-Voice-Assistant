import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ClinicalMemoryService } from '../clinicalMemoryService';
import { server } from '../../test/mocks/server';
import { http, HttpResponse } from 'msw';

describe('ClinicalMemoryService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('recalls similar cases', async () => {
    const result = await ClinicalMemoryService.recallSimilarCases({
      query_text: 'fever and cough',
      limit: 5,
    });

    expect(result.success).toBe(true);
    if (result.success && result.data) {
      expect(result.data.similar_cases).toBeDefined();
      expect(Array.isArray(result.data.similar_cases)).toBe(true);
    }
  });

  it('handles API errors gracefully', async () => {
    server.use(
      http.get('http://localhost:8000/api/v1/clinical-memory/recall', () => {
        return HttpResponse.json(
          { success: false, error: 'Server error' },
          { status: 500 }
        );
      })
    );

    const result = await ClinicalMemoryService.recallSimilarCases({
      query_text: 'test',
      limit: 5,
    });

    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error).toBeDefined();
    }
  });

  it('ingests new cases', async () => {
    const result = await ClinicalMemoryService.ingestCase({
      transcript: 'Patient presents with symptoms',
      metadata: {
        timestamp: new Date().toISOString(),
        age_group: 'adult',
        region: 'Rural Kerala',
      },
    });

    expect(result.success).toBe(true);
  });

  it('searches knowledge base', async () => {
    const result = await ClinicalMemoryService.searchKnowledgeBase({
      query: 'blood pressure',
      limit: 10,
    });

    expect(result.success).toBe(true);
    if (result.success && result.data) {
      expect(result.data.results).toBeDefined();
    }
  });
});

