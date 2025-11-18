/**
 * Transcription Service
 * 
 * Handles real-time audio transcription using Deepgram WebSocket API
 */

import { DEEPGRAM_API_KEY, TRANSCRIPTION_CONFIG, API_BASE_URL } from '../utils/constants';
import { apiRequest } from './api';
import type { ApiResponse } from './api';

export interface TranscriptionWord {
  word: string;
  start: number;
  end: number;
  confidence: number;
  speaker?: number;
}

export interface TranscriptionResult {
  transcript: string;
  is_final: boolean;
  words: TranscriptionWord[];
  confidence: number;
  speaker?: number;
  timestamp: number;
}

export interface TranscriptionConfig {
  language?: string;
  model?: string;
  smart_format?: boolean;
  punctuate?: boolean;
  diarize?: boolean;
  interim_results?: boolean;
  endpointing?: number;
  vad_events?: boolean;
}

export type TranscriptionStatus = 
  | 'idle'
  | 'connecting'
  | 'connected'
  | 'transcribing'
  | 'paused'
  | 'error'
  | 'disconnected';

export type TranscriptionCallback = (result: TranscriptionResult) => void;
export type StatusCallback = (status: TranscriptionStatus, error?: string) => void;

export class TranscriptionService {
  private ws: WebSocket | null = null;
  private mediaStream: MediaStream | null = null;
  private audioContext: AudioContext | null = null;
  private processor: ScriptProcessorNode | null = null;
  private status: TranscriptionStatus = 'idle';
  private config: TranscriptionConfig;
  private onResultCallback: TranscriptionCallback | null = null;
  private onStatusCallback: StatusCallback | null = null;
  private onStreamCallback: ((stream: MediaStream) => void) | null = null;
  private sessionStartTime: number = 0;
  private finalTranscript: string = '';
  private interimTranscript: string = '';

  constructor(config?: TranscriptionConfig) {
    try {
      this.config = {
        language: TRANSCRIPTION_CONFIG.LANGUAGE,
        model: TRANSCRIPTION_CONFIG.MODEL,
        smart_format: TRANSCRIPTION_CONFIG.SMART_FORMAT,
        punctuate: true,
        diarize: TRANSCRIPTION_CONFIG.DIARIZE,
        interim_results: TRANSCRIPTION_CONFIG.INTERIM_RESULTS,
        endpointing: 300,
        vad_events: true,
        ...config,
      };
    } catch (error) {
      console.error('Error initializing TranscriptionService config:', error);
      // Use defaults if config fails
      this.config = {
        language: 'en-US',
        model: 'nova-2',
        smart_format: true,
        punctuate: true,
        diarize: true,
        interim_results: true,
        endpointing: 300,
        vad_events: true,
        ...config,
      };
    }
  }

  /**
   * Set callback for transcription results
   */
  onResult(callback: TranscriptionCallback): void {
    this.onResultCallback = callback;
  }

  /**
   * Set callback for status changes
   */
  onStatus(callback: StatusCallback): void {
    this.onStatusCallback = callback;
  }

  /**
   * Set callback for media stream (for waveform visualization)
   */
  onStream(callback: (stream: MediaStream) => void): void {
    this.onStreamCallback = callback;
  }

  /**
   * Get current media stream
   */
  getMediaStream(): MediaStream | null {
    return this.mediaStream;
  }

  /**
   * Get current status
   */
  getStatus(): TranscriptionStatus {
    return this.status;
  }

  /**
   * Get full transcript (final + interim)
   */
  getFullTranscript(): string {
    return this.finalTranscript + (this.interimTranscript ? ' ' + this.interimTranscript : '');
  }

  /**
   * Get final transcript only
   */
  getFinalTranscript(): string {
    return this.finalTranscript;
  }

  /**
   * Start transcription session
   */
  async start(): Promise<void> {
    if (this.status === 'transcribing' || this.status === 'connected') {
      throw new Error('Transcription already in progress');
    }

    try {
      this.updateStatus('connecting');

      // Request microphone access
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      // Initialize audio context
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate: 16000,
      });

      const source = this.audioContext.createMediaStreamSource(this.mediaStream);

