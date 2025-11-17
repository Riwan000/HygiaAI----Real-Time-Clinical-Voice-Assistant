/**
 * Application constants
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
export const DEEPGRAM_API_KEY = import.meta.env.VITE_DEEPGRAM_API_KEY || '';
export const ENABLE_OFFLINE_MODE = import.meta.env.VITE_ENABLE_OFFLINE_MODE === 'true';
export const ENABLE_FEDERATED_LEARNING = import.meta.env.VITE_ENABLE_FEDERATED_LEARNING === 'true';

// API Endpoints
export const API_ENDPOINTS = {
  CLINICAL_MEMORY: {
    INGEST: '/api/v1/clinical_memory/ingest',
    SOAP: '/api/v1/clinical_memory/soap',
    SOAP_EXPORT_PDF: '/api/v1/clinical_memory/soap/export/pdf',
    RECALL_CASE: '/api/v1/clinical_memory/recall_case',
    SUMMARY: '/api/v1/clinical_memory/summary',
    LAB_REPORT: '/api/v1/clinical_memory/lab_report',
    TEMPORAL_CLUSTERING: '/api/v1/clinical_memory/temporal_clustering',
    REGIONAL_ANALYTICS: '/api/v1/clinical_memory/regional_analytics',
    TRUST_SCORE: '/api/v1/clinical_memory/trust_score',
    KNOWLEDGE_SEARCH: '/api/v1/clinical_memory/knowledge/search',
    KNOWLEDGE_DOMAINS: '/api/v1/clinical_memory/knowledge/domains',
    KNOWLEDGE_SOURCES: '/api/v1/clinical_memory/knowledge/sources',
  },
  FEDERATED: {
    ROUNDS_START: '/api/v1/federated/rounds/start',
    ROUNDS_SUBMIT: '/api/v1/federated/rounds',
    ROUNDS_AGGREGATE: '/api/v1/federated/rounds',
    ROUNDS_STATUS: '/api/v1/federated/rounds',
    STATISTICS: '/api/v1/federated/statistics',
    SYNC: '/api/v1/federated/sync',
    PARTICIPATE: '/api/v1/federated/participate',
  },
  VISUALIZATION: {
    CASE_MAP: '/api/visualization/case_map',
    TEMPORAL_TRENDS: '/api/visualization/temporal_trends',
    SIMILARITY_MAP: '/api/visualization/similarity_map',
    DASHBOARD_SUMMARY: '/api/visualization/dashboard_summary',
  },
  HEALTH: '/health',
} as const;

// File Upload Limits
export const FILE_LIMITS = {
  AUDIO: {
    MAX_SIZE: 50 * 1024 * 1024, // 50MB
    ALLOWED_TYPES: ['audio/wav', 'audio/mp3', 'audio/mpeg', 'audio/webm'],
  },
  IMAGE: {
    MAX_SIZE: 10 * 1024 * 1024, // 10MB
    ALLOWED_TYPES: ['image/jpeg', 'image/png', 'image/jpg'],
  },
  DOCUMENT: {
    MAX_SIZE: 20 * 1024 * 1024, // 20MB
    ALLOWED_TYPES: ['application/pdf', 'text/plain'],
  },
} as const;

// Pagination
export const DEFAULT_PAGE_SIZE = 10;
export const MAX_PAGE_SIZE = 100;

// Transcription
export const TRANSCRIPTION_CONFIG = {
  LANGUAGE: 'en-US',
  MODEL: 'nova-2',
  INTERIM_RESULTS: true,
  DIARIZE: true,
  SMART_FORMAT: true,
} as const;

