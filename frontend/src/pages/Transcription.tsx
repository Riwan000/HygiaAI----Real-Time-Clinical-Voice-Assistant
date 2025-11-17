/**
 * Live Transcription Page
 * 
 * Real-time audio transcription interface with Deepgram integration
 */

import { useState, useEffect, useRef } from 'react';
import { Breadcrumbs } from '../components/Breadcrumbs';
import { AudioWaveform } from '../components/AudioWaveform';
import { TranscriptDisplay } from '../components/TranscriptDisplay';
import {
  TranscriptionService,
  type TranscriptionResult,
  type TranscriptionStatus,
} from '../services/transcriptionService';
import { ClinicalMemoryService } from '../services/clinicalMemoryService';
import { testTranscriptionSetup, logTestResults } from '../utils/testTranscription';
import {
  MicrophoneIcon,
  StopIcon,
  PauseIcon,
  PlayIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import { clsx } from '../utils/clsx';

export function Transcription() {
  const [transcriptionService] = useState(() => {
    try {
      return new TranscriptionService();
    } catch (error: any) {
      console.error('Failed to initialize TranscriptionService:', error);
      // Return a minimal service that won't break
      return null as any;
    }
  });
  const [status, setStatus] = useState<TranscriptionStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<TranscriptionResult[]>([]);
  const [mediaStream, setMediaStream] = useState<MediaStream | null>(null);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [wordCount, setWordCount] = useState(0);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const durationIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const [setupTested, setSetupTested] = useState(false);

  // Early return if service failed to initialize
  if (!transcriptionService) {
    return (
      <div>
        <Breadcrumbs items={[{ name: 'Live Transcription' }]} />
        <h1 className="text-3xl font-bold text-[#1E3A8A] dark:text-white mb-6 font-heading">
          Live Transcription
        </h1>
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-800 dark:text-red-200">
            Failed to initialize transcription service. Please check the browser console for details.
          </p>
        </div>
      </div>
    );
  }

  // Test setup on component mount (non-blocking, optional)
  useEffect(() => {
    const runSetupTest = async () => {
      try {
        if (testTranscriptionSetup && logTestResults) {
          const results = await testTranscriptionSetup();
          logTestResults(results);
          setSetupTested(true);
          
          if (!results.success && results.errors.length > 0) {
            // Only show critical errors, not warnings
            const criticalErrors = results.errors.filter(e => 
              !e.includes('API key not configured') // This is expected if not set yet
            );
            if (criticalErrors.length > 0) {
              setError(`Setup issues: ${criticalErrors.join(', ')}`);
            }
          }
        }
      } catch (error: any) {
        console.error('Setup test error:', error);
        // Don't block rendering if test fails
      }
    };
    runSetupTest();
  }, []);

  useEffect(() => {
    // Set up callbacks
    transcriptionService.onResult((result: TranscriptionResult) => {
      setResults((prev) => {
        // If it's a final result, replace the last interim result
        if (result.is_final && prev.length > 0 && !prev[prev.length - 1].is_final) {
          return [...prev.slice(0, -1), result];
        }
        // Otherwise, add new result
        return [...prev, result];
      });
      setWordCount(transcriptionService.getWordCount());
    });

    transcriptionService.onStatus((newStatus: TranscriptionStatus, errorMessage?: string) => {
      setStatus(newStatus);
      setError(errorMessage || null);

      // Start/stop duration timer
      if (newStatus === 'transcribing') {
        durationIntervalRef.current = setInterval(() => {
          setRecordingDuration(transcriptionService.getRecordingDuration());
        }, 1000);
      } else {
        if (durationIntervalRef.current) {
          clearInterval(durationIntervalRef.current);
          durationIntervalRef.current = null;
        }
      }
    });

    transcriptionService.onStream((stream: MediaStream) => {
      setMediaStream(stream);
    });

    return () => {
      transcriptionService.stop();
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
      }
    };
  }, [transcriptionService]);

  const handleStart = async () => {
    try {
      setError(null);
      setSaveSuccess(false);
      setResults([]);
      await transcriptionService.start();
      // Stream will be set via onStream callback
    } catch (err: any) {
      console.error('Error starting transcription:', err);
      setError(err.message || 'Failed to start transcription');
      if (err.name === 'NotAllowedError') {
        setError('Microphone permission denied. Please allow microphone access.');
      } else if (err.name === 'NotFoundError') {
        setError('No microphone found. Please connect a microphone.');
      }
    }
  };

  const handleStop = () => {
    transcriptionService.stop();
    if (mediaStream) {
      mediaStream.getTracks().forEach((track) => track.stop());
      setMediaStream(null);
    }
    setRecordingDuration(0);
  };

  const handlePause = () => {
    transcriptionService.pause();
  };

  const handleResume = () => {
    transcriptionService.resume();
  };

  const handleSave = async () => {
    const fullTranscript = transcriptionService.getFullTranscript();
    if (!fullTranscript.trim()) {
      setError('No transcript to save');
      return;
    }

    setIsSaving(true);
    setError(null);
    setSaveSuccess(false);

    try {
      // Save to case history via ingestion endpoint
      const response = await ClinicalMemoryService.ingestCase({
        patient_id: `patient_${Date.now()}`, // In real app, this would come from context
        transcript_text: fullTranscript,
      });

      if (response.success) {
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 3000);
      } else {
        setError(response.error || 'Failed to save transcript');
      }
    } catch (err: any) {
      console.error('Error saving transcript:', err);
      setError(err.message || 'Failed to save transcript');
    } finally {
      setIsSaving(false);
    }
  };

  const handleGenerateSOAP = async () => {
    const fullTranscript = transcriptionService.getFinalTranscript();
    if (!fullTranscript.trim()) {
      setError('No final transcript available for SOAP generation');
      return;
    }

    setIsSaving(true);
    setError(null);
    setSaveSuccess(false);

    try {
      const response = await ClinicalMemoryService.generateSOAP({
        transcript: fullTranscript,
        patient_id: `patient_${Date.now()}`, // In real app, this would come from context
      });

      if (response.success && response.data) {
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 3000);
        // Optionally navigate to SOAP notes page or show the generated SOAP
        console.log('SOAP note generated:', response.data);
      } else {
        setError(response.error || 'Failed to generate SOAP note');
      }
    } catch (err: any) {
      console.error('Error generating SOAP note:', err);
      setError(err.message || 'Failed to generate SOAP note');
    } finally {
      setIsSaving(false);
    }
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusColor = (): string => {
    switch (status) {
      case 'transcribing':
        return 'text-green-600 dark:text-green-400';
      case 'connected':
        return 'text-blue-600 dark:text-blue-400';
      case 'paused':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'error':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  const getStatusText = (): string => {
    switch (status) {
      case 'idle':
        return 'Ready';
      case 'connecting':
        return 'Connecting...';
      case 'connected':
        return 'Connected';
      case 'transcribing':
        return 'Transcribing...';
      case 'paused':
        return 'Paused';
      case 'error':
        return 'Error';
      case 'disconnected':
        return 'Disconnected';
      default:
        return 'Unknown';
    }
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+R or Cmd+R: Start/Stop recording
      if ((e.ctrlKey || e.metaKey) && e.key === 'r' && !e.shiftKey) {
        e.preventDefault();
        if (status === 'idle' || status === 'error' || status === 'disconnected') {
          handleStart();
        } else if (status === 'transcribing') {
          handleStop();
        }
      }
      // Ctrl+P or Cmd+P: Pause/Resume
      if ((e.ctrlKey || e.metaKey) && e.key === 'p' && !e.shiftKey) {
        e.preventDefault();
        if (status === 'transcribing') {
          handlePause();
        } else if (status === 'paused') {
          handleResume();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [status]);

  return (
    <div>
      <Breadcrumbs items={[{ name: 'Live Transcription' }]} />
      <h1 className="text-3xl font-bold text-[#1E3A8A] dark:text-white mb-6 font-heading">
        Live Transcription
      </h1>

      {/* ARIA Live Region for Status Updates */}
      <div
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
        id="transcription-status-announcement"
      >
        {status === 'transcribing' && 'Recording in progress'}
        {status === 'paused' && 'Recording paused'}
        {status === 'error' && `Error: ${error || 'Unknown error'}`}
        {status === 'connected' && 'Connected to transcription service'}
        {status === 'disconnected' && 'Disconnected from transcription service'}
      </div>

      {/* ARIA Live Region for Transcript Updates */}
      <div
        aria-live="polite"
        aria-atomic="false"
        className="sr-only"
        id="transcript-updates-announcement"
      >
        {results.length > 0 && `Transcript updated: ${results[results.length - 1]?.transcript || ''}`}
      </div>

      <div className="space-y-6">
        {/* Status and Controls */}
        <div className="bg-white dark:bg-[#1E293B] rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div 
                className={clsx('flex items-center space-x-2', getStatusColor())}
                role="status"
                aria-live="polite"
                aria-atomic="true"
              >
                {status === 'transcribing' && (
                  <div 
                    className="h-3 w-3 rounded-full bg-green-500 animate-pulse"
                    aria-label="Recording active"
                  />
                )}
                {status === 'error' && (
                  <XCircleIcon className="h-5 w-5" aria-hidden="true" />
                )}
                {status === 'paused' && (
                  <PauseIcon className="h-5 w-5" aria-hidden="true" />
                )}
                {status === 'idle' && (
                  <MicrophoneIcon className="h-5 w-5" aria-hidden="true" />
                )}
                <span className="font-medium">{getStatusText()}</span>
              </div>
            </div>

            <div className="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
              {recordingDuration > 0 && (
                <div className="flex items-center space-x-1">
                  <ClockIcon className="h-4 w-4" />
                  <span>{formatDuration(recordingDuration)}</span>
                </div>
              )}
              {wordCount > 0 && (
                <div>
                  <span className="font-medium">{wordCount}</span> words
                </div>
              )}
            </div>
          </div>

          {/* Audio Waveform */}
          <div className="mb-4">
            <AudioWaveform
              mediaStream={mediaStream}
              isActive={status === 'transcribing' || status === 'connected'}
            />
          </div>

          {/* Error Message */}
          {error && (
            <div 
              className="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800"
              role="alert"
              aria-live="assertive"
              aria-atomic="true"
            >
              <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
            </div>
          )}

          {/* Success Message */}
          {saveSuccess && (
            <div 
              className="mb-4 p-3 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800"
              role="status"
              aria-live="polite"
              aria-atomic="true"
            >
              <div className="flex items-center space-x-2">
                <CheckCircleIcon 
                  className="h-5 w-5 text-green-600 dark:text-green-400"
                  aria-hidden="true"
                />
                <p className="text-sm text-green-800 dark:text-green-200">
                  Transcript saved successfully!
                </p>
              </div>
            </div>
          )}

          {/* Control Buttons */}
          <div 
            className="flex items-center justify-center space-x-3"
            role="group"
            aria-label="Transcription controls"
          >
            {status === 'idle' && (
              <button
                onClick={handleStart}
                className="flex items-center space-x-2 px-6 py-3 bg-[#2563EB] text-white rounded-lg hover:bg-[#1E40AF] transition-colors font-medium focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2"
                aria-label="Start recording. Press Ctrl+R or Cmd+R for keyboard shortcut."
              >
                <MicrophoneIcon className="h-5 w-5" aria-hidden="true" />
                <span>Start Recording</span>
              </button>
            )}

            {status === 'transcribing' && (
              <>
                <button
                  onClick={handlePause}
                  className="flex items-center space-x-2 px-6 py-3 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition-colors font-medium focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:ring-offset-2"
                  aria-label="Pause recording. Press Ctrl+P or Cmd+P for keyboard shortcut."
                >
                  <PauseIcon className="h-5 w-5" aria-hidden="true" />
                  <span>Pause</span>
                </button>
                <button
                  onClick={handleStop}
                  className="flex items-center space-x-2 px-6 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors font-medium focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
                  aria-label="Stop recording. Press Ctrl+R or Cmd+R for keyboard shortcut."
                >
                  <StopIcon className="h-5 w-5" aria-hidden="true" />
                  <span>Stop</span>
                </button>
              </>
            )}

            {status === 'paused' && (
              <>
                <button
                  onClick={handleResume}
                  className="flex items-center space-x-2 px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors font-medium focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
                  aria-label="Resume recording. Press Ctrl+P or Cmd+P for keyboard shortcut."
                >
                  <PlayIcon className="h-5 w-5" aria-hidden="true" />
                  <span>Resume</span>
                </button>
                <button
                  onClick={handleStop}
                  className="flex items-center space-x-2 px-6 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors font-medium focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
                  aria-label="Stop recording"
                >
                  <StopIcon className="h-5 w-5" aria-hidden="true" />
                  <span>Stop</span>
                </button>
              </>
            )}

            {(status === 'disconnected' || status === 'error') && (
              <button
                onClick={handleStart}
                className="flex items-center space-x-2 px-6 py-3 bg-[#2563EB] text-white rounded-lg hover:bg-[#1E40AF] transition-colors font-medium"
              >
                <MicrophoneIcon className="h-5 w-5" />
                <span>Retry</span>
              </button>
            )}
          </div>
        </div>

        {/* Transcript Display */}
        <div className="bg-white dark:bg-[#1E293B] rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-[#1E3A8A] dark:text-white">
              Transcript
            </h2>
            {results.length > 0 && (
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleSave}
                  disabled={isSaving || status === 'transcribing'}
                  className={clsx(
                    'flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2',
                    isSaving || status === 'transcribing'
                      ? 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
                      : 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 hover:bg-blue-200 dark:hover:bg-blue-900/50'
                  )}
                  aria-label={isSaving ? 'Saving transcript...' : 'Save transcript to case history'}
                  aria-disabled={isSaving || status === 'transcribing'}
                >
                  <DocumentTextIcon className="h-4 w-4" aria-hidden="true" />
                  <span>{isSaving ? 'Saving...' : 'Save to Cases'}</span>
                </button>
                <button
                  onClick={handleGenerateSOAP}
                  disabled={isSaving || transcriptionService.getFinalTranscript().trim() === ''}
                  className={clsx(
                    'flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-[#8B5CF6] focus:ring-offset-2',
                    isSaving || transcriptionService.getFinalTranscript().trim() === ''
                      ? 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
                      : 'bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-200 hover:bg-purple-200 dark:hover:bg-purple-900/50'
                  )}
                  aria-label={isSaving ? 'Generating SOAP note...' : 'Generate SOAP note from transcript'}
                  aria-disabled={isSaving || transcriptionService.getFinalTranscript().trim() === ''}
                >
                  <DocumentTextIcon className="h-4 w-4" aria-hidden="true" />
                  <span>{isSaving ? 'Generating...' : 'Generate SOAP Note'}</span>
                </button>
              </div>
            )}
          </div>

          <TranscriptDisplay
            results={results}
            autoScroll={true}
            showTimestamps={true}
            showConfidence={true}
            showSpeakers={true}
          />
        </div>
      </div>
    </div>
  );
}
