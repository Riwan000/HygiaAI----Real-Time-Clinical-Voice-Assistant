/**
 * Federated Learning API Service
 * 
 * Service methods for federated learning operations:
 * - Starting aggregation rounds
 * - Submitting embeddings
 * - Getting aggregated results
 * - Synchronization
 */

import { apiRequest } from './api';
import type { ApiResponse } from './api';
import { API_ENDPOINTS } from '../utils/constants';

/**
 * Request/Response Types
 */

export type StartRoundRequest = {
  min_clients?: number;
  max_clients?: number;
};

export type StartRoundResponse = {
  round_id: string;
  status: string;
  min_clients: number;
};

export type SubmitEmbeddingRequest = {
  client_id: string;
  embedding: number[];
  weight?: number;
  statistics?: Record<string, any>;
};

export type SubmitEmbeddingResponse = {
  success: boolean;
  message: string;
};

export type AggregateRoundResponse = {
  round_id: string;
  success: boolean;
  aggregated_embedding?: number[];
  aggregated_statistics?: Record<string, any>;
  participating_clients: string[];
  error?: string;
};

export type RoundStatusResponse = {
  round_id: string;
  status: string;
  participating_clients: number;
  min_clients: number;
  created_at: string;
  completed_at?: string;
};

export type FederatedStatisticsResponse = {
  enabled: boolean;
  coordinator?: Record<string, any>;
  client?: Record<string, any>;
  sync?: Record<string, any>;
};

/**
 * Federated Learning Service Class
 */
export class FederatedService {
  /**
   * Start a new federated aggregation round
   */
  static async startRound(
    request: StartRoundRequest = {}
  ): Promise<ApiResponse<StartRoundResponse>> {
    return apiRequest<StartRoundResponse>({
      method: 'POST',
      url: API_ENDPOINTS.FEDERATED.ROUNDS_START,
      data: request,
    });
  }

  /**
   * Submit embeddings for aggregation
   */
  static async submitEmbeddings(
    request: SubmitEmbeddingRequest
  ): Promise<ApiResponse<SubmitEmbeddingResponse>> {
    return apiRequest<SubmitEmbeddingResponse>({
      method: 'POST',
      url: API_ENDPOINTS.FEDERATED.ROUNDS_SUBMIT,
      data: request,
    });
  }

  /**
   * Get aggregated model result
   */
  static async getAggregatedModel(
    roundId: string
  ): Promise<ApiResponse<AggregateRoundResponse>> {
    return apiRequest<AggregateRoundResponse>({
      method: 'GET',
      url: `${API_ENDPOINTS.FEDERATED.ROUNDS_AGGREGATE}/${roundId}`,
    });
  }

  /**
   * Get round status
   */
  static async getRoundStatus(
    roundId: string
  ): Promise<ApiResponse<RoundStatusResponse>> {
    return apiRequest<RoundStatusResponse>({
      method: 'GET',
      url: `${API_ENDPOINTS.FEDERATED.ROUNDS_STATUS}/${roundId}`,
    });
  }

  /**
   * Get federated learning statistics
   */
  static async getStatistics(): Promise<ApiResponse<FederatedStatisticsResponse>> {
    return apiRequest<FederatedStatisticsResponse>({
      method: 'GET',
      url: API_ENDPOINTS.FEDERATED.STATISTICS,
    });
  }

  /**
   * Sync local data with global coordinator
   */
  static async sync(): Promise<ApiResponse<{ success: boolean; message: string }>> {
    return apiRequest({
      method: 'POST',
      url: API_ENDPOINTS.FEDERATED.SYNC,
    });
  }

  /**
   * Participate in federated learning
   */
  static async participate(
    roundId: string
  ): Promise<ApiResponse<{ success: boolean; message: string }>> {
    return apiRequest({
      method: 'POST',
      url: API_ENDPOINTS.FEDERATED.PARTICIPATE,
      data: { round_id: roundId },
    });
  }
}

