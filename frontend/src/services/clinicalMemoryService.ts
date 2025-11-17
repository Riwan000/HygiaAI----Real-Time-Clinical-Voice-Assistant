/**
 * Clinical Memory API Service
 * 
 * Service methods for clinical memory operations:
 * - Multimodal ingestion
 * - SOAP note generation
 * - Similar case recall
 * - Context-aware summarization
 * - Lab report normalization
 * - Knowledge intelligence & trend analysis
 */

import { apiRequest } from './api';
import type { ApiResponse } from './api';
import { API_ENDPOINTS, API_BASE_URL } from '../utils/constants';
import type {
  Case,
  CaseMetadata,
  SOAPNote,
  SimilarCase,
  KnowledgeEntry,
} from '../types';

/**
 * Request/Response Types matching backend models
 */

// Ingestion
export type IngestRequest = {
  patient_id: string;
  age_group?: string;
  region?: string;
  comorbidities?: string[];
  diagnosis?: string;
  outcome?: string;
  audio_file?: File;
  image_file?: File;
  text_file?: File;
  transcript_text?: string;
};

export type IngestResponse = {
  status: string;
  case_id: string;
  point_ids: string[];
  modalities_processed: Array<{
    modality_type: string;
    status: string;
    point_id?: string;
  }>;
  soap_generated: boolean;
  message: string;
};

// SOAP Note
export type SOAPRequest = {
  transcript: string;
  patient_id?: string;
  age_group?: string;
  region?: string;
  comorbidities?: string[];
};

export type SOAPResponse = {
  case_id: string;
  soap_note: {
    subjective: string;
    objective: string;
    assessment: string;
    plan: string;
  };
  metadata: Record<string, any>;
  point_ids: string[];
  generated_at: string;
};

// Case Recall
export type RecallRequest = {
  query_text?: string;
  query_image_path?: string;
  limit?: number;
  score_threshold?: number;
  age_group?: string;
  region?: string;
  diagnosis?: string;
  time_range_days?: number;
};

export type RecallResponse = {
  query_type: string;
  similar_cases: Array<{
    case_id: string;
    patient_id: string;
    case_data: Case;
    similarity_score: number;
    metadata: CaseMetadata;
  }>;
  total_found: number;
  latency_ms: number;
};

// Summary
export type SummaryRequest = {
  current_case: Record<string, any>;
  similar_cases?: Array<Record<string, any>>;
  include_differential?: boolean;
  include_treatment_plan?: boolean;
};

export type SummaryResponse = {
  summary: string;
  differential_diagnosis: Array<{
    diagnosis: string;
    confidence: number;
    reasoning: string;
  }>;
  treatment_recommendations: Array<{
    recommendation: string;
    confidence: number;
    evidence: string[];
  }>;
  confidence_scores: {
    overall: number;
    differential: number;
    treatment: number;
  };
  similar_cases_used: number;
};

// Lab Report
export type LabReportRequest = {
  lab_data: Record<string, any>;
  test_type: string;
  patient_id?: string;
  timestamp?: string;
};

export type LabReportResponse = {
  normalized_data: Record<string, any>;
  point_id: string;
  embedding_generated: boolean;
  stored: boolean;
};

// Temporal Clustering
export type TemporalClusteringRequest = {
  time_window_days: number;
  region?: string;
  min_cluster_size?: number;
};

export type TemporalClusteringResponse = {
  clusters: Array<{
    cluster_id: string;
    time_window: string;
    case_count: number;
    characteristics: {
      symptoms: string[];
      diagnoses: string[];
      locations: string[];
    };
    pattern_insights: string[];
  }>;
  total_clusters: number;
  analysis_period: string;
};

// Regional Analytics
export type RegionalAnalyticsRequest = {
  region: string;
  period_days: number;
  compare_with_previous?: boolean;
};

export type RegionalAnalyticsResponse = {
  region: string;
  period: string;
  disease_trends: Array<{
    disease: string;
    current_count: number;
    previous_count?: number;
    trend: 'rising' | 'stable' | 'declining';
    change_percentage?: number;
  }>;
  common_complaints: Array<{
    complaint: string;
    frequency: number;
    percentage: number;
  }>;
  treatment_success_rates: Array<{
    treatment: string;
    success_rate: number;
    sample_size: number;
  }>;
  outbreak_alerts: Array<{
    disease: string;
    severity: 'low' | 'medium' | 'high';
    cases: number;
    recommendation: string;
  }>;
};

// Trust Score
export type TrustScoreRequest = {
  case_id: string;
  similar_cases: Array<{
    case_id: string;
    similarity_score: number;
  }>;
};

