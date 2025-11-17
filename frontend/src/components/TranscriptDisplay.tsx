/**
 * Transcript Display Component
 * 
 * Displays real-time transcription with word-level timestamps,
 * speaker identification, and confidence scores
 */

import { useEffect, useRef, useState } from 'react';
import type { TranscriptionResult, TranscriptionWord } from '../services/transcriptionService';
import { clsx } from '../utils/clsx';
import { UserIcon } from '@heroicons/react/24/outline';

interface TranscriptDisplayProps {
  results: TranscriptionResult[];
  autoScroll?: boolean;
  showTimestamps?: boolean;
  showConfidence?: boolean;
  showSpeakers?: boolean;
  className?: string;
}

export function TranscriptDisplay({
  results,
  autoScroll = true,
  showTimestamps = false,
  showConfidence = false,
  showSpeakers = true,
  className,
}: TranscriptDisplayProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editedText, setEditedText] = useState('');

  // Auto-scroll to bottom when new results arrive
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [results, autoScroll]);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.9) return 'text-green-600 dark:text-green-400';
    if (confidence >= 0.7) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getSpeakerColor = (speaker?: number): string => {
    if (speaker === undefined) return 'bg-gray-200 dark:bg-gray-700';
    const colors = [
      'bg-blue-200 dark:bg-blue-800',
      'bg-purple-200 dark:bg-purple-800',
      'bg-pink-200 dark:bg-pink-800',
      'bg-green-200 dark:bg-green-800',
    ];
    return colors[speaker % colors.length];
  };

  const handleEdit = (index: number, text: string) => {
    setEditingIndex(index);
    setEditedText(text);
  };

  const handleSaveEdit = (index: number) => {
    if (editingIndex === index && editedText.trim()) {
      // In a real implementation, this would update the result
      // For now, we'll just close the edit
      setEditingIndex(null);
      setEditedText('');
    }
  };

  if (results.length === 0) {
    return (
      <div
        className={clsx(
          'flex items-center justify-center h-64 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-700',
          className
        )}
      >
        <p className="text-gray-500 dark:text-gray-400">
          Transcription will appear here...
        </p>
      </div>
    );
  }

  return (
    <div
      ref={scrollRef}
      role="log"
      aria-live="polite"
      aria-atomic="false"
      aria-label="Transcription display"
      className={clsx(
        'overflow-y-auto max-h-96 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-[#1E293B] p-4 space-y-3',
        className
      )}
    >
      {results.map((result, index) => (
        <div
          key={index}
          className={clsx(
            'p-3 rounded-lg transition-all',
            result.is_final
              ? 'bg-white dark:bg-[#1E293B] border border-gray-200 dark:border-gray-700'
              : 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800'
          )}
        >
          {/* Speaker and Timestamp Header */}
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              {showSpeakers && result.speaker !== undefined && (
                <div
                  className={clsx(
                    'flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-medium',
                    getSpeakerColor(result.speaker),
                    'text-gray-800 dark:text-gray-200'
                  )}
                >
                  <UserIcon className="h-3 w-3" aria-hidden="true" />
                  <span>Speaker {result.speaker + 1}</span>
                </div>
              )}
              {showTimestamps && (
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {formatTime(result.words[0]?.start || 0)}
                </span>
              )}
            </div>
            {showConfidence && (
              <span
                className={clsx(
                  'text-xs font-medium',
                  getConfidenceColor(result.confidence)
                )}
              >
                {Math.round(result.confidence * 100)}%
              </span>
            )}
          </div>

          {/* Transcript Text */}
          {editingIndex === index ? (
            <div className="flex items-center space-x-2">
              <input
                type="text"
                value={editedText}
                onChange={(e) => setEditedText(e.target.value)}
                className="flex-1 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-[#0F172A] text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2"
                autoFocus
                onBlur={() => handleSaveEdit(index)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleSaveEdit(index);
                  } else if (e.key === 'Escape') {
                    setEditingIndex(null);
                    setEditedText('');
                  }
                }}
                aria-label="Edit transcript"
              />
            </div>
          ) : (
            <div className="flex items-start space-x-2">
              <p
                className={clsx(
                  'flex-1 text-sm',
                  result.is_final
                    ? 'text-gray-900 dark:text-white'
                    : 'text-gray-600 dark:text-gray-400 italic'
                )}
                onDoubleClick={() => handleEdit(index, result.transcript)}
              >
                {result.transcript}
              </p>
              {!result.is_final && (
                <span className="text-xs text-blue-500 animate-pulse">●</span>
              )}
            </div>
          )}

          {/* Word-level details (expandable) */}
          {result.words.length > 0 && (
            <details className="mt-2">
              <summary className="text-xs text-gray-500 dark:text-gray-400 cursor-pointer hover:text-gray-700 dark:hover:text-gray-300">
                Show word details ({result.words.length} words)
              </summary>
              <div className="mt-2 flex flex-wrap gap-1">
                {result.words.map((word: TranscriptionWord, wordIndex: number) => (
                  <span
                    key={wordIndex}
                    className={clsx(
                      'inline-block px-1.5 py-0.5 rounded text-xs',
                      getConfidenceColor(word.confidence),
                      'bg-opacity-10'
                    )}
                    title={`Confidence: ${Math.round(word.confidence * 100)}% | ${formatTime(word.start)} - ${formatTime(word.end)}`}
                  >
                    {word.word}
                  </span>
                ))}
              </div>
            </details>
          )}
        </div>
      ))}
    </div>
  );
}

