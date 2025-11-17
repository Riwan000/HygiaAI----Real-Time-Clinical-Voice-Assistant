/**
 * Transcription Testing Utilities
 * 
 * Helper functions for testing transcription functionality
 */

import { TranscriptionService } from '../services/transcriptionService';
import { testDeepgramConnectivity, testWebSocketSupport } from './testNetwork';

/**
 * Test transcription service initialization
 */
export async function testTranscriptionSetup(): Promise<{
  success: boolean;
  errors: string[];
  warnings: string[];
}> {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Check for Deepgram API key
  const apiKey = import.meta.env.VITE_DEEPGRAM_API_KEY;
  console.log('🔍 Debug - API Key check:', {
    exists: !!apiKey,
    length: apiKey?.length || 0,
    startsWith: apiKey?.substring(0, 10) || 'N/A',
    isPlaceholder: apiKey === 'your_deepgram_api_key_here',
    allEnvKeys: Object.keys(import.meta.env).filter(k => k.includes('DEEPGRAM')),
  });
  if (!apiKey || apiKey === 'your_deepgram_api_key_here' || apiKey.trim() === '') {
    errors.push('Deepgram API key not configured in .env file');
  }

  // Check for microphone support
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    errors.push('MediaDevices API not supported in this browser');
  }

  // Check for WebSocket support
  const wsSupport = testWebSocketSupport();
  if (!wsSupport.supported) {
    errors.push(`WebSocket not supported: ${wsSupport.error || 'Unknown error'}`);
  }

  // Test Deepgram API connectivity
  try {
    const connectivity = await testDeepgramConnectivity();
    if (!connectivity.success) {
      warnings.push(`Deepgram API connectivity issue: ${connectivity.error}`);
    }
  } catch (error: any) {
    warnings.push(`Could not test Deepgram connectivity: ${error.message}`);
  }

  // Check for AudioContext support
  if (!window.AudioContext && !(window as any).webkitAudioContext) {
    errors.push('Web Audio API not supported in this browser');
  }

  // Check HTTPS (required for microphone in production)
  if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost') {
    warnings.push('Microphone access requires HTTPS in production');
  }

  // Test service initialization
  try {
    const service = new TranscriptionService();
    if (service.getStatus() !== 'idle') {
      errors.push('Service should start in idle state');
    }
  } catch (error: any) {
    errors.push(`Failed to initialize service: ${error.message}`);
  }

  return {
    success: errors.length === 0,
    errors,
    warnings,
  };
}

/**
 * Test microphone access
 */
export async function testMicrophoneAccess(): Promise<{
  success: boolean;
  error?: string;
  stream?: MediaStream;
}> {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    return {
      success: true,
      stream,
    };
  } catch (error: any) {
    return {
      success: false,
      error: error.message || 'Failed to access microphone',
    };
  }
}

/**
 * Log test results to console
 */
export function logTestResults(results: {
  success: boolean;
  errors: string[];
  warnings: string[];
}): void {
  console.group('🧪 Transcription Setup Test');
  
  if (results.success) {
    console.log('✅ All checks passed!');
  } else {
    console.error('❌ Setup issues found:');
    results.errors.forEach((error) => console.error(`  - ${error}`));
  }

  if (results.warnings.length > 0) {
    console.warn('⚠️  Warnings:');
    results.warnings.forEach((warning) => console.warn(`  - ${warning}`));
  }

  console.groupEnd();
}