export type TrustScoreResponse = {
  case_id: string;
  overall_score: number;
  confidence_level: 'low' | 'medium' | 'high';
  breakdown: {
    similarity_score: number;
    source_reliability: number;
    recency_score: number;
    agreement_score: number;
  };
  explanation: string;
};

/**
 * Clinical Memory Service Class
 */
export class ClinicalMemoryService {
  /**
   * Ingest multimodal case data
   */
  static async ingestCase(request: IngestRequest): Promise<ApiResponse<IngestResponse>> {
    const formData = new FormData();
    
    formData.append('patient_id', request.patient_id);
    if (request.age_group) formData.append('age_group', request.age_group);
    if (request.region) formData.append('region', request.region);
    if (request.comorbidities) {
      formData.append('comorbidities', JSON.stringify(request.comorbidities));
    }
    if (request.diagnosis) formData.append('diagnosis', request.diagnosis);
    if (request.outcome) formData.append('outcome', request.outcome);
    if (request.transcript_text) formData.append('transcript_text', request.transcript_text);
    if (request.audio_file) formData.append('audio_file', request.audio_file);
    if (request.image_file) formData.append('image_file', request.image_file);
    if (request.text_file) formData.append('text_file', request.text_file);

    return apiRequest<IngestResponse>({
      method: 'POST',
      url: API_ENDPOINTS.CLINICAL_MEMORY.INGEST,
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      retry: {
        attempts: 2,
        delay: 1000,
      },
    });
  }

  /**
   * Generate SOAP note from transcript
   */
  static async generateSOAP(request: SOAPRequest): Promise<ApiResponse<SOAPResponse>> {
    return apiRequest<SOAPResponse>({
      method: 'POST',
      url: API_ENDPOINTS.CLINICAL_MEMORY.SOAP,
      data: request,
      retry: {
        attempts: 2,
        delay: 1000,
      },
    });
  }

  /**
   * Recall similar cases
   */
  static async recallSimilarCases(request: RecallRequest): Promise<ApiResponse<RecallResponse>> {
    return apiRequest<RecallResponse>({
      method: 'POST',
      url: API_ENDPOINTS.CLINICAL_MEMORY.RECALL_CASE,
      data: request,
    });
  }

  /**
   * Generate context-aware summary
   */
  static async generateSummary(request: SummaryRequest): Promise<ApiResponse<SummaryResponse>> {
    return apiRequest<SummaryResponse>({
      method: 'POST',
      url: API_ENDPOINTS.CLINICAL_MEMORY.SUMMARY,
      data: request,
      retry: {
        attempts: 2,
        delay: 1000,
      },
    });
  }

  /**
   * Normalize and store lab report
   */
  static async processLabReport(request: LabReportRequest): Promise<ApiResponse<LabReportResponse>> {
    return apiRequest<LabReportResponse>({
      method: 'POST',
      url: API_ENDPOINTS.CLINICAL_MEMORY.LAB_REPORT,
      data: request,
    });
  }

  /**
   * Perform temporal clustering analysis
   */
  static async performTemporalClustering(
    request: TemporalClusteringRequest
  ): Promise<ApiResponse<TemporalClusteringResponse>> {
    return apiRequest<TemporalClusteringResponse>({
      method: 'POST',
      url: API_ENDPOINTS.CLINICAL_MEMORY.TEMPORAL_CLUSTERING,
      data: request,
      retry: {
        attempts: 1,
        delay: 2000,
      },
    });
  }

  /**
   * Get regional health analytics
   */
  static async getRegionalAnalytics(
    request: RegionalAnalyticsRequest
  ): Promise<ApiResponse<RegionalAnalyticsResponse>> {
    return apiRequest<RegionalAnalyticsResponse>({
      method: 'POST',
      url: API_ENDPOINTS.CLINICAL_MEMORY.REGIONAL_ANALYTICS,
      data: request,
      retry: {
        attempts: 1,
        delay: 2000,
      },
    });
  }

  /**
   * Calculate trust score for a case
   */
  static async calculateTrustScore(
    request: TrustScoreRequest
  ): Promise<ApiResponse<TrustScoreResponse>> {
    return apiRequest<TrustScoreResponse>({
      method: 'POST',
      url: API_ENDPOINTS.CLINICAL_MEMORY.TRUST_SCORE,
      data: request,
    });
  }

  /**
   * Search knowledge base
   */
  static async searchKnowledgeBase(request: {
    query: string;
    domain?: string;
    source?: string;
    year_range?: { min?: number; max?: number };
    limit?: number;
    score_threshold?: number;
  }): Promise<ApiResponse<{
    query: string;
    entries: KnowledgeEntry[];
    total_found: number;
    domains: string[];
    sources: string[];
    latency_ms: number;
  }>> {
    return apiRequest({
      method: 'POST',
      url: API_ENDPOINTS.CLINICAL_MEMORY.KNOWLEDGE_SEARCH,
      data: request,
    });
  }