      // Create script processor for audio chunks
      this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);
      this.processor.onaudioprocess = (e) => {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          const inputData = e.inputBuffer.getChannelData(0);
          const pcmData = this.convertFloat32ToInt16(inputData);
          this.ws.send(pcmData);
        }
      };

      source.connect(this.processor);
      this.processor.connect(this.audioContext.destination);

      // Notify stream callback
      if (this.onStreamCallback) {
        this.onStreamCallback(this.mediaStream);
      }

      // Connect to Deepgram WebSocket
      await this.connectWebSocket();

      this.sessionStartTime = Date.now();
      this.finalTranscript = '';
      this.interimTranscript = '';
      this.updateStatus('transcribing');
    } catch (error: any) {
      console.error('Error starting transcription:', error);
      this.updateStatus('error', error.message || 'Failed to start transcription');
      this.cleanup();
      throw error;
    }
  }

  /**
   * Connect to Deepgram WebSocket via backend proxy
   * This bypasses browser restrictions and firewall issues
   */
  private async connectWebSocket(): Promise<void> {
    return new Promise((resolve, reject) => {
      // Use backend WebSocket proxy instead of direct connection
      // This bypasses browser restrictions, CORS, and firewall issues
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const wsUrl = apiBaseUrl.replace('http://', 'ws://').replace('https://', 'wss://') + '/api/v1/transcription/ws';
      
      console.log('🔗 Connecting to backend WebSocket proxy...');
      console.log('📍 URL:', wsUrl);
      console.log('💡 This proxies to Deepgram, bypassing browser restrictions');

      // Add timeout to detect connection issues quickly
      const connectionTimeout = setTimeout(() => {
        if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
          console.error('⏱️  WebSocket connection timeout (10s)');
          this.ws.close();
          reject(new Error('WebSocket connection timeout. Is the backend server running?'));
        }
      }, 10000);

      this.ws = new WebSocket(wsUrl);
      
      // Clear timeout on successful connection
      this.ws.addEventListener('open', () => {
        clearTimeout(connectionTimeout);
      });

      this.ws.onopen = async () => {
        clearTimeout(connectionTimeout);
        console.log('✅ Connected to backend WebSocket proxy');
        
        // Send configuration to backend
        const config = {
          model: this.config.model || 'nova-2',
          language: this.config.language || 'en-US',
          smart_format: this.config.smart_format ?? true,
          punctuate: this.config.punctuate ?? true,
          diarize: this.config.diarize ?? true,
          interim_results: this.config.interim_results ?? true,
          endpointing: this.config.endpointing || 300,
          vad_events: this.config.vad_events ?? true,
        };
        
        this.ws?.send(JSON.stringify(config));
        this.updateStatus('connected');
        resolve();
      };

      this.ws.onmessage = (event) => {
        try {
          // Backend proxy sends JSON messages from Deepgram
          if (typeof event.data === 'string') {
            const data = JSON.parse(event.data);
            
            // Handle connection confirmation from backend
            if (data.type === 'connected') {
              console.log('✅ Backend connected to Deepgram:', data.message);
              return;
            }
            
            // Handle errors from backend
            if (data.type === 'error') {
              console.error('❌ Backend error:', data.message);
              this.updateStatus('error', data.message);
              return;
            }
            
            // Forward Deepgram transcription data
            this.handleDeepgramMessage(data);
          } else {
            // Binary data (shouldn't happen with our proxy, but handle it)
            console.warn('Received unexpected binary data from backend');
          }
        } catch (error) {
          console.error('Error parsing message from backend:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        console.error('WebSocket readyState:', this.ws?.readyState);
        console.error('WebSocket URL:', this.ws?.url);
        const errorMessage = 'WebSocket connection error. Check API key and network connection.';
        this.updateStatus('error', errorMessage);
        reject(new Error(errorMessage));
      };

      this.ws.onclose = (event) => {
        console.log('WebSocket closed:', {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean,
        });
        
        // Error code 1006 = abnormal closure (no close frame received)
        if (event.code === 1006) {
          console.error('❌ Connection closed abnormally (1006). Possible causes:');
          console.error('1. 🔑 Invalid API key or key lacks WebSocket permissions');
          console.error('2. 🚫 Network/firewall blocking wss://api.deepgram.com');
          console.error('3. 🌐 Corporate proxy blocking secure WebSocket');
          console.error('4. 🔒 Browser security policy blocking WebSocket');
          console.error('5. 💳 Deepgram account issue (no credits/permissions)');
          console.error('');
          console.error('💡 Troubleshooting:');
          console.error('- Try in Incognito mode (disables extensions)');
          console.error('- Check Windows Firewall settings');
          console.error('- Verify API key at https://console.deepgram.com/');
          console.error('- Test network: ping api.deepgram.com');
        }
        
        if (this.status === 'transcribing' || this.status === 'connected') {
          this.updateStatus('disconnected');
        }
      };
    });
  }

  /**
   * Handle messages from Deepgram
   */
  private handleDeepgramMessage(data: any): void {
    // Deepgram WebSocket responses can be in different formats
    // Handle both 'Results' type and direct channel results
    
    if (data.type === 'Results' || data.channel) {
      const channel = data.channel || data;
      const alternatives = channel?.alternatives || [];
      
      if (alternatives.length > 0) {
        const alternative = alternatives[0];
        const transcript = alternative.transcript || '';
        const isFinal = data.is_final !== undefined ? data.is_final : (channel.is_final || false);
        const words: TranscriptionWord[] = [];
        const confidence = alternative.confidence || 0;
        const speaker = alternative.speaker !== undefined ? alternative.speaker : (channel.speaker !== undefined ? channel.speaker : undefined);

        // Extract words with timestamps
        if (alternative.words && Array.isArray(alternative.words)) {
          for (const word of alternative.words) {
            words.push({
              word: word.word || '',
              start: word.start || 0,
              end: word.end || 0,
              confidence: word.confidence || 0,
              speaker: word.speaker !== undefined ? word.speaker : speaker,
            });
          }
        }

        // Only process if there's actual transcript text
        if (transcript.trim()) {
          // Update transcripts
          if (isFinal) {
            this.finalTranscript += (this.finalTranscript ? ' ' : '') + transcript;
            this.interimTranscript = '';
          } else {
            this.interimTranscript = transcript;
          }

          // Call callback
          if (this.onResultCallback) {
            this.onResultCallback({
              transcript,
              is_final: isFinal,
              words,
              confidence,
              speaker,
              timestamp: Date.now(),
            });
          }
        }
      }
    } else if (data.type === 'Metadata') {
      // Handle metadata (session info, etc.)
      console.log('Deepgram metadata:', data);
    } else if (data.type === 'Error' || data.error) {
      console.error('Deepgram error:', data);
      const errorMessage = data.message || data.error || 'Transcription error';
      this.updateStatus('error', errorMessage);
    } else {
      // Log unknown message types for debugging
      console.log('Unknown Deepgram message type:', data);
    }
  }

  /**
   * Convert Float32Array to Int16Array for PCM audio
   */
  private convertFloat32ToInt16(float32Array: Float32Array): Int16Array {
    const int16Array = new Int16Array(float32Array.length);
    for (let i = 0; i < float32Array.length; i++) {
      const s = Math.max(-1, Math.min(1, float32Array[i]));
      int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    return int16Array;
  }

  /**
   * Pause transcription
   */
  pause(): void {
    if (this.status === 'transcribing') {
      if (this.processor) {
        this.processor.disconnect();
      }
      this.updateStatus('paused');
    }
  }

  /**
   * Resume transcription
   */
  resume(): void {
    if (this.status === 'paused') {
      if (this.processor && this.audioContext) {
        const source = this.audioContext.createMediaStreamSource(this.mediaStream!);
        source.connect(this.processor);
        this.processor.connect(this.audioContext.destination);
      }
      this.updateStatus('transcribing');
    }
  }

  /**
   * Stop transcription
   */
  stop(): void {
    this.cleanup();
    this.updateStatus('idle');
  }

  /**
   * Cleanup resources
   */
  private cleanup(): void {
    if (this.processor) {
      this.processor.disconnect();
      this.processor = null;
    }

    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close();
      this.audioContext = null;
    }

    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop());
      this.mediaStream = null;
    }

    if (this.ws) {
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'CloseStream' }));
      }
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Update status and notify callback
   */
  private updateStatus(status: TranscriptionStatus, error?: string): void {
    this.status = status;
    if (this.onStatusCallback) {
      this.onStatusCallback(status, error);
    }
  }

  /**
   * Get recording duration in seconds
   */
  getRecordingDuration(): number {
    if (this.sessionStartTime === 0) return 0;
    return Math.floor((Date.now() - this.sessionStartTime) / 1000);
  }

  /**
   * Get word count
   */
  getWordCount(): number {
    const fullText = this.getFullTranscript();
    return fullText.trim().split(/\s+/).filter((word) => word.length > 0).length;
  }

  /**
   * Transcribe an uploaded audio file
   */
  static async transcribeFile(
    file: File,
    options?: {
      language?: string;
      model?: string;
      smart_format?: boolean;
      punctuate?: boolean;
      diarize?: boolean;
    }
  ): Promise<ApiResponse<{
    success: boolean;
    transcript: string;
    words: TranscriptionWord[];
    confidence: number;
    duration: number;
    language?: string;
    model?: string;
    error?: string;
    soap_note?: {
      subjective: string;
      objective: string;
      assessment: string;
      plan: string;
    };
  }>> {
    const formData = new FormData();
    formData.append('audio_file', file);
    if (options?.language) formData.append('language', options.language);
    if (options?.model) formData.append('model', options.model);
    if (options?.smart_format !== undefined) formData.append('smart_format', String(options.smart_format));
    if (options?.punctuate !== undefined) formData.append('punctuate', String(options.punctuate));
    if (options?.diarize !== undefined) formData.append('diarize', String(options.diarize));
    // Always generate SOAP note by default
    formData.append('generate_soap', 'true');

    // Calculate timeout based on file size
    // Audio transcription: base 2 minutes + 1 minute per 10MB
    // For a 50MB audio file: 2 min + 5 min = 7 minutes
    const fileSizeMB = file.size / (1024 * 1024);
    const timeoutMs = Math.max(120000, 120000 + (fileSizeMB / 10) * 60000); // 2 min base + 1 min per 10MB

    return apiRequest({
      method: 'POST',
      url: `${API_BASE_URL}/api/v1/transcription/file`,
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: timeoutMs,
      retry: {
        attempts: 1,
        delay: 2000,
      },
    });
  }
}

