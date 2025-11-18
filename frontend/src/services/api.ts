/**
 * API Service Layer
 * 
 * Provides typed API client with error handling, request/response interceptors,
 * and service methods for all backend endpoints.
 */

import axios from 'axios';
import type { AxiosInstance, AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios';
import { API_BASE_URL } from '../utils/constants';
import { queueRequest } from '../utils/offlineQueue';
import { getData, putData } from '../utils/indexedDB';

/**
 * Custom API Error class
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public response?: any,
    public originalError?: AxiosError
  ) {
    super(message);
    this.name = 'ApiError';
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

/**
 * API Response wrapper
 */
export type ApiResponse<T = any> = {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  statusCode?: number;
};

/**
 * Request configuration with retry options
 */
export type RequestConfig = AxiosRequestConfig & {
  retry?: {
    attempts: number;
    delay: number;
    onRetry?: (error: AxiosError, attempt: number) => void;
  };
  skipErrorHandling?: boolean;
};

/**
 * Create axios instance with default configuration
 */
const createAxiosInstance = (): AxiosInstance => {
  const instance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000, // 30 seconds
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor
  instance.interceptors.request.use(
    (config) => {
      // Add auth token if available
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor
  instance.interceptors.response.use(
    (response) => {
      return response;
    },
    async (error: AxiosError) => {
      // Handle network errors
      if (!error.response) {
        // More detailed error message
        let errorMessage = 'Network error: Unable to connect to server';
        if (error.code === 'ECONNREFUSED') {
          errorMessage = 'Connection refused. Please ensure the backend server is running.';
        } else if (error.code === 'ETIMEDOUT') {
          errorMessage = 'Request timed out. The server may be slow or unresponsive.';
        } else if (error.code === 'ECONNRESET' || error.message?.includes('ERR_CONNECTION_RESET')) {
          errorMessage = 'Connection reset by server. The request may have timed out or the server restarted. Please try again.';
        } else if (error.message) {
          errorMessage = `Network error: ${error.message}`;
        }
        throw new ApiError(
          errorMessage,
          0,
          null,
          error
        );
      }

      // Handle HTTP errors
      const statusCode = error.response.status;
      const data = error.response.data as any;

      let message = 'An error occurred';
      if (data?.detail) {
        message = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
      } else if (data?.message) {
        message = data.message;
      } else if (error.message) {
        message = error.message;
      }

      // Handle specific status codes
      switch (statusCode) {
        case 400:
          throw new ApiError(`Bad Request: ${message}`, statusCode, data, error);
        case 401:
          // Clear auth token on unauthorized
          localStorage.removeItem('auth_token');
          throw new ApiError('Unauthorized: Please login again', statusCode, data, error);
        case 403:
          throw new ApiError('Forbidden: You do not have permission', statusCode, data, error);
        case 404:
          throw new ApiError(`Not Found: ${message}`, statusCode, data, error);
        case 422:
          throw new ApiError(`Validation Error: ${message}`, statusCode, data, error);
        case 429:
          throw new ApiError('Too Many Requests: Please try again later', statusCode, data, error);
        case 500:
          throw new ApiError(`Server Error: ${message}`, statusCode, data, error);
        case 503:
          throw new ApiError('Service Unavailable: Server is temporarily unavailable', statusCode, data, error);
        default:
          throw new ApiError(message, statusCode, data, error);
      }
    }
  );

  return instance;
};

/**
 * Retry logic for failed requests
 */
const retryRequest = async (
  axiosInstance: AxiosInstance,
  config: RequestConfig,
  error: AxiosError,
  attempt: number
): Promise<AxiosResponse> => {
  const retryConfig = config.retry!;
  
  if (attempt >= retryConfig.attempts) {
    throw error;
  }

  // Only retry on network errors or 5xx errors
  if (!error.response || (error.response.status >= 500 && error.response.status < 600)) {
    if (retryConfig.onRetry) {
      retryConfig.onRetry(error, attempt);
    }

    // Wait before retrying
    await new Promise((resolve) => setTimeout(resolve, retryConfig.delay * attempt));

    // Ensure timeout is preserved in retry
    const retryRequestConfig: RequestConfig = {
      ...config,
      timeout: config.timeout ?? axiosInstance.defaults.timeout,
    };

    return axiosInstance.request(retryRequestConfig);
  }

  throw error;
};

/**
 * Check if we should queue the request (offline or local-only mode)
 */
const shouldQueueRequest = (): boolean => {
  const isLocalOnly = localStorage.getItem('hygiaai_local_only') === 'true';
  const isOnline = navigator.onLine;
  return isLocalOnly || !isOnline;
};

/**
 * Make API request with error handling, retry logic, and offline queue support
 */
export const apiRequest = async <T = any>(
  config: RequestConfig
): Promise<ApiResponse<T>> => {
  // Check if we should queue the request instead of making it
  if (shouldQueueRequest() && config.method && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(config.method.toUpperCase())) {
    // Queue the request for later sync
    try {
      const queueId = await queueRequest(config);
      return {
        success: true,
        data: { queued: true, queueId } as any,
        message: 'Request queued for offline sync',
      };
    } catch (queueError) {
      console.error('Failed to queue request:', queueError);
      // Fall through to try making the request anyway
    }
  }

  // For GET requests when offline, try to get from IndexedDB cache
  if (!navigator.onLine && config.method?.toUpperCase() === 'GET' && config.url) {
    try {
      // Try to get from cache
      const cacheKey = `cache_${config.url}`;
      const cached = await getData<any>('sync_metadata', cacheKey);
      if (cached && cached.data) {
        return {
          success: true,
          data: cached.data,
          statusCode: 200,
          message: 'Served from cache (offline)',
        };
      }
    } catch (cacheError) {
      // If cache lookup fails, continue to try network request
      console.warn('Cache lookup failed:', cacheError);
    }
  }

  const axiosInstance = createAxiosInstance();

  // Ensure timeout is applied to the request config
  // Axios will use config.timeout if provided, otherwise defaults.timeout
  const requestConfig: RequestConfig = {
    ...config,
    timeout: config.timeout ?? axiosInstance.defaults.timeout,
  };

  try {
    const response = await axiosInstance.request<T>(requestConfig);
    
    // Cache successful GET responses for offline use
    if (config.method?.toUpperCase() === 'GET' && config.url) {
      try {
        const cacheKey = `cache_${config.url}`;
        await putData('sync_metadata', {
          key: cacheKey,
          data: response.data,
          timestamp: Date.now(),
          url: config.url,
        });
      } catch (cacheError) {
        // Non-critical, just log
        console.warn('Failed to cache response:', cacheError);
      }
    }
    
    return {
      success: true,
      data: response.data,
      statusCode: response.status,
    };
  } catch (error: any) {
    // Handle retry logic
    if (requestConfig.retry && error && typeof error === 'object' && error.isAxiosError) {
      try {
        const retryResponse = await retryRequest(axiosInstance, requestConfig, error as AxiosError, 1);
        return {
          success: true,
          data: retryResponse.data,
          statusCode: retryResponse.status,
        };
      } catch (retryError: any) {
        // If retry also fails, handle as normal error
        if (retryError instanceof ApiError) {
          throw retryError;
        }
        if (retryError && typeof retryError === 'object' && retryError.isAxiosError) {
          // Will be caught by interceptor
          throw retryError;
        }
        throw new ApiError('Unknown error occurred', undefined, null, retryError);
      }
    }

    // Re-throw ApiError as-is
    if (error instanceof ApiError) {
      throw error;
    }

    // Convert AxiosError to ApiError (should be handled by interceptor, but just in case)
    if (error && typeof error === 'object' && error.isAxiosError) {
      const axiosError = error as AxiosError;
      throw new ApiError(
        axiosError.message || 'Request failed',
        axiosError.response?.status,
        axiosError.response?.data,
        axiosError
      );
    }

    // Unknown error - convert to ApiError
    const errorMessage = error?.message || error?.toString() || 'Unknown error occurred';
    throw new ApiError(errorMessage, undefined, null, error);
  }
};

/**
 * Health check endpoint
 */
export const healthCheck = async (): Promise<ApiResponse<{ status: string; service: string }>> => {
  return apiRequest({
    method: 'GET',
    url: '/health',
  });
};