  /**
   * Get available knowledge base domains
   */
  static async getKnowledgeDomains(): Promise<ApiResponse<string[]>> {
    return apiRequest({
      method: 'GET',
      url: API_ENDPOINTS.CLINICAL_MEMORY.KNOWLEDGE_DOMAINS,
    });
  }

  /**
   * Get available knowledge base sources
   */
  static async getKnowledgeSources(): Promise<ApiResponse<string[]>> {
    return apiRequest({
      method: 'GET',
      url: API_ENDPOINTS.CLINICAL_MEMORY.KNOWLEDGE_SOURCES,
    });
  }

  /**
   * Get patient timeline (all cases for a patient)
   */
  static async getPatientTimeline(
    patientId: string,
    timeRangeDays?: number
  ): Promise<ApiResponse<RecallResponse>> {
    // Use recall_case endpoint with patient_id filter
    // Note: This is a workaround - ideally we'd have a dedicated timeline endpoint
    return apiRequest<RecallResponse>({
      method: 'POST',
      url: API_ENDPOINTS.CLINICAL_MEMORY.RECALL_CASE,
      data: {
        query_text: '', // Empty query to get all cases
        limit: 100, // Get up to 100 cases
        time_range_days: timeRangeDays,
        // We'll filter by patient_id in the backend or client-side
      },
    });
  }

  /**
   * Export SOAP note to PDF
   */
  static async exportSOAPToPDF(
    soapNote: {
      subjective: string;
      objective: string;
      assessment: string;
      plan: string;
      metadata?: Record<string, any>;
    },
    patientInfo?: {
      name?: string;
      patient_id?: string;
      dob?: string;
      age?: string;
      gender?: string;
    },
    clinicianInfo?: {
      name?: string;
      title?: string;
      license?: string;
    }
  ): Promise<void> {
    const axios = (await import('axios')).default;
    const formData = new FormData();
    
    formData.append('soap_note', JSON.stringify(soapNote));
    if (patientInfo) {
      formData.append('patient_info', JSON.stringify(patientInfo));
    }
    if (clinicianInfo) {
      formData.append('clinician_info', JSON.stringify(clinicianInfo));
    }

    try {
      const response = await axios.post(
        `${API_BASE_URL}${API_ENDPOINTS.CLINICAL_MEMORY.SOAP_EXPORT_PDF}`,
        formData,
        {
          responseType: 'blob',
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      // Check if response is actually a PDF (not an error JSON)
      const contentType = response.headers['content-type'] || response.data.type || '';
      if (contentType.includes('application/json') || contentType.includes('text/')) {
        // Response is JSON error, not PDF
        const text = await response.data.text();
        let errorMessage = 'Failed to export PDF';
        try {
          const errorData = JSON.parse(text);
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch {
          errorMessage = text || errorMessage;
        }
        throw new Error(errorMessage);
      }

      // Create download link
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `soap_note_${new Date().toISOString().split('T')[0]}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error: any) {
      console.error('Error exporting SOAP note to PDF:', error);
      
      // Check for network errors (server not running)
      if (error?.code === 'ERR_NETWORK' || error?.message?.includes('Network Error') || error?.message?.includes('ECONNREFUSED')) {
        throw new Error(
          'Cannot connect to backend server. Please ensure:\n' +
          '1. Backend server is running (python run_server.py)\n' +
          '2. Server is accessible at http://localhost:8000\n' +
          '3. Check browser console for CORS errors'
        );
      }
      
      // Try to extract error message from blob response
      if (error?.response?.data && error.response.data instanceof Blob) {
        try {
          const text = await error.response.data.text();
          const errorData = JSON.parse(text);
          throw new Error(errorData.detail || errorData.message || 'Failed to export PDF');
        } catch {
          // If parsing fails, use default message
        }
      }
      
      // Check for HTTP errors
      if (error?.response?.status) {
        const status = error.response.status;
        if (status === 404) {
          throw new Error('PDF export endpoint not found. Please check backend API routes.');
        } else if (status === 500) {
          const detail = error?.response?.data?.detail || 'Internal server error';
          throw new Error(`Server error: ${detail}\n\nPlease check:\n1. reportlab is installed (pip install reportlab)\n2. Backend logs for details`);
        }
      }
      
      const errorMessage = error?.response?.data?.detail || 
                          error?.response?.data?.message || 
                          error?.message || 
                          'Failed to export PDF. Please check the console for details.';
      throw new Error(errorMessage);
    }
  }
}

