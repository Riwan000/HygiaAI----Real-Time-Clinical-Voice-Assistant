import { describe, it, expect, beforeEach, vi } from 'vitest';
import { server } from '../../test/mocks/server';
import { http, HttpResponse } from 'msw';
import { api } from '../api';

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('makes GET requests', async () => {
    server.use(
      http.get('http://localhost:8000/api/v1/test', () => {
        return HttpResponse.json({ success: true, data: { message: 'test' } });
      })
    );

    const response = await api.get('/test');
    expect(response.data.success).toBe(true);
  });

  it('makes POST requests', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/test', () => {
        return HttpResponse.json({ success: true, data: { id: 1 } });
      })
    );

    const response = await api.post('/test', { name: 'test' });
    expect(response.data.success).toBe(true);
  });

  it('handles errors gracefully', async () => {
    server.use(
      http.get('http://localhost:8000/api/v1/error', () => {
        return HttpResponse.json(
          { success: false, error: 'Server error' },
          { status: 500 }
        );
      })
    );

    try {
      await api.get('/error');
    } catch (error: any) {
      expect(error).toBeDefined();
    }
  });

  it('includes authentication headers when token is present', async () => {
    localStorage.setItem('auth_token', 'test-token');
    
    server.use(
      http.get('http://localhost:8000/api/v1/test', ({ request }) => {
        const authHeader = request.headers.get('Authorization');
        return HttpResponse.json({ 
          success: true, 
          data: { hasAuth: !!authHeader } 
        });
      })
    );

    const response = await api.get('/test');
    expect(response.data.data.hasAuth).toBe(true);
    
    localStorage.removeItem('auth_token');
  });
});

